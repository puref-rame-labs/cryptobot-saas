from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _with_back(buttons, back_callback):
    if back_callback:
        buttons.append([
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=back_callback,
            )
        ])
    return buttons


def categories_kb(categories, back_callback=None):
    buttons = [
        [InlineKeyboardButton(
            text=c.title,
            callback_data=f"category:{c.id}",
        )]
        for c in categories
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=_with_back(buttons, back_callback)
    )


def subcategories_kb(subcategories, back_callback=None):
    buttons = [
        [InlineKeyboardButton(
            text=s.title,
            callback_data=f"subcategory:{s.id}",
        )]
        for s in subcategories
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=_with_back(buttons, back_callback)
    )


def product_groups_kb(product_groups, back_callback=None):
    buttons = [
        [InlineKeyboardButton(
            text=pg.title,
            callback_data=f"product_group:{pg.id}",
        )]
        for pg in product_groups
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=_with_back(buttons, back_callback)
    )


def brands_kb(brands, back_callback=None):
    buttons = [
        [InlineKeyboardButton(
            text=b.title,
            callback_data=f"brand:{b.id}",
        )]
        for b in brands
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=_with_back(buttons, back_callback)
    )
