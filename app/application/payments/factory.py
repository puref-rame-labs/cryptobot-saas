from app.application.payments.providers.registry import (
    PROVIDERS,
)


def get_payment_provider(
    provider_name: str,
):

    provider_class = PROVIDERS.get(
        provider_name
    )

    if not provider_class:

        raise ValueError(
            f"Unknown provider: {provider_name}"
        )

    return provider_class()
