from decimal import Decimal

from app.domain.product.policy import ProductPolicy


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

    # RAW catalog (всё активное)
    async def get_catalog(self):
        return await self.uow.products.get_all_active()

    # NEW: только покупаемые товары
    async def get_purchasable_catalog(self):

        products = await self.uow.products.get_all_active()

        return [
            p for p in products
            if ProductPolicy.can_be_purchased(p.status)
        ]

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
