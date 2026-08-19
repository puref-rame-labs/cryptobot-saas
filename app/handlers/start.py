from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.application.user_service import UserService

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, command: CommandObject):

    ref_code = None

    if command.args and command.args.startswith("ref_"):
        ref_code = command.args[len("ref_"):]

    async with UnitOfWork() as uow:
        service = UserService(uow)

        user = await service.register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            ref_code=ref_code,
        )

    bot_username = (await message.bot.get_me()).username

    display_name = (
        message.from_user.first_name
        or message.from_user.username
        or "друг"
    )

    await message.answer(
        f"Добро пожаловать, {display_name}!\n\n"
        f"Используйте /buy, чтобы посмотреть каталог.\n"
        f"Если нужно пополнить баланс для оплаты — команда /help.\n\n"
        f"Ваша реферальная ссылка:\n"
        f"https://t.me/{bot_username}?start=ref_{user.referral_code}"
    )
