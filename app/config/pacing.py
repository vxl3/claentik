"""Pacing configuration — conservative, configurable delays between actions.

These values control how fast the bot performs TikTok actions. They are
intentionally conservative to reduce load on TikTok's service and to respect
its rate limits. The goal is NOT to bypass protections.

All values can be adjusted here (or via environment variables) without touching
the core bot logic.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.config.settings import get_settings


@dataclass(frozen=True)
class PacingConfig:
    """Immutable snapshot of pacing parameters for a single operation run."""

    base_delay_seconds: float = 4.0
    jitter_min: float = 1.0
    jitter_max: float = 3.0
    backoff_base: float = 2.0
    backoff_max_seconds: float = 300.0
    max_consecutive_failures: int = 5
    progress_update_every: int = 5
    progress_update_interval: int = 15


def build_pacing_config() -> PacingConfig:
    """Build a PacingConfig from the current application settings."""
    s = get_settings()
    return PacingConfig(
        base_delay_seconds=s.pacing_base_delay_seconds,
        jitter_min=s.pacing_jitter_min,
        jitter_max=s.pacing_jitter_max,
        backoff_base=s.pacing_backoff_base,
        backoff_max_seconds=s.pacing_backoff_max_seconds,
        max_consecutive_failures=s.pacing_max_consecutive_failures,
        progress_update_every=s.pacing_progress_update_every,
        progress_update_interval=s.pacing_progress_update_interval,
    )


class Pacer:
    """Computes per-action delays and exponential backoff.

    The pacer keeps internal state so that backoff grows on consecutive
    failures and resets after a success.
    """

    def __init__(self, config: PacingConfig) -> None:
        self._config = config
        self._consecutive_failures = 0
        self._backoff_level = 0

    def next_delay(self, *, failed: bool) -> float:
        """Return the delay (seconds) to wait before the next action.

        On success the delay is ``base + jitter``. On failure an exponential
        backoff is applied, growing up to ``backoff_max_seconds``.
        """
        if failed:
            self._consecutive_failures += 1
            self._backoff_level += 1
            delay = min(
                self._config.backoff_base ** self._backoff_level,
                self._config.backoff_max_seconds,
            )
        else:
            self._consecutive_failures = 0
            self._backoff_level = 0
            delay = self._config.base_delay_seconds + random.uniform(
                self._config.jitter_min, self._config.jitter_max
            )
        return max(0.0, delay)

    @property
    def should_stop(self) -> bool:
        """True when consecutive failures exceeded the allowed threshold."""
        return self._consecutive_failures >= self._config.max_consecutive_failures
