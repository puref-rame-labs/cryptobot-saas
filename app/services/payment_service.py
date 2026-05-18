from app.services.invoice_service import (
    InvoiceService,
)

from app.services.delivery_service import (
    DeliveryService,
)


class PaymentService:

    def __init__(
        self,
        invoice_service,
        delivery_service,
    ):

        self.invoice_service = invoice_service

        self.delivery_service = delivery_service

    async def complete_payment(
        self,
        invoice,
        tx_hash: str,
    ):

        await self.invoice_service.mark_paid(
            invoice=invoice,
            tx_hash=tx_hash,
        )

        await self.delivery_service.deliver_product(
            user_telegram_id=(
                invoice.user.telegram_id
            ),
            product=invoice.product,
        )

        return invoice
