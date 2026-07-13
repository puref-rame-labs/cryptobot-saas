from dataclasses import dataclass
from decimal import Decimal

from app.domain.payment.dto.payment_event_dto import (
    PaymentEventDTO,
)
from app.application.payments.providers.base import (
    BasePaymentProvider,
)

# Test-only fixed rate, no external calls.
TEST_RUB_TO_USDT_RATE = Decimal("90")


@dataclass
class MockInvoiceResponse:
    external_id: str
    payment_url: str


class MockPaymentProvider(BasePaymentProvider):

    def __init__(self, network: str = "mainnet"):
        self._network = network

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

        fiat_amount = Decimal(str(payload.get("fiat_amount", "0")))
        paid_amount = (
            fiat_amount / TEST_RUB_TO_USDT_RATE
            if fiat_amount
            else None
        )

        return PaymentEventDTO(
            external_payment_id=payload[
                "external_payment_id"
            ],
            tx_hash=payload.get("tx_hash"),
            status=payload["status"],
            paid_asset="USDT",
            paid_amount=paid_amount,
            paid_fiat_rate=TEST_RUB_TO_USDT_RATE,
        )
