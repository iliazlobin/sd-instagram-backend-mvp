"""Application configuration via pydantic-settings — env-driven, typed, with safe defaults."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://instagram:instagram@localhost:5432/instagram"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Media — relative to CWD (the workspace root) or absolute path
    media_dir: str = "media"
    max_upload_bytes: int = 10_485_760  # 10 MB

    # Feed
    feed_default_limit: int = 20
    feed_max_limit: int = 100
    feed_backfill_count: int = 20

    # Search
    search_default_limit: int = 20
    search_max_limit: int = 100


settings = Settings()
