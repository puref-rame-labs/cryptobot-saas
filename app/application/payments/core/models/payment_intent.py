# app/services/payments/core/models/payment_intent.py

from dataclasses import dataclass


@dataclass
class PaymentIntent:
    invoice_id: int
    provider: str
    amount: float
