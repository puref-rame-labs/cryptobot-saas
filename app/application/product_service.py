from decimal import Decimal


class ProductService:

    def __init__(self, uow):
        self.uow = uow

    async def get_product(self, product_id: int):
        return await self.uow.products.get_by_id(product_id)

    async def create_product(
        self,
        title: str,
        description: str | None,
        price: Decimal,
        brand_id: int,
        currency: str = "USDT",
    ):
        return await self.uow.products.create_product(
            title=title,
            description=description,
            price=price,
            brand_id=brand_id,
            currency=currency,
        )
