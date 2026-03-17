from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # App
    app_env: Environment = Environment.DEVELOPMENT
    app_secret_key: str
    app_debug: bool = False
    app_port: int = 8000

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # MeiliSearch
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: str | None = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


settings = Settings()
