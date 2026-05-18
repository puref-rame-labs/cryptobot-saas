from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    BOT_TOKEN: str

    DATABASE_URL: str

    ADMIN_IDS: list[int] = Field(
        default_factory=list
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
