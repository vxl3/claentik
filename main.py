"""Application entry point.

Usage:
    python main.py

Requires a valid .env (run `python -m scripts.setup_wizard` first if missing).
"""
from __future__ import annotations

import asyncio
import signal

from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.bot.dispatcher import build_dispatcher
from app.config.settings import get_settings
from app.database.base import Base
from app.database.engine import close_engine, get_engine
from app.dependencies import Container, set_container
from app.models import UserRole  # noqa: F401 - ensure models are registered
from app.tiktok.session_manager import shutdown as tiktok_shutdown
from app.utils.logger import setup_logging
from app.workers.operation_manager import OperationManager


async def _init_db() -> None:
    """Create tables if they do not exist (idempotent).

    For versioned migrations use Alembic (`alembic upgrade head`).
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _ensure_owner() -> None:
    """Create/update the owner user with the OWNER role."""
    from app.database.engine import session_scope
    from app.repositories.user_repository import UserRepository

    settings = get_settings()
    if not settings.owner_telegram_id:
        return
    async with session_scope() as session:
        repo = UserRepository(session)
        await repo.get_or_create(settings.owner_telegram_id)
        await repo.set_role(settings.owner_telegram_id, UserRole.OWNER)
    logger.info("Owner user ensured: {}", settings.owner_telegram_id)


async def main() -> None:
    setup_logging()
    settings = get_settings()

    if not settings.is_configured:
        logger.error(
            "Configuration is incomplete. Run `python -m scripts.setup_wizard` "
            "to create your .env file."
        )
        raise SystemExit(1)

    await _init_db()
    await _ensure_owner()

    bot = Bot(token=settings.telegram_bot_token)
    storage = MemoryStorage()
    operation_manager = OperationManager(bot)
    set_container(Container(bot=bot, operation_manager=operation_manager, fsm_storage=storage))

    dp = build_dispatcher(bot, storage)

    logger.info("Bot is starting...")

    stop_event = asyncio.Event()

    def _request_stop() -> None:
        logger.info("Shutdown signal received.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:  # pragma: no cover - Windows
            pass

    try:
        await dp.start_polling(bot, skip_updates=True)
        await stop_event.wait()
    finally:
        logger.info("Shutting down...")
        await operation_manager.shutdown()
        await tiktok_shutdown()
        await bot.session.close()
        await close_engine()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")
