from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config.settings import settings
from app.states.upload_state import (
    UploadStates,
)

router = Router()


@router.message(Command("attach"))
async def attach_command(
    message: Message,
    state: FSMContext,
):

    if message.from_user.id not in settings.ADMIN_IDS:

        await message.answer(
            "Access denied"
        )
        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "Usage: /attach <product_id>"
        )
        return

    product_id = int(parts[1])

    await state.update_data(
        product_id=product_id
    )

    await state.set_state(
        UploadStates.waiting_for_file
    )

    await message.answer(
        "Send file for product"
    )
