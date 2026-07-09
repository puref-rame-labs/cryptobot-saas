from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Brand


class BrandRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_product_group(self, product_group_id: int):
        stmt = select(Brand).where(
            Brand.product_group_id == product_group_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, brand_id: int):
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
