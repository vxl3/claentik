"""Application settings loaded from environment variables / .env file.

No secrets are ever hardcoded here — everything comes from the environment.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    All sensitive values (bot token, owner id, database url) are read from the
    environment, never from source code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    telegram_bot_token: str = ""
    owner_telegram_id: int = 0

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://tiktokbot:tiktokbot_password@localhost:5432/tiktokbot"
    )

    # --- Logging ---
    log_level: str = "INFO"
    log_dir: str = "logs"

    # --- TikTok adapter ---
    tiktok_automation_enabled: bool = True
    tiktok_browser_headless: bool = True
    tiktok_persist_session: bool = False

    # --- Pacing ---
    pacing_base_delay_seconds: float = 4.0
    pacing_jitter_min: float = 1.0
    pacing_jitter_max: float = 3.0
    pacing_backoff_base: float = 2.0
    pacing_backoff_max_seconds: float = 300.0
    pacing_max_consecutive_failures: int = 5
    pacing_progress_update_every: int = 5
    pacing_progress_update_interval: int = 15

    # --- Broadcast ---
    broadcast_batch_size: int = 20
    broadcast_delay_between_messages: float = 0.5

    @property
    def is_configured(self) -> bool:
        """Whether the mandatory secrets are present."""
        return bool(self.telegram_bot_token and self.owner_telegram_id)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
