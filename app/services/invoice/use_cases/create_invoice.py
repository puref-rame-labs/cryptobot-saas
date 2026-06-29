from datetime import datetime, timedelta

from app.infrastructure.database.models import Invoice
from app.services.payments.factory import get_payment_provider
from app.domain.invoice_status import InvoiceStatus
from app.domain.product.policy import ProductPolicy


class CreateInvoiceUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, user, product, provider_name: str = "mock"):

        # 1. DOMAIN GUARD
        if product.status is None:
            raise ValueError("Product invalid state")

        if not ProductPolicy.can_be_purchased(product.status):
            raise ValueError(f"Product not purchasable: {product.status}")

        if not product.telegram_file_id:
            raise ValueError("Product not deliverable")

        # 2. ENTITY BUILD
        invoice = Invoice(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            currency=product.currency,
            status=InvoiceStatus.PENDING.value,
            provider=provider_name,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )

        # 3. PERSIST
        self.uow.invoices.session.add(invoice)
        await self.uow.session.flush()

        # 4. PAYMENT PROVIDER
        provider = get_payment_provider(provider_name)
        payment_data = await provider.create_invoice(invoice)

        # 5. UPDATE ENTITY
        invoice.external_payment_id = str(payment_data.external_id)
        await self.uow.session.flush()

        return {
            "invoice": invoice,
            "payment_data": payment_data,
        }
