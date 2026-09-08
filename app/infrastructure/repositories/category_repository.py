from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Category, Subcategory


class CategoryRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self):
        stmt = select(Category)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, category_id: int):
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, title: str) -> Category:
        category = Category(title=title)
        self.session.add(category)
        await self.session.flush()
        return category

    async def count_subcategories(self, category_id: int) -> int:
        stmt = select(func.count()).select_from(Subcategory).where(
            Subcategory.category_id == category_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, category_id: int) -> None:
        category = await self.get_by_id(category_id)
        await self.session.delete(category)
