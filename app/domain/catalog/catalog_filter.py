from app.domain.catalog.catalog_item import CatalogItem
from app.domain.product.policy import ProductPolicy


class CatalogFilter:

    @staticmethod
    def get_visible(items: list[CatalogItem]) -> list[CatalogItem]:
        return [
            item for item in items
            if ProductPolicy.is_visible(item.status)
        ]

    @staticmethod
    def get_purchasable(items: list[CatalogItem]) -> list[CatalogItem]:
        return [
            item for item in items
            if ProductPolicy.can_be_purchased(item.status)
        ]
