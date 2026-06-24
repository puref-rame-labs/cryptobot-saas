from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Product


class ProductRepository:
    """
    Persistence layer only:
    - no business logic
    - no state transitions
    - no file attachment mutations
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------
    # QUERIES
    # -------------------------

    async def get_all_active(self):
        stmt = select(Product).where(Product.is_active.is_(True))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, product_id: int):
        stmt = select(Product).where(Product.id == product_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # -------------------------
    # CREATE
    # -------------------------

    async def create_product(
        self,
        title: str,
        description: str | None,
        price,
        currency: str = "USDT",
    ) -> Product:

        product = Product(
            title=title,
            description=description,
            price=price,
            currency=currency,
        )

        self.session.add(product)
        await self.session.flush()  # чтобы появился product.id

        return product
