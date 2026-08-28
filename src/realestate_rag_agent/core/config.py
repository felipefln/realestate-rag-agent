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

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5544/realestate"
    db_echo: bool = False

    # Embeddings. The active provider's dimension must match the `embedding`
    # column (see EMBEDDING_DIM in repositories/models.py) — switching provider
    # to one with a different dimension needs a new migration.
    embedding_provider: Literal["local", "openai", "fake"] = "local"
    embedding_model_local: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_model_openai: str = "text-embedding-3-small"

    openai_api_key: str | None = None
    aws_region: str = "us-east-1"

    # Agent (LangGraph + Claude).
    agent_model: str = "claude-sonnet-5"
    anthropic_api_key: str | None = None
    agent_recursion_limit: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
