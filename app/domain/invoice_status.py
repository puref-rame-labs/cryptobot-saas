from enum import Enum


class InvoiceStatus(str, Enum):

    PENDING = "PENDING"

    PAID = "PAID"

    EXPIRED = "EXPIRED"

    DELIVERED = "DELIVERED"

    FAILED = "FAILED"
