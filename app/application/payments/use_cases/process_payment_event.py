import json
import hashlib

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.uow import UnitOfWork
from app.infrastructure.database.models import PaymentEvent

from app.application.invoice.use_cases.mark_paid import MarkInvoicePaidUseCase
from app.application.invoice.use_cases.deliver_invoice import DeliverInvoiceUseCase
from app.application.delivery.service import DeliveryService
from app.infrastructure.database.models import ReferralAccrual
from app.config.settings import settings


def build_idempotency_key(provider, external_payment_id, event_type):
    return hashlib.sha256(
        f"{provider}:{external_payment_id}:{event_type}".encode()
    ).hexdigest()


async def process_payment_event(normalized, provider_name: str):

    idempotency_key = build_idempotency_key(
        provider_name,
        normalized.external_payment_id,
        "payment",
    )

    async with UnitOfWork() as uow:

        # 1. LOAD INVOICE
        invoice = await uow.invoices.get_by_external_payment_id(
            normalized.external_payment_id
        )

        # 2. IDEMPOTENCY EVENT
        # webhook_idempotency.md: "EVERY webhook event must be stored.
        # Even invalid ones." So the event is created and flushed
        # BEFORE branching on whether the invoice was found.
        event = PaymentEvent(
            invoice_id=invoice.id if invoice else None,
            provider=provider_name,
            event_type="payment",
            idempotency_key=idempotency_key,
            processed=False,
            payload=json.dumps({
                "external_payment_id": normalized.external_payment_id,
                "invoice_id": invoice.id if invoice else None,
                "tx_hash": normalized.tx_hash,
            }),
        )

        try:
            await uow.payment_events.create_event(event)
        except IntegrityError:
            await uow.session.rollback()
            return {"status": "duplicate"}

        # 3. INVOICE NOT FOUND -> event already persisted, stop here
        if not invoice:
            event.failed = True
            event.last_error = "invoice_not_found"
            await uow.session.commit()
            return {"status": "invoice_not_found"}

        # 3.5 STATUS GATE
        # invoice_state_machine.md: only a genuine "paid" event may
        # trigger the PAID transition + delivery. Non-paid events
        # (processing, expired, failed, or any unmapped provider
        # status) must be persisted (already done above) but MUST NOT
        # mutate invoice state or trigger delivery.
        if normalized.status != "paid":
            event.last_error = f"non_paid_status:{normalized.status}"
            await uow.session.commit()
            return {"status": f"ignored_status_{normalized.status}"}

        # 4. DOMAIN STEP: MARK PAID
        paid_uc = MarkInvoicePaidUseCase(uow)
        ok = await paid_uc.execute(
            invoice,
            normalized.tx_hash,
            paid_asset=normalized.paid_asset,
            paid_amount=normalized.paid_amount,
            paid_fiat_rate=normalized.paid_fiat_rate,
        )

        if not ok:
            event.failed = True
            event.last_error = "invalid_transition"
            await uow.session.commit()
            return {"status": "invalid_transition"}

        # 4.5 SIDE EFFECT: REFERRAL ACCRUAL
        # referral_program.md: accrual is a side effect of the SAME
        # idempotent webhook pipeline, in the SAME transaction/checkpoint
        # as the PAID transition - not after delivery, not best-effort.
        # invoice.user is already loaded via selectinload in
        # get_by_external_payment_id().
        if invoice.user and invoice.user.referred_by_id:
            existing_accrual = await uow.referral_accruals.get_by_invoice_id(
                invoice.id
            )
            if not existing_accrual:
                accrual = ReferralAccrual(
                    invoice_id=invoice.id,
                    referrer_id=invoice.user.referred_by_id,
                    referred_user_id=invoice.user.id,
                    amount=invoice.amount * settings.REFERRAL_PERCENT / 100,
                    currency=invoice.currency,
                    percent=settings.REFERRAL_PERCENT,
                )
                await uow.referral_accruals.create_accrual(accrual)

        # CHECKPOINT COMMIT
        # invoice_state_machine.md: "Delivery failure does NOT change
        # invoice state." idempotency.md: "invoice transition" and
        # "delivery trigger" are separate allowed side effects. Commit
        # the PAID transition + PaymentEvent now, BEFORE attempting
        # delivery, so that any failure during delivery - including
        # infrastructure exceptions, not just a returned False - can
        # never roll back the payment state or lose the event record.
        await uow.session.commit()

        # 5. SIDE EFFECT: DELIVERY
        try:
            delivery_service = DeliveryService(uow=uow)
            deliver_uc = DeliverInvoiceUseCase(delivery_service)
            ok = await deliver_uc.execute(invoice)
        except Exception as exc:
            ok = False
            event.last_error = f"delivery_exception: {exc}"

        # 6. FINAL EVENT STATE
        if ok:
            event.processed = True
        else:
            event.failed = True
            if not event.last_error:
                event.last_error = "delivery_failed"

        # 7. FINAL COMMIT
        await uow.session.commit()

    return {"status": "accepted"}
