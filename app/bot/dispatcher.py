"""Dispatcher construction and router registration."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from loguru import logger

from app.bot.middlewares import RateLimitMiddleware, UserMiddleware
from app.handlers import (
    accounts,
    login,
    operations,
    owner,
    settings,
    start,
    stats,
)


def build_dispatcher(bot: Bot, storage: MemoryStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)

    # Middlewares run for every update.
    dp.update.outer_middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    @dp.errors()
    async def on_error(event, exception):
        """Swallow harmless errors; log the rest without crashing the bot."""
        text = str(exception)
        if "query is too old" in text or "query ID is invalid" in text:
            # Stale callback query — ignore silently.
            return True
        logger.error("Unhandled error: {}", exception)
        return True

    # Routers.
    dp.include_router(start.router)
    dp.include_router(login.router)
    dp.include_router(accounts.router)
    dp.include_router(operations.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)
    dp.include_router(owner.router)

    return dp

