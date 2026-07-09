from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.application.user_service import UserService
from app.application.catalog.use_cases.get_catalog_nodes import (
    GetCategoriesUseCase,
)
from app.handlers.keyboards.catalog import categories_kb

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):

    async with UnitOfWork() as uow:

        await UserService(uow).register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        categories = await GetCategoriesUseCase(uow).execute()

    if not categories:
        await message.answer("Каталог пока пуст.")
        return

    await message.answer(
        "Выберите категорию:",
        reply_markup=categories_kb(categories),
    )
