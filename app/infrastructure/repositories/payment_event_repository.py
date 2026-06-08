from sqlalchemy import select

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

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ):
    
        stmt = select(PaymentEvent).where(
            PaymentEvent.idempotency_key
            == idempotency_key
        )
    
        result = await self.session.execute(stmt)
    
        return result.scalar_one_or_none()
