import json
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.infrastructure.database.uow import UnitOfWork
from app.infrastructure.database.models import PaymentEvent
from app.services.payments.webhook_factory import get_webhook_adapter

router = APIRouter()


class PaymentWebhookSchema(BaseModel):
    provider: str
    external_payment_id: str
    status: str


@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhookSchema,
    x_webhook_secret: str = Header(),
):

    payload_dict = payload.model_dump()
    provider = payload_dict.get("provider", "mock")

    adapter = get_webhook_adapter(provider)

    # 1. verify signature
    is_valid = await adapter.verify_signature(
        headers={"x-webhook-secret": x_webhook_secret},
        payload=payload_dict,
    )

    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # 2. normalize provider payload
    normalized = await adapter.normalize(payload_dict)

    # 3. persist raw event (audit log only)
    async with UnitOfWork() as uow:
        invoice = await (
            uow.invoices
            .get_by_external_payment_id(
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
                    provider=provider,
                    payload=json.dumps({
                        "invoice_id": invoice.id,
                        "external_payment_id": normalized.external_payment_id,
                        "tx_hash": normalized.tx_hash,
                    }),
                )
            )
        )
    
    return {"status": "accepted"}
