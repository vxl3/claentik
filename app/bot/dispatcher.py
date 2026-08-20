"""Dispatcher construction and router registration."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

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

    # Routers.
    dp.include_router(start.router)
    dp.include_router(login.router)
    dp.include_router(accounts.router)
    dp.include_router(operations.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)
    dp.include_router(owner.router)

    return dp
