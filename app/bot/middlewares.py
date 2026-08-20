"""Telegram update middlewares: user provisioning, block checks, rate limiting."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from loguru import logger

from app.models.user import UserRole
from app.services.user_service import get_or_create_user, touch_user

# Simple per-user rate limit: max N messages per window (seconds).
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 10.0
_buckets: dict[int, deque] = defaultdict(deque)


class UserMiddleware(BaseMiddleware):
    """Ensure every update has an associated, non-blocked user."""

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        if event.message is not None:
            tg_user = event.message.from_user
        elif event.callback_query is not None:
            tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        user, _created = await get_or_create_user(
            tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        await touch_user(tg_user.id)

        if user.role == UserRole.BLOCKED:
            # Silently ignore blocked users.
            logger.info("Blocked user {} attempted interaction", tg_user.id)
            return None

        data["user"] = user
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Basic per-user flood protection."""

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        msg: Message | None = event.message
        if msg is None or msg.from_user is None:
            return await handler(event, data)

        uid = msg.from_user.id
        now = time.monotonic()
        bucket = _buckets[uid]
        while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_MAX:
            logger.warning("Rate limited user {}", uid)
            return None
        bucket.append(now)
        return await handler(event, data)
