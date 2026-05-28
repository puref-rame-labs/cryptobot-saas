# app/services/payments/core/dto/payment_event_dto.py

from pydantic import BaseModel
from typing import Optional


class PaymentEventDTO(BaseModel):

    invoice_id: int

    provider: str

    external_payment_id: str

    tx_hash: Optional[str] = None

    status: str
