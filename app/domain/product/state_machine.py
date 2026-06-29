from enum import Enum


class ProductStateError(Exception):
    pass


class InvalidProductTransition(ProductStateError):
    pass


class ProductState(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"


class ProductStateMachine:
    """
    Single source of truth for product state transitions.
    """

    _transitions: dict[ProductState, set[ProductState]] = {
        ProductState.DRAFT: {ProductState.READY},
        ProductState.READY: {ProductState.PUBLISHED},
        ProductState.PUBLISHED: set(),
    }

    @classmethod
    def normalize(cls, value: str) -> ProductState:
        try:
            return ProductState(value)
        except ValueError:
            raise ProductStateError(f"Unknown state: {value}")

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        try:
            c = ProductState(current)
            t = ProductState(target)
        except ValueError:
            return False

        return t in cls._transitions.get(c, set())

    @classmethod
    def transition(cls, current: str, target: str) -> str:
        if current == target:
            return current

        if not cls.can_transition(current, target):
            raise InvalidProductTransition(f"{current} -> {target}")

        return ProductState(target).value

    @classmethod
    def mark_ready(cls, current: str) -> str:
        return cls.transition(current, ProductState.READY.value)

    @classmethod
    def mark_published(cls, current: str) -> str:
        return cls.transition(current, ProductState.PUBLISHED.value)

    @classmethod
    def can_attach(cls, current: str) -> bool:
        try:
            c = ProductState(current)
        except ValueError:
            return False
    
            # attach разрешён только до публикации
        return c in {
            ProductState.DRAFT,
            ProductState.READY,
        }
