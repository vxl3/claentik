"""In-memory registry of live TikTok clients per account.

Sessions are kept in memory only (unless persistence is explicitly enabled) so
that a bot restart drops every session — matching the "no persistent session"
requirement.
"""
from __future__ import annotations

from app.tiktok.base import TikTokClient

_clients: dict[int, TikTokClient] = {}


def register(account_id: int, client: TikTokClient) -> None:
    _clients[account_id] = client


def get(account_id: int) -> TikTokClient | None:
    return _clients.get(account_id)


def remove(account_id: int) -> TikTokClient | None:
    return _clients.pop(account_id, None)


def has(account_id: int) -> bool:
    return account_id in _clients
