from app.domain.catalog.catalog_item import CatalogItem
from app.domain.catalog.catalog_policy import CatalogPolicy


class CatalogFilter:

    @staticmethod
    def get_visible(items: list[CatalogItem]) -> list[CatalogItem]:
        return [
            item for item in items
            if CatalogPolicy.is_visible(item.status)
        ]

    @staticmethod
    def get_purchasable(items: list[CatalogItem]) -> list[CatalogItem]:
        return [
            item for item in items
            if CatalogPolicy.is_purchasable(item.status)
        ]
