from app.domain.product.state_machine import ProductState


class ProductPolicy:
    @staticmethod
    def can_be_purchased(status: str) -> bool:
        return status == ProductState.PUBLISHED.value
