import json
import hashlib

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.uow import UnitOfWork
from app.infrastructure.database.models import PaymentEvent

from app.application.invoice.use_cases.mark_paid import MarkInvoicePaidUseCase
from app.application.invoice.use_cases.deliver_invoice import DeliverInvoiceUseCase
from app.application.delivery.service import DeliveryService


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

        # 5. SIDE EFFECT: DELIVERY
        delivery_service = DeliveryService(uow=uow)
        deliver_uc = DeliverInvoiceUseCase(delivery_service)

        ok = await deliver_uc.execute(invoice)

        # 6. FINAL EVENT STATE
        if ok:
            event.processed = True
        else:
            event.failed = True
            event.last_error = "delivery_failed"

        # 7. SINGLE COMMIT POINT
        await uow.session.commit()

    return {"status": "accepted"}
