import json
import hashlib

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.models import PaymentEvent
from app.infrastructure.database.uow import UnitOfWork
from app.services.invoice_service import InvoiceService
from app.services.bot_instance import get_bot
from app.services.delivery.service import DeliveryService


def build_idempotency_key(
    provider: str,
    external_payment_id: str,
    event_type: str,
) -> str:
    raw = f"{provider}:{external_payment_id}:{event_type}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def process_payment_event(
    normalized,
    provider_name: str,
):

    idempotency_key = build_idempotency_key(
        provider=provider_name,
        external_payment_id=normalized.external_payment_id,
        event_type="payment",
    )

    async with UnitOfWork() as uow:

        invoice = await uow.invoices.get_by_external_payment_id(
            normalized.external_payment_id
        )

        if not invoice:
            return {"status": "invoice_not_found"}

        event = PaymentEvent(
            invoice_id=invoice.id,
            provider=provider_name,
            event_type="payment",
            idempotency_key=idempotency_key,
            processed=False,
            payload=json.dumps(
                {
                    "invoice_id": invoice.id,
                    "external_payment_id": normalized.external_payment_id,
                    "tx_hash": normalized.tx_hash,
                    "status": normalized.status,
                }
            ),
        )

        try:
            await uow.payment_events.create_event(event)

            invoice_service = InvoiceService(uow)

            await invoice_service.mark_paid(
                invoice=invoice,
                tx_hash=normalized.tx_hash,
            )

            delivery = DeliveryService(bot=get_bot(), uow=uow)

            result = await delivery.deliver(
                invoice=invoice,
                user_id=invoice.user.telegram_id,
            )

            if result.success:
                invoice.status = "DELIVERED"
                invoice.delivered = True
            else:
                invoice.status = "FAILED"

            event.processed = True

            await uow.session.commit()

        except IntegrityError:
            await uow.session.rollback()
            return {"status": "duplicate"}

    return {"status": "accepted"}
