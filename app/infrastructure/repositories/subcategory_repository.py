from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Subcategory, ProductGroup


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

    async def create(self, category_id: int, title: str) -> Subcategory:
        subcategory = Subcategory(category_id=category_id, title=title)
        self.session.add(subcategory)
        await self.session.flush()
        return subcategory

    async def count_product_groups(self, subcategory_id: int) -> int:
        stmt = select(func.count()).select_from(ProductGroup).where(
            ProductGroup.subcategory_id == subcategory_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, subcategory_id: int) -> None:
        subcategory = await self.get_by_id(subcategory_id)
        await self.session.delete(subcategory)
