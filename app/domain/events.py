from dataclasses import dataclass

@dataclass
class InvoicePaidEvent:
    invoice_id: int
    external_payment_id: str
    tx_hash: str | None = None
