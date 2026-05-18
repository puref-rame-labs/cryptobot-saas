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

    async def get_by_id(
        self,
        product_id: int,
    ):

        stmt = select(Product).where(
            Product.id == product_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

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

    async def attach_file(
        self,
        product,
        file_id: str,
        file_type: str,
    ):

        product.telegram_file_id = file_id

        product.file_type = file_type

        await self.session.flush()

        return product
