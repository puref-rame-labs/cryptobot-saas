from app.application.payments.providers.mock.provider import (
    MockPaymentProvider,
)
from app.application.payments.providers.cryptobot.provider import (
    CryptoBotProvider,
)

PROVIDERS = {
    "mock": MockPaymentProvider,
    "cryptobot": CryptoBotProvider,
}
