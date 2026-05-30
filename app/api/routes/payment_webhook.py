from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.services.payments.use_cases.handle_webhook import (
    handle_webhook,
)

router = APIRouter()


class PaymentWebhookSchema(BaseModel):
    provider: str
    external_payment_id: str
    status: str
    tx_hash: str | None = None


@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhookSchema,
    x_webhook_secret: str = Header(),
):

    return await handle_webhook(
        payload=payload.model_dump(),
        headers={
            "x-webhook-secret": x_webhook_secret,
        },
    )
