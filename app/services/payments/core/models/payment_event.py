# app/services/payments/core/models/payment_event.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentEvent:
    invoice_id: int
    provider: str
    external_payment_id: str
    tx_hash: Optional[str]
    status: str
