

class UserService:
    def __init__(self, uow):
        self.uow = uow

    async def register_user(self, telegram_id: int, username: str | None):

        existing = await self.uow.users.get_by_telegram_id(telegram_id)

        if existing:
            return existing

        user = await self.uow.users.create_user(
            telegram_id=telegram_id,
            username=username,
        )

        return user
