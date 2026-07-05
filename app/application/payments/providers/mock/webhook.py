from app.config.settings import settings


class MockWebhookHandler:

    async def verify_signature(
        self,
        headers: dict,
        payload: dict,
    ) -> bool:

        received_secret = headers.get(
            "x-webhook-secret"
        )

        return (
            received_secret
            == settings.WEBHOOK_SECRET
        )
