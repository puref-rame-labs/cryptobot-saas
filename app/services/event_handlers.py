from app.services.invoice_service import InvoiceService
from app.services.delivery_service import DeliveryService
from app.infrastructure.database.uow import UnitOfWork
from app.services.bot_instance import get_bot

async def handle_invoice_paid(event):

    async with UnitOfWork() as uow:

        invoice = await (
            uow.invoices.get_by_external_payment_id(
                event.external_payment_id
            )
        )

        if not invoice:
            return

        if invoice.status == "PAID" and invoice.delivered:
            return

        service = InvoiceService(uow)

        await service.mark_paid(
            invoice=invoice,
            tx_hash=event.tx_hash,
        )

        delivery = DeliveryService(
            bot=get_bot(),
            uow=uow,
        )

        await delivery.deliver(
            invoice=invoice,
            user_id=invoice.user.telegram_id,
        )

        await uow.session.commit()
