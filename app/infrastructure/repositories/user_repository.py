from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> User | None:

        stmt = select(User).where(
            User.telegram_id == telegram_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_referral_code(
        self,
        referral_code: str,
    ) -> User | None:

        stmt = select(User).where(
            User.referral_code == referral_code
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        username: str | None,
        referral_code: str | None = None,
        referred_by_id: int | None = None,
    ) -> User:

        user = User(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            referred_by_id=referred_by_id,
        )

        self.session.add(user)

        await self.session.flush()

        #await self.session.commit()

        return user
