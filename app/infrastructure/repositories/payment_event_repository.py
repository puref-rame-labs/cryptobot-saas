from app.infrastructure.database.models import (
    PaymentEvent,
)


class PaymentEventRepository:

    def __init__(self, session):

        self.session = session

    async def create_event(
        self,
        event: PaymentEvent,
    ):

        self.session.add(event)

        await self.session.flush()

        return event
