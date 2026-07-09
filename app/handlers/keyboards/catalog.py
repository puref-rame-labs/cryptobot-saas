from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def categories_kb(categories):
    buttons = [
        [InlineKeyboardButton(
            text=c.title,
            callback_data=f"category:{c.id}",
        )]
        for c in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subcategories_kb(subcategories):
    buttons = [
        [InlineKeyboardButton(
            text=s.title,
            callback_data=f"subcategory:{s.id}",
        )]
        for s in subcategories
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_groups_kb(product_groups):
    buttons = [
        [InlineKeyboardButton(
            text=pg.title,
            callback_data=f"product_group:{pg.id}",
        )]
        for pg in product_groups
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def brands_kb(brands):
    buttons = [
        [InlineKeyboardButton(
            text=b.title,
            callback_data=f"brand:{b.id}",
        )]
        for b in brands
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
