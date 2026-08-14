"""
Application settings loaded from environment variables.

Uses pydantic-settings to validate and type-cast .env values at startup.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — all values come from .env or OS env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "FinOps Cloud Cost Optimizer"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/finops"

    # ── Redis / Celery ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── AWS defaults ─────────────────────────────────────────────
    AWS_DEFAULT_REGION: str = "us-east-1"

    # ── Gemini AI API Key ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor — settings are read once and cached."""
    return Settings()
