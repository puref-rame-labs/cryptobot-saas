from app.domain.product.state_machine import ProductState


class ProductPolicy:
    @staticmethod
    def is_visible(status: str) -> bool:
        return status == ProductState.PUBLISHED.value

    @staticmethod
    def can_be_purchased(status: str) -> bool:
        return status == ProductState.PUBLISHED.value
