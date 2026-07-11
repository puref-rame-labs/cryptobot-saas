from enum import Enum


class InvoiceStateError(Exception):
    pass


class InvalidTransition(InvoiceStateError):
    pass


class InvoiceState(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class InvoiceStateMachine:
    """
    Single source of truth for invoice lifecycle transitions.
    """

    _transitions: dict["InvoiceState", set["InvoiceState"]] = {
        InvoiceState.PENDING: {
            InvoiceState.PAID,
            InvoiceState.EXPIRED,
            InvoiceState.FAILED,
        },
        InvoiceState.PAID: {
            InvoiceState.DELIVERED,
            InvoiceState.FAILED,
        },
        InvoiceState.DELIVERED: set(),
        InvoiceState.FAILED: set(),
        InvoiceState.EXPIRED: {InvoiceState.PAID},
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        try:
            c = InvoiceState(current)
            t = InvoiceState(target)
        except ValueError:
            return False

        return t in cls._transitions.get(c, set())

    @classmethod
    def transition(cls, current: str, target: str) -> str:
        if not cls.can_transition(current, target):
            raise InvalidTransition(f"{current} -> {target}")

        return InvoiceState(target).value

    @classmethod
    def mark_paid(cls, current: str) -> str:
        return cls.transition(current, InvoiceState.PAID.value)

    @classmethod
    def mark_delivered(cls, current: str) -> str:
        return cls.transition(current, InvoiceState.DELIVERED.value)

    @classmethod
    def mark_failed(cls, current: str) -> str:
        return cls.transition(current, InvoiceState.FAILED.value)

    @classmethod
    def mark_expired(cls, current: str) -> str:
        return cls.transition(current, InvoiceState.EXPIRED.value)
