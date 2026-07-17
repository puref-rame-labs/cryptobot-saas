from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    BOT_TOKEN: str

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/database.db"

    ADMIN_IDS: list[int] = Field(default_factory=list)

    WEBHOOK_SECRET: str

    CRYPTOBOT_MAINNET_TOKEN: str = ""
    CRYPTOBOT_MAINNET_HOST: str = "pay.crypt.bot"

    CRYPTOBOT_TESTNET_TOKEN: str = ""
    CRYPTOBOT_TESTNET_HOST: str = "testnet-pay.crypt.bot"

    DEFAULT_PAYMENT_PROVIDER: str = "mock"

    CRYPTOBOT_PROXY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
