from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.application.user_service import UserService

router = Router()


@router.message(CommandStart())
async def start_command(message: Message):

    async with UnitOfWork() as uow:
        service = UserService(uow)

        user = await service.register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

    await message.answer(
        f"Welcome, user #{user.id}\n\n"
        f"Используйте /buy, чтобы посмотреть каталог.\n"
        f"Если нужно пополнить баланс для оплаты — команда /help."
    )
