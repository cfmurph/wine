from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Wine App API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wineapp"

    # Auth / JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # External API keys
    WINE_SEARCHER_API_KEY: str = ""
    WINE_SEARCHER_BASE_URL: str = "https://api.wine-searcher.com/v1"

    GLOBAL_WINE_SCORE_API_KEY: str = ""
    GLOBAL_WINE_SCORE_BASE_URL: str = "https://api.globalwinescore.com"

    SPOONACULAR_API_KEY: str = ""
    SPOONACULAR_BASE_URL: str = "https://api.spoonacular.com"



@lru_cache()
def get_settings() -> Settings:
    return Settings()
