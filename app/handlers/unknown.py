from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def unknown_handler(
    message: Message,
):

    if (
        message.text
        and message.text.startswith("/")
    ):

        await message.answer(
            "Unknown command."
        )
