from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProductGroup


class ProductGroupRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_subcategory(self, subcategory_id: int):
        stmt = select(ProductGroup).where(
            ProductGroup.subcategory_id == subcategory_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, product_group_id: int):
        stmt = select(ProductGroup).where(
            ProductGroup.id == product_group_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
