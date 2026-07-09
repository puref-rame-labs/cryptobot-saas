from decimal import Decimal


class BootstrapCatalogUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self):
        products = await self.uow.products.get_all_active()

        if products:
            return

        await self.uow.products.create_product(
            title="Test Product",
            description="Development product",
            price=Decimal("5"),
            currency="USDT",
            brand_id=1,
        )
