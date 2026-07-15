from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

HELP_TEXT = (
    "💰 <b>Как пополнить баланс для оплаты</b>\n\n"
    "Оплата товаров проходит через встроенный кошелёк CryptoBot. "
    "Чтобы купить товар, на балансе должна быть крипта (например, USDT или TON).\n\n"
    "<b>Способы пополнить:</b>\n"
    "1. Откройте @CryptoBot → раздел <b>Купить крипту</b> — можно купить картой напрямую в боте.\n"
    "2. Переведите крипту с биржи (Binance, Bybit и т.п.) на адрес своего CryptoBot-кошелька "
    "(в @CryptoBot: <b>Кошелёк</b> → <b>Пополнить</b>).\n"
    "3. Если у вас уже есть баланс в CryptoBot у другого пользователя — попросите перевод, "
    "он придёт мгновенно и без комиссии.\n\n"
    "После пополнения возвращайтесь сюда и нажимайте /buy — оплата пройдёт по выданной ссылке."
)


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")
