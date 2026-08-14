from fastapi import HTTPException

from app.application.payments.factory import (
    get_payment_provider,
)

from app.application.payments.use_cases.process_payment_event import (
    process_payment_event,
)

from app.infrastructure.database.uow import UnitOfWork


def _extract_external_payment_id(provider_name: str, payload: dict) -> str | None:
    # Payload shape is provider-specific, so extraction must be too.
    # This runs before verify_signature (see note below), purely to
    # resolve which network's credentials to use - not a business
    # decision, just a lookup key.
    if provider_name == "cryptobot":
        inner_payload = payload.get("payload", payload)
        return inner_payload.get("invoice_id")
    if provider_name == "btcpay":
        return payload.get("invoiceId")
    return None


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
    external_payment_id = _extract_external_payment_id(provider_name, payload)

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
