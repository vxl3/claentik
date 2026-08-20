"""Tests for the broadcast service (with a fake bot)."""
from __future__ import annotations

import types

from app.services.broadcast_service import broadcast
from app.services.user_service import get_or_create_user


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


async def test_broadcast_sends_to_all_active_users(monkeypatch):
    # Register a few users.
    for uid in (100, 200, 300):
        await get_or_create_user(uid)

    # Speed up broadcast by zeroing delays.
    fake_settings = types.SimpleNamespace(
        broadcast_batch_size=1000, broadcast_delay_between_messages=0.0
    )
    import app.services.broadcast_service as bs

    monkeypatch.setattr(bs, "get_settings", lambda: fake_settings)

    bot = FakeBot()
    result = await broadcast(bot, "hello")

    assert result["total"] == 3
    assert result["success"] == 3
    assert result["failed"] == 0
    assert {cid for cid, _ in bot.sent} == {100, 200, 300}
    assert all(text == "hello" for _, text in bot.sent)
