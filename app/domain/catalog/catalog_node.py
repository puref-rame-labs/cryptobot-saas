from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryNode:
    id: int
    title: str


@dataclass(frozen=True)
class SubcategoryNode:
    id: int
    title: str
    category_id: int


@dataclass(frozen=True)
class ProductGroupNode:
    id: int
    title: str
    subcategory_id: int


@dataclass(frozen=True)
class BrandNode:
    id: int
    title: str
    product_group_id: int
