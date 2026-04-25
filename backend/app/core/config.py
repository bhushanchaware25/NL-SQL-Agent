"""
Core application settings loaded from environment variables.
Uses Pydantic BaseSettings for type-safe configuration.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── OpenRouter / LLM ─────────────────────────────────────────────────────
    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_model: str = Field(
        default="openrouter/auto",
        description="Model identifier passed to OpenRouter",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://nl2sql:nl2sql_secret@localhost:5432/ecommerce",
        description="SQLAlchemy-compatible database URL",
    )

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default="./chroma_data",
        description="Directory where ChromaDB persists its data",
    )

    # ── Agent behaviour ───────────────────────────────────────────────────────
    max_retries: int = Field(
        default=3, ge=1, le=10,
        description="Max self-correction retries in critic loop",
    )
    sql_safety_enabled: bool = Field(
        default=True,
        description="Block destructive SQL statements",
    )

    # ── API ────────────────────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


settings = get_settings()
