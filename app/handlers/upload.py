from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.infrastructure.database.uow import UnitOfWork
from app.states.upload_state import UploadStates
from app.utils.access import is_admin

from app.application.product.use_cases.attach_file import AttachProductFileUseCase


router = Router()


@router.message(Command("upload"))
async def upload_command(message: Message):

    if not is_admin(message.from_user.id):
        await message.answer("Access denied")
        return

    await message.answer("Send image or file")


@router.message(UploadStates.waiting_for_file)
async def file_receiver(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await message.answer("Product ID missing")
        await state.clear()
        return

    file_id = None
    file_type = None

    if message.document:
        file_id = message.document.file_id
        file_type = "document"

    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    else:
        await message.answer("Send image or document")
        return

    async with UnitOfWork() as uow:

        product = await uow.products.get_by_id(product_id)

        if not product:
            await message.answer("Product not found")
            await state.clear()
            return

        # -------------------------
        # USE CASE LAYER (correct architecture)
        # -------------------------
        use_case = AttachProductFileUseCase(uow)

        await use_case.execute(
            product_id=product.id,
            file_id=file_id,
            file_type=file_type,
        )

    await state.clear()

    await message.answer(f"File attached to product #{product.id}")
