from datetime import datetime, timedelta

from app.domain.invoice_status import InvoiceStatus
from app.services.payments.factory import get_payment_provider
from app.infrastructure.database.models import Invoice


class InvoiceService:

    def __init__(self, uow):
        self.uow = uow

    async def create_invoice(self, user, product):

        # временно фиксируем provider (mock)
        provider_name = "mock"
        provider = get_payment_provider(provider_name)

        invoice = Invoice(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            currency=product.currency,
            status=InvoiceStatus.PENDING,
            provider=provider_name,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )

        invoice = await self.uow.invoices.create_invoice(
            invoice=invoice
        )

        payment_data = await provider.create_invoice(invoice)

        invoice.external_payment_id = str(
            payment_data.external_id
        ).replace("'", "")

        await self.uow.session.commit()

        return {
            "invoice": invoice,
            "payment_data": payment_data,
        }

    async def mark_paid(self, invoice, tx_hash: str):

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Invoice already paid")

        invoice.status = InvoiceStatus.PAID
        invoice.tx_hash = tx_hash

        await self.uow.session.commit()
