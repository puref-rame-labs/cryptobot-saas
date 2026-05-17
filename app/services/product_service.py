from decimal import Decimal


class ProductService:

    def __init__(self, uow):
        self.uow = uow

    async def bootstrap_products(self):

        existing = await (
            self.uow.products.get_all_active()
        )

        if existing:
            return

        await self.uow.products.create_product(
            title="Test Product",
            description="Development product",
            price=Decimal("5.00"),
            currency="USDT",
        )

    async def get_catalog(self):

        return await self.uow.products.get_all_active()
