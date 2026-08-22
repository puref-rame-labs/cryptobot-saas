from decimal import Decimal

from app.infrastructure.database.models import (
    Category,
    Subcategory,
    ProductGroup,
    Brand,
)


class BootstrapCatalogUseCase:
    """
    catalog_hierarchy.md: "Brand is REQUIRED for every Product (no
    nullable brand)". This use case seeds a minimal dev/demo catalog
    on an EMPTY database - it must create the full Category ->
    Subcategory -> ProductGroup -> Brand chain itself before creating
    a Product, rather than assuming any hierarchy node already exists.

    known_issues.md: previously hardcoded brand_id=1 and crashed with
    a ForeignKeyViolationError on a genuinely empty database, since no
    Brand had ever been created. Fixed 2026-08-20.
    """

    def __init__(self, uow):
        self.uow = uow

    async def execute(self):
        products = await self.uow.products.get_all_active()

        if products:
            return

        category = Category(title="Электроника")
        self.uow.session.add(category)
        await self.uow.session.flush()

        subcategory = Subcategory(
            title="Планшеты",
            category_id=category.id,
        )
        self.uow.session.add(subcategory)
        await self.uow.session.flush()

        product_group = ProductGroup(
            title="iPad",
            subcategory_id=subcategory.id,
        )
        self.uow.session.add(product_group)
        await self.uow.session.flush()

        brand = Brand(
            title="Apple",
            product_group_id=product_group.id,
        )
        self.uow.session.add(brand)
        await self.uow.session.flush()

        await self.uow.products.create_product(
            title="Test Product",
            description="Development product",
            price=Decimal("500"),
            currency="RUB",
            brand_id=brand.id,
        )
