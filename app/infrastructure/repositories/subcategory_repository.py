from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Subcategory


class SubcategoryRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_category(self, category_id: int):
        stmt = select(Subcategory).where(
            Subcategory.category_id == category_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, subcategory_id: int):
        stmt = select(Subcategory).where(
            Subcategory.id == subcategory_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
