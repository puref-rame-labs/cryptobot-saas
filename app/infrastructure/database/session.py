from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config.settings import settings
from pathlib import Path

_engine = None
_async_session = None


def get_engine():
    global _engine

    if _engine is None:
        url = settings.DATABASE_URL

        # ВАЖНО: достаём файл БЕЗ попытки трактовать как directory
        raw = url.replace("sqlite+aiosqlite:///", "")
        db_file = Path(raw)

        print("[DB DEBUG] DB FILE:", db_file)

        # ВАЖНО: создаём директорию файла, а не "data как сущность"
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # используем ОРИГИНАЛЬНЫЙ URL без пересборки
        _engine = create_async_engine(
            url,
            echo=True,
        )

    return _engine


def get_sessionmaker():
    global _async_session

    if _async_session is None:
        _async_session = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _async_session
