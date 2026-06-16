from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_engine

from app.infrastructure.database import models


async def init_db():
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
