from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork

router = Router()


@router.message(Command("referral_stats"))
async def referral_stats_command(message: Message):

    async with UnitOfWork() as uow:

        user = await uow.users.get_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("Сначала запустите /start")
            return

        rows = await uow.referral_accruals.get_summary_for_referrer(
            user.id
        )

    pending_amount = 0
    pending_count = 0
    paid_out_amount = 0
    paid_out_count = 0

    for status, amount, count in rows:
        if status == "PENDING":
            pending_amount = amount or 0
            pending_count = count or 0
        elif status == "PAID_OUT":
            paid_out_amount = amount or 0
            paid_out_count = count or 0

    text = (
        "📊 <b>Ваша реферальная статистика</b>\n\n"
        f"Ваш код: <code>{user.referral_code}</code>\n\n"
        f"💰 Накоплено (ожидает выплаты): {pending_amount} RUB "
        f"({pending_count} покупок)\n"
        f"✅ Уже выплачено: {paid_out_amount} RUB "
        f"({paid_out_count} покупок)"
    )

    await message.answer(text, parse_mode="HTML")
