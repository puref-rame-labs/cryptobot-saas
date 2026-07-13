from fastapi import HTTPException

from app.application.payments.factory import (
    get_payment_provider,
)

from app.application.payments.use_cases.process_payment_event import (
    process_payment_event,
)

from app.infrastructure.database.uow import UnitOfWork


async def handle_webhook(
    provider_name: str,
    payload: dict,
    raw_body: str,
    headers: dict,
):
    # Read-only lookup, before signature verification: no side effects,
    # so this does not violate the idempotency gate. We need to know
    # which network the invoice was created on to pick the right
    # provider credentials for verify_signature.
    inner_payload = payload.get("payload", payload)
    external_payment_id = inner_payload.get("invoice_id")

    network = "mainnet"

    if external_payment_id is not None:
        async with UnitOfWork() as uow:
            invoice = await uow.invoices.get_by_external_payment_id(
                str(external_payment_id)
            )
            if invoice:
                network = invoice.network

    payment_provider = get_payment_provider(
        provider_name,
        network=network,
    )

    is_valid = await payment_provider.verify_signature(
        headers=headers,
        payload=raw_body,
    )

    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature",
        )

    normalized = await payment_provider.normalize(payload)

    return await process_payment_event(
        normalized=normalized,
        provider_name=provider_name,
    )
