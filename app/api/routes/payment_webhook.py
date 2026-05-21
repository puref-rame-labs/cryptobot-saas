from fastapi import (
    APIRouter,
    Header,
    HTTPException,
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

router = APIRouter()


class PaymentWebhook(BaseModel):

    external_payment_id: str
    status: str


@router.post("/payment")
async def payment_webhook(
    payload: PaymentWebhook,
    x_webhook_secret: str = Header(),
):

    print(
        "WEBHOOK:",
        payload.model_dump(),
    )
    if (
        x_webhook_secret
        != settings.WEBHOOK_SECRET
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook secret",
        )

    async with UnitOfWork() as uow:

        invoice = await (
            uow.invoices
            .get_by_external_payment_id(
                payload.external_payment_id
            )
        )

        print("INVOICE:", invoice)

        if not invoice:

            return {
                "status":
                "invoice_not_found"
            }

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
            tx_hash="webhook_tx",
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
            user_id=invoice.user.telegram_id,
        )

        await bot.session.close()

    return {
        "status": "ok"
    }
