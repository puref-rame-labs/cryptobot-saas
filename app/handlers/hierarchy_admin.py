from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.config.settings import settings
from app.infrastructure.database.uow import UnitOfWork
from app.states.hierarchy_state import HierarchyCreateStates

from app.application.catalog.use_cases.get_catalog_nodes import (
    GetCategoriesUseCase,
    GetSubcategoriesUseCase,
    GetProductGroupsUseCase,
    GetBrandsUseCase,
)
from app.application.catalog.use_cases.manage_hierarchy import (
    CreateCategoryUseCase,
    CreateSubcategoryUseCase,
    CreateProductGroupUseCase,
    CreateBrandUseCase,
    DeleteCategoryUseCase,
    DeleteSubcategoryUseCase,
    DeleteProductGroupUseCase,
    DeleteBrandUseCase,
    HierarchyNodeNotEmptyError,
)
from app.handlers.keyboards.catalog import (
    hierarchy_level_kb,
    categories_kb,
    subcategories_kb,
    product_groups_kb,
)

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# -------------------------
# CREATE FLOW
# -------------------------

@router.message(Command("addhierarchy"))
async def addhierarchy_command(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("Доступ запрещён")
        return

    await state.set_state(HierarchyCreateStates.waiting_for_level)
    await message.answer(
        "Выберите уровень иерархии для создания:",
        reply_markup=hierarchy_level_kb(),
    )


@router.callback_query(
    HierarchyCreateStates.waiting_for_level,
    F.data.startswith("level:"),
)
async def create_level_selected(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[1]
    await state.update_data(level=level)

    if level == "category":
        await state.set_state(HierarchyCreateStates.waiting_for_title)
        await callback.message.edit_text("Отправьте название новой категории")
        await callback.answer()
        return

    async with UnitOfWork() as uow:
        categories = await GetCategoriesUseCase(uow).execute()

    if not categories:
        await callback.answer(
            "Сначала создайте хотя бы одну категорию", show_alert=True
        )
        return

    await state.set_state(HierarchyCreateStates.waiting_for_category)
    await callback.message.edit_text(
        "Выберите категорию:", reply_markup=categories_kb(categories)
    )
    await callback.answer()


@router.callback_query(
    HierarchyCreateStates.waiting_for_category,
    F.data.startswith("category:"),
)
async def create_category_selected(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    level = data["level"]
    await state.update_data(category_id=category_id)

    if level == "subcategory":
        await state.set_state(HierarchyCreateStates.waiting_for_title)
        await callback.message.edit_text("Отправьте название новой подкатегории")
        await callback.answer()
        return

    async with UnitOfWork() as uow:
        subcategories = await GetSubcategoriesUseCase(uow).execute(category_id)

    if not subcategories:
        await callback.answer(
            "Сначала создайте подкатегорию в этой категории", show_alert=True
        )
        return

    await state.set_state(HierarchyCreateStates.waiting_for_subcategory)
    await callback.message.edit_text(
        "Выберите подкатегорию:", reply_markup=subcategories_kb(subcategories)
    )
    await callback.answer()


@router.callback_query(
    HierarchyCreateStates.waiting_for_subcategory,
    F.data.startswith("subcategory:"),
)
async def create_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    subcategory_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    level = data["level"]
    await state.update_data(subcategory_id=subcategory_id)

    if level == "product_group":
        await state.set_state(HierarchyCreateStates.waiting_for_title)
        await callback.message.edit_text("Отправьте название новой группы товаров")
        await callback.answer()
        return

    async with UnitOfWork() as uow:
        product_groups = await GetProductGroupsUseCase(uow).execute(subcategory_id)

    if not product_groups:
        await callback.answer(
            "Сначала создайте группу товаров в этой подкатегории", show_alert=True
        )
        return

    await state.set_state(HierarchyCreateStates.waiting_for_product_group)
    await callback.message.edit_text(
        "Выберите группу товаров:", reply_markup=product_groups_kb(product_groups)
    )
    await callback.answer()


@router.callback_query(
    HierarchyCreateStates.waiting_for_product_group,
    F.data.startswith("product_group:"),
)
async def create_product_group_selected(callback: CallbackQuery, state: FSMContext):
    product_group_id = int(callback.data.split(":")[1])
    await state.update_data(product_group_id=product_group_id)
    await state.set_state(HierarchyCreateStates.waiting_for_title)
    await callback.message.edit_text("Отправьте название нового бренда")
    await callback.answer()


@router.message(HierarchyCreateStates.waiting_for_title)
async def create_title_received(message: Message, state: FSMContext):
    data = await state.get_data()
    level = data["level"]
    title = message.text.strip()

    if not title:
        await message.answer("Название не может быть пустым")
        return

    async with UnitOfWork() as uow:
        if level == "category":
            node = await CreateCategoryUseCase(uow).execute(title)
        elif level == "subcategory":
            node = await CreateSubcategoryUseCase(uow).execute(
                data["category_id"], title
            )
        elif level == "product_group":
            node = await CreateProductGroupUseCase(uow).execute(
                data["subcategory_id"], title
            )
        else:
            node = await CreateBrandUseCase(uow).execute(
                data["product_group_id"], title
            )

    await state.clear()
    await message.answer(f"Создано: «{node.title}» (id={node.id})")


# -------------------------
# LIST (нужно для получения ID перед удалением)
# -------------------------

@router.message(Command("listhierarchy"))
async def list_hierarchy(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Доступ запрещён")
        return

    lines = []
    async with UnitOfWork() as uow:
        categories = await GetCategoriesUseCase(uow).execute()
        for c in categories:
            lines.append(f"📁 [{c.id}] {c.title}")
            subcategories = await GetSubcategoriesUseCase(uow).execute(c.id)
            for s in subcategories:
                lines.append(f"  📂 [{s.id}] {s.title}")
                product_groups = await GetProductGroupsUseCase(uow).execute(s.id)
                for pg in product_groups:
                    lines.append(f"    📦 [{pg.id}] {pg.title}")
                    brands = await GetBrandsUseCase(uow).execute(pg.id)
                    for b in brands:
                        lines.append(f"      🏷 [{b.id}] {b.title}")

    if not lines:
        await message.answer("Иерархия пуста")
        return

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n...(обрезано)"
    await message.answer(text)


# -------------------------
# DELETE FLOW (прямой ID, как /archive и /publish)
# -------------------------

async def _delete_node(message: Message, command: CommandObject, use_case_cls, label: str):
    if not _is_admin(message.from_user.id):
        await message.answer("Доступ запрещён")
        return

    if not command.args:
        await message.answer(f"Использование: /{label} <id>")
        return

    try:
        node_id = int(command.args)
    except ValueError:
        await message.answer("Некорректный id")
        return

    async with UnitOfWork() as uow:
        try:
            await use_case_cls(uow).execute(node_id)
        except HierarchyNodeNotEmptyError as e:
            await message.answer(str(e))
            return

    await message.answer(f"Удалено (id={node_id})")


@router.message(Command("delcategory"))
async def delete_category(message: Message, command: CommandObject):
    await _delete_node(message, command, DeleteCategoryUseCase, "delcategory")


@router.message(Command("delsubcategory"))
async def delete_subcategory(message: Message, command: CommandObject):
    await _delete_node(message, command, DeleteSubcategoryUseCase, "delsubcategory")


@router.message(Command("delproductgroup"))
async def delete_product_group(message: Message, command: CommandObject):
    await _delete_node(message, command, DeleteProductGroupUseCase, "delproductgroup")


@router.message(Command("delbrand"))
async def delete_brand(message: Message, command: CommandObject):
    await _delete_node(message, command, DeleteBrandUseCase, "delbrand")
