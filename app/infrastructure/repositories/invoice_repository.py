from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Invoice


class InvoiceRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_invoice(self, invoice: Invoice):

        self.session.add(invoice)

        return invoice

    async def get_by_id(self, invoice_id: int):

        stmt = select(Invoice).where(
            Invoice.id == invoice_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
