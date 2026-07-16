from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config.settings import settings
from app.states.upload_state import UploadStates
from app.infrastructure.database.uow import UnitOfWork
from app.application.product.use_cases.attach_file import AttachProductFileUseCase

router = Router()


# -------------------------
# INIT ATTACH FLOW
# -------------------------
@router.message(Command("attach"))
async def attach_command(message: Message, state: FSMContext):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Доступ запрещён")
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer("Использование: /attach <product_id>")
        return

    product_id = int(parts[1])

    await state.update_data(product_id=product_id)
    await state.set_state(UploadStates.waiting_for_file)

    await message.answer("Отправьте файл для товара")


# -------------------------
# FILE RECEIVER
# -------------------------
@router.message(UploadStates.waiting_for_file)
async def handle_file_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await message.answer("Не найден контекст товара")
        return

    file_id = None
    file_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    elif message.document:
        file_id = message.document.file_id
        file_type = "document"

    else:
        await message.answer("Неподдерживаемый тип файла")
        return

    async with UnitOfWork() as uow:
        
        result = await AttachProductFileUseCase(uow).execute(
            product_id=product_id,
            file_id=file_id,
            file_type=file_type,
        )

        if result["status"] != "ok":
            await message.answer(f"Ошибка прикрепления: {result.get('reason', 'unknown')}")
            return

        await uow.session.flush()

    await state.clear()

    product = result["product"]

    await message.answer(
        f"Файл прикреплён к товару\n"
        f"ID: {product.id}\n"
        f"Статус: {product.status}"
    )
