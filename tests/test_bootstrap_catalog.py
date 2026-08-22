from decimal import Decimal

from sqlalchemy import select

from app.application.catalog.use_cases.bootstrap_catalog import BootstrapCatalogUseCase
from app.infrastructure.database.uow import UnitOfWork
from app.infrastructure.database.session import get_sessionmaker
from app.infrastructure.database.models import (
    Category,
    Subcategory,
    ProductGroup,
    Brand,
    Product,
)


async def test_bootstrap_catalog_creates_full_hierarchy_on_empty_db(clean_db):
    """
    Regression test for known_issues.md: BootstrapCatalogUseCase used to
    hardcode brand_id=1 and crash with a ForeignKeyViolationError on a
    genuinely empty database, since no Brand had ever been created.

    catalog_hierarchy.md: "Brand is REQUIRED for every Product (no
    nullable brand)" and "Every level MUST reference its immediate
    parent only" - this test confirms the use case now creates the full
    Category -> Subcategory -> ProductGroup -> Brand chain itself,
    with each level correctly referencing its parent, before creating
    the seed Product.
    """
    async with UnitOfWork() as uow:
        await BootstrapCatalogUseCase(uow).execute()

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        category = (await session.execute(select(Category))).scalar_one()
        assert category.title == "Электроника"

        subcategory = (await session.execute(select(Subcategory))).scalar_one()
        assert subcategory.category_id == category.id

        product_group = (await session.execute(select(ProductGroup))).scalar_one()
        assert product_group.subcategory_id == subcategory.id

        brand = (await session.execute(select(Brand))).scalar_one()
        assert brand.product_group_id == product_group.id

        product = (await session.execute(select(Product))).scalar_one()
        assert product.brand_id == brand.id
        assert product.price == Decimal("500.00000000")
    finally:
        await session.close()


async def test_bootstrap_catalog_is_a_noop_when_products_already_exist(
    seeded_invoice
):
    """
    BootstrapCatalogUseCase.execute() checks `if products: return` first -
    it must not create a second, duplicate hierarchy when a product
    (and therefore presumably a hierarchy) already exists.
    """
    async with UnitOfWork() as uow:
        await BootstrapCatalogUseCase(uow).execute()

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        categories = (await session.execute(select(Category))).scalars().all()
        assert len(categories) == 1, (
            "BootstrapCatalogUseCase must be a no-op when a product "
            f"already exists, but found {len(categories)} categories "
            "(expected the single one from the seeded_invoice fixture)"
        )
    finally:
        await session.close()
