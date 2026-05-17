from datetime import datetime, timedelta

from app.infrastructure.database.models import (
    Invoice,
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
            expires_at=expires_at,
        )

        await self.uow.invoices.create_invoice(
            invoice
        )

        return invoice
