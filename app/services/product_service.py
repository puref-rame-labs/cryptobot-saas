from decimal import Decimal

from app.infrastructure.database.models import (
    Product,
)


class ProductService:

    def __init__(self, uow):
        self.uow = uow

    async def bootstrap_products(self):

        products = await (
            self.uow.products.get_all_active()
        )

        if products:
            return

        await self.uow.products.create_product(
            title="Test Product",
            description="Development product",
            price=Decimal("5"),
            currency="USDT",
        )

    async def create_product(
        self,
        title: str,
        description: str | None,
        price: Decimal,
        currency: str = "USDT",
    ):

        product = await (
            self.uow.products.create_product(
                title=title,
                description=description,
                price=price,
                currency=currency,
            )
        )

        return product

    async def attach_file(
        self,
        product,
        file_id: str,
        file_type: str,
    ):

        return await (
            self.uow.products.attach_file(
                product=product,
                file_id=file_id,
                file_type=file_type,
            )
        )
    async def get_product(
        self,
        product_id: int,
    ):
    
        return await (
            self.uow.products.get_by_id(
                product_id
            )
        )
