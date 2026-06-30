from app.domain.product.state_machine import ProductState


class ProductPolicy:
    @staticmethod
    def can_be_purchased(status: str) -> bool:
        # READY = товар с файлом, доступен к продаже
        # PUBLISHED = активный публичный товар
        return status in {
            ProductState.READY.value,
            ProductState.PUBLISHED.value,
        }
