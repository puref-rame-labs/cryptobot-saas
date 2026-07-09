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
        reply_markup=subcategories_kb(subcategories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("subcategory:"))
async def select_subcategory(callback: CallbackQuery):
    subcategory_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        product_groups = await GetProductGroupsUseCase(uow).execute(
            subcategory_id
        )

    if not product_groups:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите тип товара:",
        reply_markup=product_groups_kb(product_groups),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_group:"))
async def select_product_group(callback: CallbackQuery):
    product_group_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        brands = await GetBrandsUseCase(uow).execute(product_group_id)

    if not brands:
        await callback.answer(EMPTY_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=brands_kb(brands),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("brand:"))
async def select_brand(callback: CallbackQuery):
    brand_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        raw_products = await uow.products.get_by_brand_id(brand_id)

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
        reply_markup=products_kb(products),
    )
    await callback.answer()
