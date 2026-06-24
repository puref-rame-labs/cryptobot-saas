from decimal import Decimal


class ProductService:

    def __init__(self, uow):
        self.uow = uow

    async def bootstrap_products(self):

        products = await self.uow.products.get_all_active()

        if products:
            return

        await self.uow.products.create_product(
            title="Test Product",
            description="Development product",
            price=Decimal("5"),
            currency="USDT",
        )

    async def get_catalog(self):

        return await self.uow.products.get_all_active()

    async def get_product(self, product_id: int):

        return await self.uow.products.get_by_id(product_id)

    async def create_product(
        self,
        title: str,
        description: str | None,
        price: Decimal,
        currency: str = "USDT",
    ):

        return await self.uow.products.create_product(
            title=title,
            description=description,
            price=price,
            currency=currency,
        )
