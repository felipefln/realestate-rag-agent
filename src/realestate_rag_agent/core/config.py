from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    debug: bool = False
    api_title: str = "realestate-rag-agent"
    api_version: str = "0.1.0"

    # Placeholders for later phases (kept optional so /health works with no config).
    database_url: str | None = None
    openai_api_key: str | None = None
    aws_region: str = "us-east-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
