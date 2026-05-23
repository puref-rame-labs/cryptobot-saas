from app.services.invoice_service import InvoiceService
from app.services.delivery_service import DeliveryService
from app.infrastructure.database.uow import UnitOfWork
from aiogram import Bot


class PaymentService:

    def __init__(self, uow: UnitOfWork, bot: Bot):
        self.uow = uow
        self.bot = bot

    async def process_payment(
        self,
        provider: str,
        external_payment_id: str,
        tx_hash: str | None = None,
    ):

        invoice = await self.uow.invoices.get_by_external_payment_id(
            external_payment_id
        )

        if not invoice:
            return {"status": "invoice_not_found"}

        if invoice.status == "PAID":
            return {"status": "already_processed"}

        invoice_service = InvoiceService(self.uow)

        await invoice_service.mark_paid(
            invoice=invoice,
            tx_hash=tx_hash,
        )

        delivery_service = DeliveryService(
            bot=self.bot,
            uow=self.uow,
        )

        await delivery_service.deliver(
            invoice=invoice,
            user_id=invoice.user.telegram_id,
        )

        return {"status": "ok"}
