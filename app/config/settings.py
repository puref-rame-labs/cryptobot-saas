from pathlib import Path
from decimal import Decimal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    BOT_TOKEN: str

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/database.db"

    TEST_DATABASE_URL: str = ""

    DB_ECHO: bool = False

    ADMIN_IDS: list[int] = Field(default_factory=list)

    WEBHOOK_SECRET: str

    CRYPTOBOT_MAINNET_TOKEN: str = ""
    CRYPTOBOT_MAINNET_HOST: str = "pay.crypt.bot"

    CRYPTOBOT_TESTNET_TOKEN: str = ""
    CRYPTOBOT_TESTNET_HOST: str = "testnet-pay.crypt.bot"

    DEFAULT_PAYMENT_PROVIDER: str = "mock"

    REFERRAL_PERCENT: Decimal = Decimal("10.00")

    CRYPTOBOT_PROXY: str | None = None

    BTCPAY_MAINNET_HOST: str = ""
    BTCPAY_MAINNET_API_KEY: str = ""
    BTCPAY_MAINNET_STORE_ID: str = ""
    BTCPAY_MAINNET_WEBHOOK_SECRET: str = ""

    BTCPAY_TESTNET_HOST: str = ""
    BTCPAY_TESTNET_API_KEY: str = ""
    BTCPAY_TESTNET_STORE_ID: str = ""
    BTCPAY_TESTNET_WEBHOOK_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
