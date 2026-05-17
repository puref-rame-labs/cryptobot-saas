from app.infrastructure.database.base import Base
from app.infrastructure.database.session import engine

# импорт моделей ОБЯЗАТЕЛЕН
from app.infrastructure.database import models


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
