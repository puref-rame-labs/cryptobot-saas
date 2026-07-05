# app/services/payments/core/registry/provider_registry.py

from app.application.payments.providers.crypto.provider import (
    CryptoProvider,
)

PROVIDERS = {
    "crypto": CryptoProvider(),
    "mock": CryptoProvider(),
}


def get_provider(name: str):

    provider = PROVIDERS.get(name)

    if not provider:
        raise ValueError(f"Unknown payment provider: {name}")

    return provider
