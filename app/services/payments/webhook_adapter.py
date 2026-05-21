from abc import ABC
from abc import abstractmethod

from app.services.payments.webhook_schema import (
    NormalizedWebhook,
)


class BaseWebhookAdapter(ABC):

    @abstractmethod
    async def verify_signature(
        self,
        headers,
        payload: dict,
    ) -> bool:

        raise NotImplementedError

    @abstractmethod
    async def normalize(
        self,
        payload: dict,
    ) -> NormalizedWebhook:

        raise NotImplementedError
