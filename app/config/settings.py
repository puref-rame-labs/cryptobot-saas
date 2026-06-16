from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]  # cryptobot/

class Settings(BaseSettings):

    BOT_TOKEN: str

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/database.db"

    ADMIN_IDS: list[int] = Field(default_factory=list)

    WEBHOOK_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
