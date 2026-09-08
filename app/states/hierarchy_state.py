from aiogram.fsm.state import State, StatesGroup


class HierarchyCreateStates(StatesGroup):
    waiting_for_level = State()
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_product_group = State()
    waiting_for_title = State()
