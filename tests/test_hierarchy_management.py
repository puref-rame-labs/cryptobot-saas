import pytest

from app.infrastructure.database.uow import UnitOfWork
from app.application.catalog.use_cases.manage_hierarchy import (
    CreateCategoryUseCase,
    CreateSubcategoryUseCase,
    DeleteCategoryUseCase,
    HierarchyNodeNotEmptyError,
)


@pytest.mark.asyncio
async def test_delete_category_blocked_when_subcategory_exists():
    async with UnitOfWork() as uow:
        category = await CreateCategoryUseCase(uow).execute("Тест-Категория")
        await CreateSubcategoryUseCase(uow).execute(category.id, "Тест-Подкатегория")

    async with UnitOfWork() as uow:
        with pytest.raises(HierarchyNodeNotEmptyError) as exc_info:
            await DeleteCategoryUseCase(uow).execute(category.id)

        assert exc_info.value.child_count == 1


@pytest.mark.asyncio
async def test_delete_category_succeeds_when_empty():
    async with UnitOfWork() as uow:
        category = await CreateCategoryUseCase(uow).execute("Пустая категория")

    async with UnitOfWork() as uow:
        await DeleteCategoryUseCase(uow).execute(category.id)
        deleted = await uow.categories.get_by_id(category.id)
        assert deleted is None
