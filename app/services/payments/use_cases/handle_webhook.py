import json

from fastapi import HTTPException

from app.infrastructure.database.models import PaymentEvent
from app.infrastructure.database.uow import UnitOfWork

from app.services.payments.webhook_factory import get_webhook_adapter


async def handle_webhook(
    payload: dict,
    headers: dict,
):

    provider = payload.get("provider", "mock")

    adapter = get_webhook_adapter(provider)

    # 1. verify provider signature
    is_valid = await adapter.verify_signature(
        headers=headers,
        payload=payload,
    )

    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature",
        )

    # 2. normalize provider payload
    normalized = await adapter.normalize(payload)

    # 3. persist normalized event
    async with UnitOfWork() as uow:

        invoice = await (
            uow.invoices
            .get_by_external_payment_id(
                normalized.external_payment_id
            )
        )

        if not invoice:
            return

        await (
            uow.payment_events.create_event(
                PaymentEvent(
                    invoice_id=invoice.id,
                    event_type="webhook_received",
                    provider=provider,
                    payload=json.dumps({
                        "invoice_id": invoice.id,
                        "external_payment_id": normalized.external_payment_id,
                        "tx_hash": normalized.tx_hash,
                    }),
                )
            )
        )
