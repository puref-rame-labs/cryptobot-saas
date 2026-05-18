from aiogram.types import FSInputFile


class DeliveryService:

    def __init__(self, bot, uow):
        self.bot = bot
        self.uow = uow

    async def deliver(self, invoice, user_id: int):

        product = await self.uow.products.get_by_id(
            invoice.product_id
        )

        if not product:
            raise ValueError("Product not found")

        if not product.telegram_file_id:
            raise ValueError("No file attached to product")

        if product.file_type == "photo":

            await self.bot.send_photo(
                chat_id=user_id,
                photo=product.telegram_file_id,
                caption=f"Your product: {product.title}",
            )
            return

        await self.bot.send_document(
            chat_id=user_id,
            document=product.telegram_file_id,
            caption=f"Your product: {product.title}",
        )
