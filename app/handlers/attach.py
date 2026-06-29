from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config.settings import settings
from app.states.upload_state import UploadStates
from app.infrastructure.database.uow import UnitOfWork
from app.services.product.use_cases.attach_file import AttachProductFileUseCase

router = Router()


# -------------------------
# INIT ATTACH FLOW
# -------------------------
@router.message(Command("attach"))
async def attach_command(message: Message, state: FSMContext):

    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Access denied")
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer("Usage: /attach <product_id>")
        return

    product_id = int(parts[1])

    await state.update_data(product_id=product_id)
    await state.set_state(UploadStates.waiting_for_file)

    await message.answer("Send file for product")


# -------------------------
# FILE RECEIVER
# -------------------------
@router.message(UploadStates.waiting_for_file)
async def handle_file_upload(message: Message, state: FSMContext):
    print("1) FSM HIT attach handler")

    data = await state.get_data()
    product_id = data.get("product_id")
    print("2) FSM DATA:", data)
    print("2) PRODUCT ID:", product_id)

    if not product_id:
        await message.answer("Missing product context")
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
        await message.answer("Unsupported file type")
        return

    async with UnitOfWork() as uow:
        print("3) BEFORE USE CASE")
        print("3) file_id:", file_id)
        print("3) file_type:", file_type)
        
        result = await AttachProductFileUseCase(uow).execute(
            product_id=product_id,
            file_id=file_id,
            file_type=file_type,
        )

        if result["status"] != "ok":
            await message.answer(f"Attach failed: {result.get('reason', 'unknown')}")
            return

        await uow.session.flush()
        print("8) AFTER USE CASE RETURNED")
        print("product_id:", product_id)
        print("final product.status:", product.status)

    await state.clear()

    product = result["product"]

    await message.answer(
        f"Product attached\n"
        f"ID: {product.id}\n"
        f"Status: {product.status}"
    )
