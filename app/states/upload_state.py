from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class UploadStates(StatesGroup):

    waiting_for_product_id = State()

    waiting_for_file = State()
