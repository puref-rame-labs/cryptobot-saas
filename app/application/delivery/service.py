from app.application.bot_instance import get_bot
from app.infrastructure.database.models import Invoice
from app.domain.invoice.state_machine import InvoiceState


class DeliveryResult:
    def __init__(self, success: bool, reason: str | None = None):
        self.success = success
        self.reason = reason


class DeliveryService:

    def __init__(self, bot=None, uow=None):
        self.bot = bot or get_bot()
        self.uow = uow

    async def deliver(self, invoice: Invoice, user_id: int) -> DeliveryResult:

        # IDEMPOTENCY GUARANTEE (state-based)
        if invoice.status == InvoiceState.DELIVERED.value:
            return DeliveryResult(success=True, reason="already_delivered")

        if invoice.status != InvoiceState.PAID.value:
            return DeliveryResult(success=False, reason="invalid_state")

        product = await self.uow.products.get_by_id(invoice.product_id)

        if not product or not product.telegram_file_id:
            return DeliveryResult(success=False, reason="missing_file")

        try:
            caption = f"Your product: {product.title}"

            if product.file_type == "photo":
                await self.bot.send_photo(
                    chat_id=user_id,
                    photo=product.telegram_file_id,
                    caption=caption,
                )
            else:
                await self.bot.send_document(
                    chat_id=user_id,
                    document=product.telegram_file_id,
                    caption=caption,
                )

            return DeliveryResult(success=True)

        except Exception:
            return DeliveryResult(success=False, reason="telegram_error")
