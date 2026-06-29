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
        await message.answer("Access denied")
        return

    if not command.args:
        await message.answer("Usage: /publish <product_id>")
        return

    try:
        product_id = int(command.args)
    except ValueError:
        await message.answer("Invalid product_id")
        return

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await message.answer("Product not found")
            return

        if product.status != ProductState.READY.value:
            await message.answer(f"Cannot publish from {product.status}")
            return

        product.status = ProductStateMachine.mark_published(product.status)

        await uow.session.flush()

    await message.answer(f"Product {product_id} published")
