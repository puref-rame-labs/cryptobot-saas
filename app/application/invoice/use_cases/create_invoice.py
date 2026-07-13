from datetime import datetime, timedelta

from app.infrastructure.database.models import Invoice
from app.application.payments.factory import get_payment_provider
from app.domain.invoice.state_machine import InvoiceState as InvoiceStatus
from app.domain.product.policy import ProductPolicy


class CreateInvoiceUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, user, product, provider_name: str = "mock", network: str = "mainnet"):

        # 1. DOMAIN GUARD
        if product.status is None:
            raise ValueError("Product invalid state")

        if not ProductPolicy.can_be_purchased(product.status):
            raise ValueError(f"Product not purchasable: {product.status}")

        if not product.telegram_file_id:
            raise ValueError("Product not deliverable")

        # 2. DUPLICATE INVOICE GUARD (DDoS / spam mitigation)
        existing = await self.uow.invoices.get_active_by_user_and_product(
            user_id=user.id,
            product_id=product.id,
            network=network,
        )

        if existing:
            return {
                "invoice": existing,
                "payment_data": None,
                "payment_url": existing.payment_url,
            }

        # 3. ENTITY BUILD
        invoice = Invoice(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            currency=product.currency,
            status=InvoiceStatus.PENDING.value,
            provider=provider_name,
            network=network,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )

        # 4. PERSIST
        self.uow.invoices.session.add(invoice)
        await self.uow.session.flush()

        # 5. PAYMENT PROVIDER
        provider = get_payment_provider(provider_name, network=network)
        payment_data = await provider.create_invoice(invoice)

        # 6. UPDATE ENTITY
        invoice.external_payment_id = str(payment_data.external_id)
        invoice.payment_url = payment_data.payment_url
        await self.uow.session.flush()

        return {
            "invoice": invoice,
            "payment_data": payment_data,
            "payment_url": invoice.payment_url,
        }
