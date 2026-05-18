from datetime import datetime, timedelta

from app.infrastructure.database.models import (
    Invoice,
)

from app.domain.invoice_status import (
    InvoiceStatus,
)


class InvoiceService:

    def __init__(self, uow):
        self.uow = uow

    async def create_invoice(
        self,
        user,
        product,
    ):

        expires_at = (
            datetime.utcnow() + timedelta(minutes=15)
        )

        invoice = Invoice(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            currency=product.currency,
            status=InvoiceStatus.PENDING,
            expires_at=expires_at,
        )

        await self.uow.invoices.create_invoice(
            invoice
        )

        return invoice

    async def mark_paid(
        self,
        invoice,
        tx_hash: str,
    ):

        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError(
                "Only pending invoice can be paid"
            )

        invoice.status = InvoiceStatus.PAID

        invoice.tx_hash = tx_hash

    async def mark_expired(
        self,
        invoice,
    ):

        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError(
                "Only pending invoice can expire"
            )

        invoice.status = InvoiceStatus.EXPIRED
