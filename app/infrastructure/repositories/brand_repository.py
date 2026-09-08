from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Brand, Product


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

    async def create(self, product_group_id: int, title: str) -> Brand:
        brand = Brand(product_group_id=product_group_id, title=title)
        self.session.add(brand)
        await self.session.flush()
        return brand

    async def count_products(self, brand_id: int) -> int:
        stmt = select(func.count()).select_from(Product).where(
            Product.brand_id == brand_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, brand_id: int) -> None:
        brand = await self.get_by_id(brand_id)
        await self.session.delete(brand)
