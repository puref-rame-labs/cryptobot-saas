from app.domain.catalog.catalog_node import (
    CategoryNode,
    SubcategoryNode,
    ProductGroupNode,
    BrandNode,
)


class GetCategoriesUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self) -> list[CategoryNode]:
        categories = await self.uow.categories.get_all()

        return [
            CategoryNode(id=c.id, title=c.title)
            for c in categories
        ]


class GetSubcategoriesUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, category_id: int) -> list[SubcategoryNode]:
        subcategories = await self.uow.subcategories.get_by_category(
            category_id
        )

        return [
            SubcategoryNode(
                id=s.id,
                title=s.title,
                category_id=s.category_id,
            )
            for s in subcategories
        ]


class GetProductGroupsUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(
        self, subcategory_id: int
    ) -> list[ProductGroupNode]:
        product_groups = await self.uow.product_groups.get_by_subcategory(
            subcategory_id
        )

        return [
            ProductGroupNode(
                id=pg.id,
                title=pg.title,
                subcategory_id=pg.subcategory_id,
            )
            for pg in product_groups
        ]


class GetBrandsUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_group_id: int) -> list[BrandNode]:
        brands = await self.uow.brands.get_by_product_group(
            product_group_id
        )

        return [
            BrandNode(
                id=b.id,
                title=b.title,
                product_group_id=b.product_group_id,
            )
            for b in brands
        ]
