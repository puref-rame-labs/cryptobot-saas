from typing import Optional

from pydantic import BaseModel


class PaymentEventDTO(BaseModel):
    external_payment_id: str
    status: str

    tx_hash: Optional[str] = None
    invoice_id: Optional[int] = None
    provider: Optional[str] = None
