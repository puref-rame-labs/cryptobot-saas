from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork

router = Router()


@router.message(Command("referral_payouts"))
async def referral_payouts_command(message: Message, command: CommandObject):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Доступ запрещён")
        return

    # No args: list referrers with PENDING accruals.
    if not command.args:

        async with UnitOfWork() as uow:
            rows = await uow.referral_accruals.get_pending_totals_by_referrer()

        if not rows:
            await message.answer("Нет ожидающих выплат")
            return

        lines = ["💸 <b>Ожидающие выплаты</b>\n"]

        for referrer_id, amount, count in rows:
            lines.append(
                f"referrer_id={referrer_id}: {amount} RUB ({count} начислений)"
            )

        lines.append(
            "\nЧтобы отметить выплаченным:\n"
            "/referral_payouts <referrer_id>"
        )

        await message.answer("\n".join(lines), parse_mode="HTML")
        return

    # With arg: mark all PENDING accruals for that referrer as PAID_OUT.
    try:
        referrer_id = int(command.args)
    except ValueError:
        await message.answer("Некорректный referrer_id")
        return

    async with UnitOfWork() as uow:
        count = await uow.referral_accruals.mark_paid_out_for_referrer(
            referrer_id
        )

    if count == 0:
        await message.answer(
            f"Нет ожидающих начислений для referrer_id={referrer_id}"
        )
        return

    await message.answer(
        f"✅ Отмечено выплаченным: {count} начислений "
        f"для referrer_id={referrer_id}"
    )
