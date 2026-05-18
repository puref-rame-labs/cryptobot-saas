from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.services.invoice_service import InvoiceService
from app.services.product_service import ProductService
from app.services.user_service import UserService

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):

    async with UnitOfWork() as uow:

        user_service = UserService(uow)
        product_service = ProductService(uow)
        invoice_service = InvoiceService(uow)

        user = await user_service.register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        products = await product_service.get_catalog()

        if not products:
            await message.answer(
                "No active products."
            )
            return

        product = products[0]

        invoice = await (
            invoice_service.create_invoice(
                user=user,
                product=product,
            )
        )

    await message.answer(
        f"Invoice #{invoice.id} created\n"
        f"Amount: {invoice.amount} "
        f"{invoice.currency}\n"
        f"Status: {invoice.status}"
    )
