from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET_KEY = "change-me-in-production"
_MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Wine App API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wineapp"

    # Auth / JWT
    SECRET_KEY: str = _DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # External API keys
    WINE_SEARCHER_API_KEY: str = ""
    WINE_SEARCHER_BASE_URL: str = "https://api.wine-searcher.com/v1"

    GLOBAL_WINE_SCORE_API_KEY: str = ""
    GLOBAL_WINE_SCORE_BASE_URL: str = "https://api.globalwinescore.com"

    SPOONACULAR_API_KEY: str = ""
    SPOONACULAR_BASE_URL: str = "https://api.spoonacular.com"


    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_deployed(self) -> bool:
        return self.ENVIRONMENT != "development"

    @model_validator(mode="after")
    def _refuse_unsafe_deployment(self):
        """Fail at startup rather than run a deployed environment with development settings."""
        if not self.is_deployed:
            return self
        problems = []
        if self.SECRET_KEY == _DEV_SECRET_KEY or len(self.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH:
            problems.append(f"SECRET_KEY must be a unique value of at least {_MIN_SECRET_KEY_LENGTH} characters")
        if self.DEBUG:
            problems.append("DEBUG must be false")
        if "localhost:5432" in self.DATABASE_URL or "postgres:postgres@" in self.DATABASE_URL:
            problems.append("DATABASE_URL must not use the development database or password")
        if not self.cors_origin_list or "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS must list the allowed sites")
        if problems:
            raise ValueError(f"Unsafe {self.ENVIRONMENT} settings: " + "; ".join(problems))
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
