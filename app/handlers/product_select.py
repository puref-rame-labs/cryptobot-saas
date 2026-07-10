from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.application.invoice.use_cases.create_invoice import CreateInvoiceUseCase

router = Router()


@router.callback_query(F.data.startswith("product:"))
async def select_product(callback: CallbackQuery):

    product_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await callback.answer("Product not found", show_alert=True)
            return

        user = callback.from_user

        use_case = CreateInvoiceUseCase(uow)
        result = await use_case.execute(
            user,
            product,
            provider_name=settings.DEFAULT_PAYMENT_PROVIDER,
        )

        invoice = result["invoice"]
        payment = result["payment_data"]

        await callback.message.answer(
            f"Invoice #{invoice.id} created\n"
            f"Amount: {invoice.amount} {invoice.currency}\n"
            f"Status: {invoice.status}\n\n"
            f"{payment.payment_url}"
        )

    await callback.answer()
