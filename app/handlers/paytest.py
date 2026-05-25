import json
import uuid

from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import settings

from app.infrastructure.database.models import (
    PaymentEvent,
)

from app.infrastructure.database.uow import (
    UnitOfWork,
)

router = Router()


@router.message(Command("paytest"))
async def paytest_command(message: Message, bot: Bot):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Access denied")
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer(
            "Usage: /paytest <external_payment_id>"
        )
        return

    external_payment_id = parts[1]

    async with UnitOfWork() as uow:

        invoice = await (
            uow.invoices.get_by_external_payment_id(
                external_payment_id
            )
        )

        if not invoice:

            await message.answer(
                "Invoice not found"
            )
            return

        payload = {
            "invoice_id": invoice.id,
            "external_payment_id": external_payment_id,
            "tx_hash": uuid.uuid4().hex,
        }

        event = PaymentEvent(
            invoice_id=invoice.id,
            event_type="webhook_received",
            provider="mock",
            payload=json.dumps(payload),
        )

        await (
            uow.payment_events.create_event(event)
        )

        await uow.session.commit()

    await message.answer(
        f"Payment event queued\n"
        f"Invoice ID: {invoice.id}\n"
        f"External ID: {external_payment_id}"
    )
