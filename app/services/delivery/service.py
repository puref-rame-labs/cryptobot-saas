from app.services.bot_instance import get_bot
from app.services.delivery.exceptions import ProductFileMissing
from app.infrastructure.database.models import Invoice


class DeliveryService:

    def __init__(self, bot=None, uow=None):
        self.bot = bot or get_bot()
        self.uow = uow

    async def deliver(self, invoice: Invoice, user_id: int):
        if invoice.delivered:
            return

        if invoice.status != "PAID":
            return

        product = await self.uow.products.get_by_id(invoice.product_id)
        if not product:
            raise ProductFileMissing("Product not found")

        if not product.telegram_file_id:
            raise ProductFileMissing("No product file attached to product")

        if product.file_type == "photo":
            await self.bot.send_photo(
                chat_id=user_id,
                photo=product.telegram_file_id,
                caption=f"Your product: {product.title}",
            )
        else:
            await self.bot.send_document(
                chat_id=user_id,
                document=product.telegram_file_id,
                caption=f"Your product: {product.title}",
            )

        invoice.delivered = True
        await self.uow.session.flush()
