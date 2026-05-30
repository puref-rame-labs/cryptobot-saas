import json

from fastapi import HTTPException

from app.infrastructure.database.models import (
    PaymentEvent,
)
from app.infrastructure.database.uow import (
    UnitOfWork,
)
from app.services.payments.factory import (
    get_payment_provider,
)


async def handle_webhook(
    payload: dict,
    headers: dict,
):

    provider_name = payload.get(
        "provider",
        "mock",
    )

    payment_provider = get_payment_provider(
        provider_name
    )

    is_valid = await (
        payment_provider.verify_signature(
            headers=headers,
            payload=payload,
        )
    )

    if not is_valid:

        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature",
        )

    normalized = await (
        payment_provider.normalize(payload)
    )

    async with UnitOfWork() as uow:

        invoice = await (
            uow.invoices.get_by_external_payment_id(
                normalized.external_payment_id
            )
        )

        if not invoice:

            return {
                "status": "invoice_not_found"
            }

        await (
            uow.payment_events.create_event(
                PaymentEvent(
                    invoice_id=invoice.id,
                    event_type="webhook_received",
                    provider=provider_name,
                    payload=json.dumps({
                        "invoice_id": invoice.id,
                        "external_payment_id": (
                            normalized.external_payment_id
                        ),
                        "tx_hash": (
                            normalized.tx_hash
                        ),
                        "status": (
                            normalized.status
                        ),
                    }),
                )
            )
        )

        await uow.session.commit()

    return {
        "status": "accepted"
    }
