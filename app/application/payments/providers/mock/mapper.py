from app.application.payments.core.dto.payment_event_dto import (
    PaymentEventDTO,
)


class MockPaymentMapper:

    async def normalize(
        self,
        payload: dict,
    ) -> PaymentEventDTO:

        return PaymentEventDTO(
            provider=payload["provider"],
            external_payment_id=payload[
                "external_payment_id"
            ],
            status=payload["status"],
            tx_hash="mock_tx_hash",
        )
