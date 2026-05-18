from aiogram import Bot


class DeliveryService:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def deliver_product(
        self,
        user_telegram_id: int,
        product,
    ):

        if not product.telegram_file_id:
            raise ValueError(
                "Product has no attached file"
            )

        if product.file_type == "photo":

            await self.bot.send_photo(
                chat_id=user_telegram_id,
                photo=product.telegram_file_id,
                caption=product.title,
            )

            return

        if product.file_type == "document":

            await self.bot.send_document(
                chat_id=user_telegram_id,
                document=product.telegram_file_id,
                caption=product.title,
            )

            return

        raise ValueError(
            "Unsupported file type"
        )
