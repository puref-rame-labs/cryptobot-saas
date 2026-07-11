from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    Invoice,
)


class InvoiceRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_invoice(
        self,
        invoice: Invoice,
    ):

        self.session.add(invoice)

        await self.session.flush()

        return invoice

    async def get_by_id(
        self,
        invoice_id: int,
    ):

        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.user),
                selectinload(Invoice.product),
            )
            .where(
                Invoice.id == invoice_id
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_external_payment_id(
        self,
        external_payment_id: str,
    ):

        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.user),
                selectinload(Invoice.product),
            )
            .where(
                Invoice.external_payment_id
                == external_payment_id
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_active_by_user_and_product(
        self,
        user_id: int,
        product_id: int,
    ):

        stmt = (
            select(Invoice)
            .where(
                Invoice.user_id == user_id,
                Invoice.product_id == product_id,
                Invoice.status == "PENDING",
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
