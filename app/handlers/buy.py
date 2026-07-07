from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.application.user_service import UserService
from app.application.catalog.use_cases.get_catalog import GetCatalogUseCase
from app.application.invoice.use_cases.create_invoice import CreateInvoiceUseCase

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):

    async with UnitOfWork() as uow:

        user = await UserService(uow).register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        products = await GetCatalogUseCase(uow).execute()

        if not products:
            await message.answer("No purchasable products.")
            return

        product = await uow.products.get_by_id(products[0].id)

        result = await CreateInvoiceUseCase(uow).execute(
            user,
            product,
            provider_name=settings.DEFAULT_PAYMENT_PROVIDER,
        )

    invoice = result["invoice"]
    payment = result["payment_data"]

    await message.answer(
        f"Invoice #{invoice.id}\n"
        f"{invoice.amount} {invoice.currency}\n\n"
        f"{payment.payment_url}"
    )
