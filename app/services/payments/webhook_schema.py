from dataclasses import dataclass


@dataclass
class NormalizedWebhook:

    external_payment_id: str
    status: str
    tx_hash: str | None = None
