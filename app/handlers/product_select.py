from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.infrastructure.database.uow import UnitOfWork
from app.services.invoice_service import InvoiceService

router = Router()


@router.callback_query(F.data.startswith("product:"))
async def select_product(callback: CallbackQuery):

    product_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await callback.answer(
                "Product not found",
                show_alert=True
            )
            return

        invoice_service = InvoiceService(uow)

        invoice = await invoice_service.create_invoice(
            user=callback.from_user,
            product=product,
        )

        await callback.message.answer(
            f"Invoice #{invoice.id} created\n"
            f"Amount: {invoice.amount} {invoice.currency}\n"
            f"Status: {invoice.status}"
        )

    await callback.answer()
