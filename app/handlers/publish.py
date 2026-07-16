from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.domain.product.state_machine import ProductStateMachine, ProductState

router = Router()


@router.message(Command("publish"))
async def publish_product(message: Message, command: CommandObject):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Доступ запрещён")
        return

    if not command.args:
        await message.answer("Использование: /publish <product_id>")
        return

    try:
        product_id = int(command.args)
    except ValueError:
        await message.answer("Некорректный product_id")
        return

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await message.answer("Товар не найден")
            return

        if product.status != ProductState.READY.value:
            await message.answer(f"Нельзя опубликовать из статуса {product.status}")
            return

        product.status = ProductStateMachine.mark_published(product.status)

        await uow.session.flush()

    await message.answer(f"Товар {product_id} опубликован")
