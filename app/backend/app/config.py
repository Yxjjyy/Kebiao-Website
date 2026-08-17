from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ACCESS_TOKEN: str = "dev-token-change-me"
    LOGIN_USERNAME: str = "yang"
    LOGIN_PASSWORD: str = ""
    SESSION_TTL_DAYS: int = 365
    DB_PATH: str = "./data/app.db"
    TIMEZONE: str = "Asia/Shanghai"
    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    MAX_RESTORE_BYTES: int = 100 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        db_path = Path(self.DB_PATH).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
