from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def products_kb(products, back_callback=None):
    buttons = []

    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p.title} — {p.price} {p.currency}",
                callback_data=f"product:{p.id}"
            )
        ])

    if back_callback:
        buttons.append([
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=back_callback,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
