from abc import ABC, abstractmethod


class BasePaymentProvider(ABC):

    @abstractmethod
    async def create_invoice(
        self,
        invoice,
    ):
        pass
