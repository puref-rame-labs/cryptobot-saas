from app.services.payments.base import (
    BasePaymentProvider,
)

from app.services.payments.schemas import (
    PaymentInvoice,
)


class MockPaymentProvider(
    BasePaymentProvider
):

    async def create_invoice(
        self,
        invoice,
    ):

        return PaymentInvoice(
            payment_url=(
                f"https://mock.pay/{invoice.id}"
            ),
            external_id=str(invoice.id),
        )
