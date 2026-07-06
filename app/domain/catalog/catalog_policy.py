from app.domain.product.state_machine import ProductState


class CatalogPolicy:

    @staticmethod
    def is_visible(status: str) -> bool:
        return status == ProductState.PUBLISHED.value

    @staticmethod
    def is_purchasable(status: str) -> bool:
        return status == ProductState.PUBLISHED.value
