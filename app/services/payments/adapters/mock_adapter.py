from app.config.settings import settings

from app.services.payments.webhook_adapter import (
    BaseWebhookAdapter,
)

from app.services.payments.webhook_schema import (
    NormalizedWebhook,
)


class MockWebhookAdapter(
    BaseWebhookAdapter
):

    async def verify_signature(
        self,
        headers,
        payload: dict,
    ) -> bool:

        secret = headers.get(
            "x-webhook-secret"
        )

        return (
            secret
            == settings.WEBHOOK_SECRET
        )

    async def normalize(
        self,
        payload: dict,
    ) -> NormalizedWebhook:

        return NormalizedWebhook(
            external_payment_id=(
                payload[
                    "external_payment_id"
                ]
            ),
            status=payload["status"],
            tx_hash="mock_tx_hash",
        )
