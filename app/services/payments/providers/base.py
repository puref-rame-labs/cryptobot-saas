# app/services/payments/providers/base.py

from abc import ABC, abstractmethod

from app.services.payments.core.dto.payment_event_dto import (
    PaymentEventDTO,
)


class BasePaymentProvider(ABC):

    @abstractmethod
    async def create_invoice(self, invoice):
        pass

    @abstractmethod
    async def verify_signature(
        self,
        headers: dict,
        payload: dict,
    ) -> bool:
        pass

    @abstractmethod
    async def normalize(
        self,
        payload: dict,
    ) -> PaymentEventDTO:
        pass
