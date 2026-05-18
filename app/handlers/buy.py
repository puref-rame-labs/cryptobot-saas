from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.handlers.keyboards.products import products_kb
from app.services.user_service import UserService

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):

    async with UnitOfWork() as uow:

        user_service = UserService(uow)

        user = await user_service.register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        products = await uow.products.get_all_active()

        if not products:
            await message.answer("No active products.")
            return

        await message.answer(
            "Select product:",
            reply_markup=products_kb(products)
        )
