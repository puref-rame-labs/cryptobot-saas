from dataclasses import dataclass

from app.application.payments.core.dto.payment_event_dto import (
    PaymentEventDTO,
)
from app.application.payments.providers.base import (
    BasePaymentProvider,
)


@dataclass
class MockInvoiceResponse:
    external_id: str
    payment_url: str


class MockPaymentProvider(BasePaymentProvider):

    async def create_invoice(self, invoice):

        return MockInvoiceResponse(
            external_id=f"mock_{invoice.id}",
            payment_url=(
                f"https://mock.provider/pay/{invoice.id}"
            ),
        )

    async def verify_signature(
        self,
        headers: dict,
        payload: dict,
    ) -> bool:

        return True

    async def normalize(
        self,
        payload: dict,
    ) -> PaymentEventDTO:

        return PaymentEventDTO(
            external_payment_id=payload[
                "external_payment_id"
            ],
            tx_hash=payload.get("tx_hash"),
            status=payload["status"],
        )
