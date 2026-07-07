from fastapi import APIRouter, Header, Request

from app.application.payments.use_cases.handle_webhook import (
    handle_webhook,
)

router = APIRouter()


@router.post("/payment/{provider_name}")
async def payment_webhook(
    provider_name: str,
    request: Request,
    crypto_pay_api_signature: str = Header(default=""),
    x_webhook_secret: str = Header(default=""),
):
    raw_body = await request.body()
    payload = await request.json()

    return await handle_webhook(
        provider_name=provider_name,
        payload=payload,
        raw_body=raw_body.decode(),
        headers={
            "crypto-pay-api-signature": crypto_pay_api_signature,
            "x-webhook-secret": x_webhook_secret,
        },
    )
