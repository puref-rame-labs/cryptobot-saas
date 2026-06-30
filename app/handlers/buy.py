from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.services.product_service import ProductService
from app.services.user_service import UserService
from app.services.invoice.use_cases.create_invoice import CreateInvoiceUseCase
from app.domain.product.policy import ProductPolicy

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):

    async with UnitOfWork() as uow:

        user = await UserService(uow).register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        products = await ProductService(uow).get_catalog()

        if not products:
            await message.answer("No active products.")
            return

        # FIX: выбираем первый ПРИГОДНЫЙ к покупке товар
        product = next(
            (p for p in products if ProductPolicy.can_be_purchased(p.status)),
            None
        )

        if not product:
            await message.answer("No purchasable products.")
            return

        use_case = CreateInvoiceUseCase(uow)
        result = await use_case.execute(user, product)

    invoice = result["invoice"]
    payment = result["payment_data"]

    await message.answer(
        f"Invoice #{invoice.id}\n"
        f"{invoice.amount} {invoice.currency}\n\n"
        f"{payment.payment_url}"
    )
