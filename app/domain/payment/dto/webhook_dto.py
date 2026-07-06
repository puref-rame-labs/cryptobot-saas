# app/services/payments/core/dto/webhook_dto.py

from pydantic import BaseModel


class WebhookDTO(BaseModel):

    provider: str

    external_payment_id: str

    status: str
