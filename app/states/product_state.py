from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class ProductStates(StatesGroup):

    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_product_group = State()
    waiting_for_brand = State()

    waiting_for_title = State()

    waiting_for_description = State()

    waiting_for_price = State()

    waiting_for_currency = State()

    waiting_for_file = State()
