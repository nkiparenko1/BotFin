"""Application configuration."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings."""

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str = "postgresql+asyncpg://botfin:botfin@localhost:5432/botfin"

    @model_validator(mode="after")
    def normalize_database_url(self) -> "Settings":
        """Railway provides postgresql:// — SQLAlchemy async needs postgresql+asyncpg://."""
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 30
    cors_origins: str = "http://localhost:3000"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-chat"
    deepseek_embedding_model: str = "deepseek-embedding"
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:3000/api/auth/callback/google"
    env: str = "development"


settings = Settings()
