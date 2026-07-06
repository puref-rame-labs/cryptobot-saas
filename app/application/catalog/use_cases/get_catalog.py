from app.domain.catalog.catalog_filter import CatalogFilter
from app.domain.catalog.catalog_item import CatalogItem


class GetCatalogUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self) -> list[CatalogItem]:
        products = await self.uow.products.get_all_active()

        items = [
            CatalogItem(
                id=p.id,
                title=p.title,
                description=p.description,
                price=p.price,
                currency=p.currency,
                status=p.status,
            )
            for p in products
        ]

        return CatalogFilter.get_purchasable(items)
