from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states.product_state import ProductStates
from app.utils.access import is_admin

from app.infrastructure.database.uow import UnitOfWork
from app.application.product_service import ProductService
from app.application.product.use_cases.attach_file import AttachProductFileUseCase
from app.application.catalog.use_cases.get_catalog_nodes import (
    GetCategoriesUseCase,
    GetSubcategoriesUseCase,
    GetProductGroupsUseCase,
    GetBrandsUseCase,
)
from app.handlers.keyboards.catalog import (
    categories_kb,
    subcategories_kb,
    product_groups_kb,
    brands_kb,
)

router = Router()


@router.message(Command("newproduct"))
async def newproduct_command(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён")
        return

    async with UnitOfWork() as uow:
        categories = await GetCategoriesUseCase(uow).execute()

    if not categories:
        await message.answer(
            "Нет ни одной категории. Сначала создайте иерархию каталога."
        )
        return

    await state.set_state(ProductStates.waiting_for_category)
    await message.answer(
        "Выберите категорию для нового товара:",
        reply_markup=categories_kb(categories),
    )


@router.callback_query(
    ProductStates.waiting_for_category,
    F.data.startswith("category:"),
)
async def newproduct_category_handler(
    callback: CallbackQuery, state: FSMContext
):
    category_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        subcategories = await GetSubcategoriesUseCase(uow).execute(
            category_id
        )

    if not subcategories:
        await callback.answer(
            "В этой категории нет подкатегорий", show_alert=True
        )
        return

    await state.update_data(category_id=category_id)
    await state.set_state(ProductStates.waiting_for_subcategory)

    await callback.message.edit_text(
        "Выберите подкатегорию:",
        reply_markup=subcategories_kb(subcategories),
    )
    await callback.answer()


@router.callback_query(
    ProductStates.waiting_for_subcategory,
    F.data.startswith("subcategory:"),
)
async def newproduct_subcategory_handler(
    callback: CallbackQuery, state: FSMContext
):
    subcategory_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        product_groups = await GetProductGroupsUseCase(uow).execute(
            subcategory_id
        )

    if not product_groups:
        await callback.answer(
            "В этой подкатегории нет групп товаров", show_alert=True
        )
        return

    await state.update_data(subcategory_id=subcategory_id)
    await state.set_state(ProductStates.waiting_for_product_group)

    await callback.message.edit_text(
        "Выберите тип товара:",
        reply_markup=product_groups_kb(product_groups),
    )
    await callback.answer()


@router.callback_query(
    ProductStates.waiting_for_product_group,
    F.data.startswith("product_group:"),
)
async def newproduct_product_group_handler(
    callback: CallbackQuery, state: FSMContext
):
    product_group_id = int(callback.data.split(":")[1])

    async with UnitOfWork() as uow:
        brands = await GetBrandsUseCase(uow).execute(product_group_id)

    if not brands:
        await callback.answer(
            "В этой группе нет брендов", show_alert=True
        )
        return

    await state.update_data(product_group_id=product_group_id)
    await state.set_state(ProductStates.waiting_for_brand)

    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=brands_kb(brands),
    )
    await callback.answer()


@router.callback_query(
    ProductStates.waiting_for_brand,
    F.data.startswith("brand:"),
)
async def newproduct_brand_handler(
    callback: CallbackQuery, state: FSMContext
):
    brand_id = int(callback.data.split(":")[1])

    await state.update_data(brand_id=brand_id)
    await state.set_state(ProductStates.waiting_for_title)

    await callback.message.edit_text("Отправьте название товара")
    await callback.answer()


@router.message(ProductStates.waiting_for_title)
async def product_title_handler(message: Message, state: FSMContext):

    await state.update_data(title=message.text)
    await state.set_state(ProductStates.waiting_for_description)

    await message.answer("Отправьте описание")


@router.message(ProductStates.waiting_for_description)
async def product_description_handler(message: Message, state: FSMContext):

    await state.update_data(description=message.text)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer("Отправьте цену")


@router.message(ProductStates.waiting_for_price)
async def product_price_handler(message: Message, state: FSMContext):

    try:
        price = Decimal(message.text)
    except Exception:
        await message.answer("Некорректная цена")
        return

    await state.update_data(price=str(price))
    await state.set_state(ProductStates.waiting_for_currency)

    await message.answer("Отправьте валюту")


@router.message(ProductStates.waiting_for_currency)
async def product_currency_handler(message: Message, state: FSMContext):

    await state.update_data(currency=message.text.upper())
    await state.set_state(ProductStates.waiting_for_file)

    await message.answer("Отправьте файл или изображение товара")


@router.message(ProductStates.waiting_for_file)
async def product_file_handler(message: Message, state: FSMContext):

    file_id = None
    file_type = None

    if message.document:
        file_id = message.document.file_id
        file_type = "document"

    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    else:
        await message.answer("Отправьте документ или фото")
        return

    data = await state.get_data()

    async with UnitOfWork() as uow:

        product_service = ProductService(uow)

        product = await product_service.create_product(
            title=data["title"],
            description=data["description"],
            price=Decimal(data["price"]),
            currency=data["currency"],
            brand_id=data["brand_id"],
        )

        # ARCHITECTURE FIX: use-case layer only
        await AttachProductFileUseCase(uow).execute(
            product_id=product.id,
            file_id=file_id,
            file_type=file_type,
        )

    await state.clear()

    await message.answer(
        f"Товар создан\n"
        f"ID: {product.id}\n"
        f"Название: {product.title}\n"
        f"Цена: {product.price} {product.currency}"
    )
