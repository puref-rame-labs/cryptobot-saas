from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProductGroup, Brand


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

    async def create(self, subcategory_id: int, title: str) -> ProductGroup:
        product_group = ProductGroup(subcategory_id=subcategory_id, title=title)
        self.session.add(product_group)
        await self.session.flush()
        return product_group

    async def count_brands(self, product_group_id: int) -> int:
        stmt = select(func.count()).select_from(Brand).where(
            Brand.product_group_id == product_group_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, product_group_id: int) -> None:
        product_group = await self.get_by_id(product_group_id)
        await self.session.delete(product_group)
