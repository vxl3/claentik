"""Safe, rate-limited broadcast to all bot users."""
from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from app.config.settings import get_settings
from app.database.engine import session_scope
from app.repositories.user_repository import UserRepository


async def broadcast(bot: Bot, text: str) -> dict:
    """Send ``text`` to every active user, respecting Telegram rate limits.

    Returns counts of recipients, successes and failures.
    """
    settings = get_settings()
    async with session_scope() as session:
        user_ids = await UserRepository(session).all_ids()

    total = len(user_ids)
    success = 0
    failed = 0

    batch_size = settings.broadcast_batch_size
    delay = settings.broadcast_delay_between_messages

    for start in range(0, total, batch_size):
        batch = user_ids[start : start + batch_size]
        for user_id in batch:
            try:
                await bot.send_message(chat_id=user_id, text=text)
                success += 1
            except TelegramAPIError as exc:
                failed += 1
                logger.warning("Broadcast to {} failed: {}", user_id, exc)
            # Respect Telegram rate limits between messages.
            await asyncio.sleep(delay)
        # Slightly longer pause between batches.
        await asyncio.sleep(1.0)

    logger.info("Broadcast finished: {} sent, {} failed of {}", success, failed, total)
    return {"total": total, "success": success, "failed": failed}
