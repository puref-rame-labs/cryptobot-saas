from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.filters.is_admin import IsAdminFilter
from app.infrastructure.database.uow import UnitOfWork

router = Router()


@router.message(Command("testmode"), IsAdminFilter())
async def testmode_command(message: Message, command: CommandObject):

    arg = (command.args or "").strip().lower()

    async with UnitOfWork() as uow:

        user = await uow.users.get_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("Пользователь не найден. Сначала отправьте /start.")
            return

        if arg == "on":
            user.testnet_override = True
        elif arg == "off":
            user.testnet_override = False
        elif arg == "":
            status = "включён (testnet)" if user.testnet_override else "выключен (mainnet)"
            await message.answer(f"Тестовый режим сейчас: {status}")
            return
        else:
            await message.answer("Использование: /testmode on | off")
            return

        await uow.session.flush()

    status = "включён — следующие покупки пойдут через testnet" if user.testnet_override else "выключен — следующие покупки пойдут через mainnet"
    await message.answer(f"Тестовый режим: {status}")
