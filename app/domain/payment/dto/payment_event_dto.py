from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PaymentEventDTO(BaseModel):
    external_payment_id: str
    status: str

    tx_hash: Optional[str] = None
    invoice_id: Optional[int] = None
    provider: Optional[str] = None

    paid_asset: Optional[str] = None
    paid_amount: Optional[Decimal] = None
    paid_fiat_rate: Optional[Decimal] = None
