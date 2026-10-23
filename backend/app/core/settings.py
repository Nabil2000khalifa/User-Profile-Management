from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = Field(default="local", min_length=1)
    database_url: SecretStr
    session_secret: SecretStr
    frontend_origin: str = Field(default="http://localhost:5173", min_length=1)
    session_ttl_hours: int = Field(default=8, ge=1, le=24 * 7)
    login_max_attempts: int = Field(default=5, ge=1, le=20)
    login_window_seconds: int = Field(default=300, ge=60, le=3600)

    @property
    def secure_cookies(self) -> bool:
        return self.app_env.lower() not in {"local", "test"}

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        url = value.get_secret_value()
        if not url.startswith("mysql+pymysql://"):
            raise ValueError("DATABASE_URL must use the mysql+pymysql scheme")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
