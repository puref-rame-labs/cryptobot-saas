from datetime import datetime, timedelta

from app.domain.invoice_status import InvoiceStatus

from app.services.payments.factory import (
    get_payment_provider,
)

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

        #
        # temporary fixed provider
        #
        provider_name = "mock"

        provider = get_payment_provider(
            provider_name
        )

        invoice = Invoice(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            currency=product.currency,
            status=InvoiceStatus.PENDING,
            provider=provider_name,
            expires_at=(
                datetime.utcnow()
                + timedelta(minutes=15)
            ),
        )

        invoice = await (
            self.uow.invoices.create_invoice(
                invoice=invoice
            )
        )

        payment_data = await (
            provider.create_invoice(invoice)
        )

        invoice.external_payment_id = str(
            payment_data.external_id
        ).replace("'", "")

        await self.uow.session.commit()

        return {
            "invoice": invoice,
            "payment_data": payment_data,
        }

    async def mark_paid(
        self,
        invoice,
        tx_hash: str | None,
    ) -> bool:

        #
        # idempotent state guard
        #
        if invoice.status == InvoiceStatus.PAID:

            return False

        #
        # state transition
        #
        invoice.status = InvoiceStatus.PAID

        #
        # tx_hash must not mutate repeatedly
        #
        if tx_hash and not invoice.tx_hash:

            invoice.tx_hash = tx_hash

        await self.uow.session.flush()

        return True
