import uuid

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infrastructure.database.uow import (
    UnitOfWork,
)

from app.services.delivery_service import (
    DeliveryService,
)

from app.services.invoice_service import (
    InvoiceService,
)

router = Router()


@router.message(Command("paytest"))
async def paytest_command(
    message: Message,
    bot: Bot,
):

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "Usage: /paytest <invoice_id>"
        )

        return

    invoice_id = int(parts[1])

    async with UnitOfWork() as uow:

        invoice_service = InvoiceService(uow)

        delivery_service = DeliveryService(bot)

        invoice = await (
            uow.invoices.get_by_id(invoice_id)
        )

        if not invoice:

            await message.answer(
                "Invoice not found"
            )

            return

        fake_tx_hash = uuid.uuid4().hex

        try:

            await invoice_service.mark_paid(
                invoice=invoice,
                tx_hash=fake_tx_hash,
            )

        except ValueError as e:

            await message.answer(str(e))

            return

        product = invoice.product

        user = invoice.user

        await delivery_service.deliver_product(
            user_telegram_id=user.telegram_id,
            product=product,
        )

    await message.answer(
        f"Invoice #{invoice.id} paid\n"
        f"TX: {fake_tx_hash[:16]}..."
    )
