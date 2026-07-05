from fastapi import HTTPException

from app.services.payments.factory import (
    get_payment_provider,
)

from app.services.payments.use_cases.process_payment_event import (
    process_payment_event,
)


async def handle_webhook(
    provider_name: str,
    payload: dict,
    headers: dict,
):
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

    return await process_payment_event(
        normalized=normalized,
        provider_name=provider_name,
    )
