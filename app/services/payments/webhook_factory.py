from app.services.payments.provider_registry import (
    WEBHOOK_ADAPTERS,
)


def get_webhook_adapter(
    provider: str,
):

    adapter_class = (
        WEBHOOK_ADAPTERS.get(provider)
    )

    if not adapter_class:

        raise ValueError(
            f"Unknown provider: {provider}"
        )

    return adapter_class()
