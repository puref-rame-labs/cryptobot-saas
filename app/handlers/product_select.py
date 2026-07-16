from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.application.user_service import UserService
from app.application.invoice.use_cases.create_invoice import CreateInvoiceUseCase

router = Router()

STATUS_LABELS_RU = {
    "PENDING": "Ожидает оплаты",
    "PAID": "Оплачен",
    "EXPIRED": "Истёк",
    "FAILED": "Ошибка оплаты",
    "DELIVERED": "Доставлен",
}


@router.callback_query(F.data.startswith("product:"))
async def select_product(callback: CallbackQuery):

    product_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return

        user = await UserService(uow).register_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )

        is_admin = callback.from_user.id in settings.ADMIN_IDS
        network = "testnet" if (is_admin and user.testnet_override) else "mainnet"

        use_case = CreateInvoiceUseCase(uow)
        result = await use_case.execute(
            user,
            product,
            provider_name=settings.DEFAULT_PAYMENT_PROVIDER,
            network=network,
        )

        invoice = result["invoice"]
        payment_url = result["payment_url"]

        status_ru = STATUS_LABELS_RU.get(invoice.status, invoice.status)

        await callback.message.answer(
            f"Заказ #{invoice.id} создан\n"
            f"Сумма: {invoice.amount} {invoice.currency}\n"
            f"Статус: {status_ru}\n\n"
            f"{payment_url}"
        )

    await callback.answer()
