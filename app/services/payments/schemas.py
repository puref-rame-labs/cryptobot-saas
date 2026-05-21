from dataclasses import dataclass


@dataclass
class PaymentInvoice:

    payment_url: str
    external_id: str
