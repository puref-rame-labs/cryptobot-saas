from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def products_kb(products):
    buttons = []

    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p.title} — {p.price} {p.currency}",
                callback_data=f"product:{p.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
