from app.application.payments.providers.mock.provider import (
    MockPaymentProvider,
)
from app.application.payments.providers.cryptobot.provider import (
    CryptoBotProvider,
)
from app.application.payments.providers.btcpay.provider import (
    BTCPayProvider,
)

PROVIDERS = {
    "mock": MockPaymentProvider,
    "cryptobot": CryptoBotProvider,
    "btcpay": BTCPayProvider,
}
