import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from aiogram.fsm.storage.memory import MemoryStorage
from app.application import bot_instance

from app.config.settings import settings
from app.config.logging import setup_logging

from app.handlers.start import router as start_router
from app.handlers.buy import router as buy_router
from app.handlers.catalog_navigation import router as catalog_navigation_router
from app.handlers.paytest import router as paytest_router
from app.handlers.upload import router as upload_router
from app.handlers.attach import router as attach_router
from app.handlers.newproduct import router as newproduct_router
from app.handlers.product_select import router as product_router
from app.handlers.testmode import router as testmode_router
from app.handlers.help import router as help_router
from app.handlers.unknown import router as unknown_router
from app.handlers.publish import router as publish_router

from app.infrastructure.database.init_db import init_db
from app.infrastructure.database.uow import UnitOfWork
from app.application.catalog.use_cases.bootstrap_catalog import BootstrapCatalogUseCase
from app.workers.invoice_expiry import invoice_expiry_loop
from app.api.server import run_api


async def main():

    setup_logging()

    bot = Bot(token=settings.BOT_TOKEN)

    bot_instance.bot = bot
    assert bot_instance.bot is not None
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()

    async with UnitOfWork() as uow:
        await BootstrapCatalogUseCase(uow).execute()

    dp.include_router(start_router)
    dp.include_router(buy_router)
    dp.include_router(paytest_router)
    dp.include_router(upload_router)
    dp.include_router(attach_router)
    dp.include_router(newproduct_router)
    dp.include_router(product_router)
    dp.include_router(testmode_router)
    dp.include_router(help_router)
    dp.include_router(publish_router)
    dp.include_router(catalog_navigation_router)
    dp.include_router(unknown_router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start bot"),
            BotCommand(command="buy", description="Create invoice"),
            BotCommand(command="help", description="How to top up balance"),
        ],
        scope=BotCommandScopeDefault(),
    )

    for admin_id in settings.ADMIN_IDS:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Start bot"),
                BotCommand(command="buy", description="Create invoice"),
                BotCommand(command="paytest", description="Simulate payment"),
                BotCommand(command="upload", description="Upload digital asset"),
                BotCommand(command="attach", description="Attach file"),
                BotCommand(command="newproduct", description="Create product"),
                BotCommand(command="publish", description="Publish product"),
                BotCommand(command="testmode", description="Toggle testnet payments"),
            ],
            scope=BotCommandScopeChat(chat_id=admin_id),
        )

    expiry_task = asyncio.create_task(invoice_expiry_loop())
    api_task = asyncio.create_task(run_api())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    try:
        await asyncio.gather(api_task, bot_task)
    finally:
        expiry_task.cancel()
        api_task.cancel()
        bot_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
