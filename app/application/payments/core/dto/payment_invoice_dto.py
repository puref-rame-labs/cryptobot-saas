from pydantic import BaseModel


class PaymentInvoiceDTO(BaseModel):

    external_id: str
    payment_url: str

    amount: float
    currency: str
