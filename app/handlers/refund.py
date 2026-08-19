from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.application.invoice.use_cases.refund_invoice import RefundInvoiceUseCase

router = Router()


@router.message(Command("refund"))
async def refund_invoice_command(message: Message, command: CommandObject):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Доступ запрещён")
        return

    if not command.args:
        await message.answer("Использование: /refund <invoice_id>")
        return

    try:
        invoice_id = int(command.args)
    except ValueError:
        await message.answer("Некорректный invoice_id")
        return

    async with UnitOfWork() as uow:

        invoice = await uow.invoices.get_by_id(invoice_id)

        if not invoice:
            await message.answer("Инвойс не найден")
            return

        refund_uc = RefundInvoiceUseCase(uow)
        result = await refund_uc.execute(invoice)

        if not result["ok"]:
            await message.answer(
                f"Нельзя вернуть инвойс {invoice_id} "
                f"из статуса {result['status']}"
            )
            return

        await uow.session.commit()

    text = f"✅ Инвойс {invoice_id} помечен как REFUNDED"

    if result.get("clawback_warning"):
        text += f"\n\n{result['clawback_warning']}"

    await message.answer(text)
