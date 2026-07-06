from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CatalogItem:
    id: int
    title: str
    description: str | None
    price: Decimal
    currency: str
    status: str
