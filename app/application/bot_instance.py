from aiogram import Bot

bot: Bot | None = None


def get_bot() -> Bot:
    if bot is None:
        raise RuntimeError("Bot is not initialized")
    return bot
