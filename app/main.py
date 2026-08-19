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
from app.handlers.attach import router as attach_router
from app.handlers.newproduct import router as newproduct_router
from app.handlers.product_select import router as product_router
from app.handlers.testmode import router as testmode_router
from app.handlers.help import router as help_router
from app.handlers.unknown import router as unknown_router
from app.handlers.publish import router as publish_router
from app.handlers.archive import router as archive_router
from app.handlers.referral_stats import router as referral_stats_router
from app.handlers.referral_payouts import router as referral_payouts_router
from app.handlers.refund import router as refund_router

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

    async with UnitOfWork() as uow:
        await BootstrapCatalogUseCase(uow).execute()

    dp.include_router(start_router)
    dp.include_router(buy_router)
    dp.include_router(attach_router)
    dp.include_router(newproduct_router)
    dp.include_router(product_router)
    dp.include_router(testmode_router)
    dp.include_router(help_router)
    dp.include_router(publish_router)
    dp.include_router(archive_router)
    dp.include_router(referral_stats_router)
    dp.include_router(referral_payouts_router)
    dp.include_router(refund_router)
    dp.include_router(catalog_navigation_router)
    dp.include_router(unknown_router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="buy", description="Оформить покупку"),
            BotCommand(command="help", description="Как пополнить баланс"),
            BotCommand(command="referral_stats", description="Моя реферальная статистика"),
        ],
        scope=BotCommandScopeDefault(),
    )

    for admin_id in settings.ADMIN_IDS:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Запустить бота"),
                BotCommand(command="buy", description="Оформить покупку"),
                BotCommand(command="attach", description="Прикрепить файл"),
                BotCommand(command="newproduct", description="Создать товар"),
                BotCommand(command="publish", description="Опубликовать товар"),
                BotCommand(command="archive", description="Архивировать товар"),
                BotCommand(command="testmode", description="Переключить testnet"),
                BotCommand(command="referral_payouts", description="Реферальные выплаты"),
                BotCommand(command="refund", description="Вернуть оплату по инвойсу"),
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
