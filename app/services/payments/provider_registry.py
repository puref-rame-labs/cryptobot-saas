from app.services.payments.adapters.mock_adapter import (
    MockWebhookAdapter,
)


WEBHOOK_ADAPTERS = {
    "mock": MockWebhookAdapter,
}
