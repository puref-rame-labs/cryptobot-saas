import uuid
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import settings
from app.domain.events import InvoicePaidEvent
from app.services.event_dispatcher import EventDispatcher

router = Router()


@router.message(Command("paytest"))
async def paytest_command(message: Message, bot: Bot):

    # 1. security gate
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Access denied")
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /paytest <invoice_id>")
        return

    invoice_id = parts[1]

    # 2. simulate EXACT SAME EVENT as webhook
    event = InvoicePaidEvent(
        provider="mock",
        external_payment_id=str(invoice_id),
        tx_hash=uuid.uuid4().hex,
    )

    # 3. send into event pipeline
    await EventDispatcher.dispatch(event)

    await message.answer(
        f"Simulated payment event sent\n"
        f"Invoice: {invoice_id}\n"
        f"TX: {event.tx_hash[:16]}..."
    )
