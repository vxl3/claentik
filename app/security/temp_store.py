"""In-memory temporary storage for sensitive transient data.

Used to hold login credentials / OTP codes only for the duration of an
authentication flow. Values are dropped as soon as they are no longer needed
and are never persisted to disk or the database.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TempStore:
    """A tiny TTL cache for transient secrets, keyed by Telegram user id."""

    def __init__(self, default_ttl: float = 600.0) -> None:
        self._default_ttl = default_ttl
        self._data: dict[str, _Entry] = {}

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [k for k, e in self._data.items() if e.expires_at <= now]
        for k in expired:
            self._data.pop(k, None)

    def put(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._purge()
        self._data[key] = _Entry(
            value=value, expires_at=time.monotonic() + (ttl or self._default_ttl)
        )

    def get(self, key: str) -> Any | None:
        self._purge()
        entry = self._data.get(key)
        return entry.value if entry else None

    def pop(self, key: str) -> Any | None:
        self._purge()
        entry = self._data.pop(key, None)
        return entry.value if entry else None

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


# Singleton used across the app.
temp_store = TempStore()
