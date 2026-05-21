import json
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
)
from pydantic import BaseModel
from aiogram import Bot
from app.config.settings import settings
from app.infrastructure.database.uow import (
    UnitOfWork,
)
from app.services.invoice_service import (
    InvoiceService,
)
from app.services.delivery_service import (
    DeliveryService,
)
from app.services.payments.webhook_factory import (
    get_webhook_adapter,
)
from app.infrastructure.database.models import (
    PaymentEvent,
)

router = APIRouter()

class PaymentWebhookSchema(
    BaseModel
):

    provider: str
    external_payment_id: str
    status: str

@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhookSchema,
    x_webhook_secret: str = Header(),
):

    payload = payload.model_dump()
    
    provider = payload.get(
        "provider",
        "mock",
    )
    
    adapter = get_webhook_adapter(
        provider
    )

    is_valid = await (
        adapter.verify_signature(
            headers={
                "x-webhook-secret":
                x_webhook_secret
            },
            payload=payload,
        )
    )

    if not is_valid:

        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature",
        )

    normalized = await (
        adapter.normalize(payload)
    )

    print(
        "NORMALIZED:",
        normalized,
    )

    async with UnitOfWork() as uow:
    
        invoice = await (
            uow.invoices
            .get_by_external_payment_id(
                normalized
                .external_payment_id
            )
        )
    
        if not invoice:
    
            return {
                "status":
                "invoice_not_found"
            }
    
        await (
            uow.payment_events.create_event(
                PaymentEvent(
                    invoice_id=invoice.id,
                    event_type="webhook_received",
                    provider=provider,
                    payload=json.dumps(
                        payload
                    ),
                )
            )
        )
    
        if invoice.status == "PAID":
    
            return {
                "status":
                "already_processed"
            }
    
        invoice_service = InvoiceService(
            uow
        )

        await invoice_service.mark_paid(
            invoice=invoice,
            tx_hash=(
                normalized.tx_hash
            ),
        )

        bot = Bot(
            token=settings.BOT_TOKEN
        )

        delivery_service = DeliveryService(
            bot=bot,
            uow=uow,
        )

        await delivery_service.deliver(
            invoice=invoice,
            user_id=(
                invoice.user.telegram_id
            ),
        )

        await bot.session.close()

    return {
        "status": "ok"
    }
    
