from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Product


class ProductRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self):

        stmt = select(Product).where(
            Product.is_active == True
        )

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def create_product(
        self,
        title: str,
        description: str | None,
        price,
        currency: str = "USDT",
    ):

        product = Product(
            title=title,
            description=description,
            price=price,
            currency=currency,
        )

        self.session.add(product)

        return product
