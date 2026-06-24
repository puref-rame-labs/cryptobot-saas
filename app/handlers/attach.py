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
# STEP 1: INIT ATTACH FLOW
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
# STEP 2: FILE RECEIVER → PRODUCT READY
# -------------------------
@router.message(UploadStates.waiting_for_file)
async def handle_file_upload(message: Message, state: FSMContext):

    data = await state.get_data()
    product_id = data.get("product_id")

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

        product = await uow.products.get_by_id(product_id)

        if not product:
            await message.answer("Product not found")
            return

        # -------------------------
        # USE CASE (source of truth)
        # -------------------------
        use_case = AttachProductFileUseCase(uow)

        await use_case.execute(
            product=product,
            file_id=file_id,
            file_type=file_type,
        )

        await uow.session.commit()

    await state.clear()

    await message.answer("Product is now READY")
