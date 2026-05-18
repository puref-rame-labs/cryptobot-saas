import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.config.settings import settings
from app.config.logging import setup_logging
from app.handlers.start import (
    router as start_router,
)
from app.infrastructure.database.init_db import init_db

from app.infrastructure.database.uow import UnitOfWork
from app.handlers.buy import router as buy_router
from app.handlers.paytest import (
    router as paytest_router,
)
from app.handlers.upload import (
    router as upload_router,
)
from aiogram.fsm.storage.memory import (
    MemoryStorage,
)
from app.handlers.attach import (
    router as attach_router,
)

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

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.include_router(start_router)
    dp.include_router(buy_router)
    dp.include_router(paytest_router)
    dp.include_router(upload_router)
    dp.include_router(attach_router)
    
    await bot.set_my_commands([
        BotCommand(
            command="start",
            description="Start bot"
        ),
        BotCommand(
            command="buy",
            description="Create invoice"
        ),
        BotCommand(
            command="paytest",
            description="Simulate payment"
        ),
        BotCommand(
            command="upload",
            description="Upload digital asset"
        ),
        BotCommand(
            command="attach",
            description="Attach file to product"
        ),
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
