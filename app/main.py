import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.config.settings import settings
from app.config.logging import setup_logging
from app.handlers.start import router
from app.infrastructure.database.init_db import init_db

from app.infrastructure.database.uow import UnitOfWork

async def main():
    setup_logging()

    bot = Bot(token=settings.BOT_TOKEN)

    await init_db()

    async with UnitOfWork() as uow:
        from app.services.product_service import (
            ProductService,
        )
    
        product_service = ProductService(uow)
    
        await product_service.bootstrap_products()

    dp = Dispatcher()

    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(
            command="start",
            description="Start bot"
        )
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
