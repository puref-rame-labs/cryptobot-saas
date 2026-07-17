from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.infrastructure.database.uow import UnitOfWork
from app.application.catalog.use_cases.get_catalog_nodes import (
    GetCategoriesUseCase,
    GetSubcategoriesUseCase,
    GetProductGroupsUseCase,
    GetBrandsUseCase,
)
from app.domain.catalog.catalog_filter import CatalogFilter
from app.domain.catalog.catalog_item import CatalogItem
from app.handlers.keyboards.catalog import (
    categories_kb,
    subcategories_kb,
    product_groups_kb,
    brands_kb,
)
from app.handlers.keyboards.products import products_kb

router = Router()

EMPTY_MESSAGE = "Пока нет доступных товаров в этой категории"


@router.callback_query(F.data.startswith("category:"))
async def select_category(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        subcategories = await GetSubcategoriesUseCase(uow).execute(
            category_id
        )

    if not subcategories:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите подкатегорию:",
        reply_markup=subcategories_kb(
            subcategories,
            back_callback="back_to_categories",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("subcategory:"))
async def select_subcategory(callback: CallbackQuery):
    subcategory_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        product_groups = await GetProductGroupsUseCase(uow).execute(
            subcategory_id
        )
        subcategory = await uow.subcategories.get_by_id(subcategory_id)

    if not product_groups:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите тип товара:",
        reply_markup=product_groups_kb(
            product_groups,
            back_callback=f"back_to_subcategories:{subcategory.category_id}",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_group:"))
async def select_product_group(callback: CallbackQuery):
    product_group_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        brands = await GetBrandsUseCase(uow).execute(product_group_id)
        product_group = await uow.product_groups.get_by_id(
            product_group_id
        )

    if not brands:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=brands_kb(
            brands,
            back_callback=(
                f"back_to_product_groups:{product_group.subcategory_id}"
            ),
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("brand:"))
async def select_brand(callback: CallbackQuery):
    brand_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        raw_products = await uow.products.get_by_brand_id(brand_id)
        brand = await uow.brands.get_by_id(brand_id)

        items = [
            CatalogItem(
                id=p.id,
                title=p.title,
                description=p.description,
                price=p.price,
                currency=p.currency,
                status=p.status,
            )
            for p in raw_products
        ]

        products = CatalogFilter.get_purchasable(items)

    if not products:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите товар:",
        reply_markup=products_kb(
            products,
            back_callback=f"back_to_brands:{brand.product_group_id}",
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_to_start")
async def cancel_to_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "Возврат в начало. Используйте /buy, чтобы посмотреть каталог заново."
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    async with UnitOfWork() as uow:
        categories = await GetCategoriesUseCase(uow).execute()

    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=categories_kb(categories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_subcategories:"))
async def back_to_subcategories(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        subcategories = await GetSubcategoriesUseCase(uow).execute(
            category_id
        )

    await callback.message.edit_text(
        "Выберите подкатегорию:",
        reply_markup=subcategories_kb(
            subcategories,
            back_callback="back_to_categories",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_product_groups:"))
async def back_to_product_groups(callback: CallbackQuery):
    subcategory_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        product_groups = await GetProductGroupsUseCase(uow).execute(
            subcategory_id
        )
        subcategory = await uow.subcategories.get_by_id(subcategory_id)

    await callback.message.edit_text(
        "Выберите тип товара:",
        reply_markup=product_groups_kb(
            product_groups,
            back_callback=f"back_to_subcategories:{subcategory.category_id}",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_brands:"))
async def back_to_brands(callback: CallbackQuery):
    product_group_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        brands = await GetBrandsUseCase(uow).execute(product_group_id)
        product_group = await uow.product_groups.get_by_id(
            product_group_id
        )

    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=brands_kb(
            brands,
            back_callback=(
                f"back_to_product_groups:{product_group.subcategory_id}"
            ),
        ),
    )
    await callback.answer()
