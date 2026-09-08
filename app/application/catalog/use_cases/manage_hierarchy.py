class HierarchyNodeNotEmptyError(Exception):
    """
    catalog_hierarchy.md: "Deleting a parent node MUST NOT
    cascade-delete Products silently — requires explicit
    reassignment or archive step." Resolved as: block deletion,
    surface what's blocking (variant 1, decided 2026-09-08).
    """

    def __init__(self, child_count: int, child_label: str):
        self.child_count = child_count
        self.child_label = child_label
        super().__init__(
            f"Нельзя удалить: внутри {child_count} {child_label}"
        )


class CreateCategoryUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, title: str):
        return await self.uow.categories.create(title)


class DeleteCategoryUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, category_id: int):
        count = await self.uow.categories.count_subcategories(category_id)
        if count > 0:
            raise HierarchyNodeNotEmptyError(count, "подкатегорий")
        await self.uow.categories.delete(category_id)


class CreateSubcategoryUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, category_id: int, title: str):
        return await self.uow.subcategories.create(category_id, title)


class DeleteSubcategoryUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, subcategory_id: int):
        count = await self.uow.subcategories.count_product_groups(subcategory_id)
        if count > 0:
            raise HierarchyNodeNotEmptyError(count, "групп товаров")
        await self.uow.subcategories.delete(subcategory_id)


class CreateProductGroupUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, subcategory_id: int, title: str):
        return await self.uow.product_groups.create(subcategory_id, title)


class DeleteProductGroupUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_group_id: int):
        count = await self.uow.product_groups.count_brands(product_group_id)
        if count > 0:
            raise HierarchyNodeNotEmptyError(count, "брендов")
        await self.uow.product_groups.delete(product_group_id)


class CreateBrandUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_group_id: int, title: str):
        return await self.uow.brands.create(product_group_id, title)


class DeleteBrandUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, brand_id: int):
        count = await self.uow.brands.count_products(brand_id)
        if count > 0:
            raise HierarchyNodeNotEmptyError(count, "товаров")
        await self.uow.brands.delete(brand_id)
