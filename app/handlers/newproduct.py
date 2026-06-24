from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.product_state import ProductStates
from app.utils.access import is_admin

from app.infrastructure.database.uow import UnitOfWork
from app.services.product_service import ProductService

router = Router()


@router.message(Command("newproduct"))
async def newproduct_command(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        await message.answer("Access denied")
        return

    await state.set_state(ProductStates.waiting_for_title)
    await message.answer("Send product title")


@router.message(ProductStates.waiting_for_title)
async def product_title_handler(message: Message, state: FSMContext):

    await state.update_data(title=message.text)
    await state.set_state(ProductStates.waiting_for_description)

    await message.answer("Send description")


@router.message(ProductStates.waiting_for_description)
async def product_description_handler(message: Message, state: FSMContext):

    await state.update_data(description=message.text)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer("Send price")


@router.message(ProductStates.waiting_for_price)
async def product_price_handler(message: Message, state: FSMContext):

    try:
        price = Decimal(message.text)
    except Exception:
        await message.answer("Invalid price")
        return

    await state.update_data(price=str(price))
    await state.set_state(ProductStates.waiting_for_currency)

    await message.answer("Send currency")


@router.message(ProductStates.waiting_for_currency)
async def product_currency_handler(message: Message, state: FSMContext):

    await state.update_data(currency=message.text.upper())
    await state.set_state(ProductStates.waiting_for_file)

    await message.answer("Send product file or image")


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
        await message.answer("Send document or photo")
        return

    data = await state.get_data()

    async with UnitOfWork() as uow:

        product_service = ProductService(uow)

        product = await product_service.create_product(
            title=data["title"],
            description=data["description"],
            price=Decimal(data["price"]),
            currency=data["currency"],
        )

        # FIX: attachment теперь через service/use-case слой
        await product_service.attach_file(
            product_id=product.id,
            file_id=file_id,
            file_type=file_type,
        )

    await state.clear()

    await message.answer(
        f"Product created\n"
        f"ID: {product.id}\n"
        f"Title: {product.title}\n"
        f"Price: {product.price} {product.currency}"
    )
