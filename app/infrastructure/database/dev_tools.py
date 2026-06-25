from app.infrastructure.database.base import Base
from app.infrastructure.database.session import engine


async def reset_database():
    """
    DEV ONLY: полный сброс схемы.
    НИКОГДА не использовать в production.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
