# app/services/payments/providers/crypto/provider.py

from app.application.payments.providers.base import (
    BasePaymentProvider,
)

from app.application.payments.core.dto.payment_event_dto import (
    PaymentEventDTO,
)


class CryptoProvider(BasePaymentProvider):

    async def verify_signature(
        self,
        headers: dict,
        payload: dict,
    ) -> bool:

        # temporary mock validation
        return True

    async def normalize(
        self,
        payload: dict,
    ) -> PaymentEventDTO:

        return PaymentEventDTO(
            invoice_id=int(payload["external_payment_id"]),
            provider=payload["provider"],
            external_payment_id=payload[
                "external_payment_id"
            ],
            tx_hash=payload.get("tx_hash"),
            status=payload["status"],
        )
