"""Business logic for cleanup operations."""
from __future__ import annotations

from aiogram import Bot
from loguru import logger

from app.database.engine import session_scope
from app.models.operation import Operation, OperationType
from app.models.tiktok_account import TikTokAccount
from app.repositories.account_repository import AccountRepository
from app.repositories.operation_repository import OperationRepository
from app.services.account_service import ensure_client
from app.tiktok.models import ComparisonResult
from app.workers.operation_manager import OperationManager
from app.workers.progress import ProgressReporter

_TYPE_LABELS = {
    OperationType.CLEANUP_FOLLOWING: "Following",
    OperationType.CLEANUP_FOLLOWERS: "Followers",
}


async def get_plan(account_id: int) -> ComparisonResult:
    """Fetch and compare followers/following for an account."""
    client = await ensure_client(account_id)
    return await client.compare()


async def refresh_stats(account_id: int) -> TikTokAccount | None:
    """Refresh cached follower/following counts from TikTok."""
    client = await ensure_client(account_id)
    profile = await client.get_profile()
    await _save_profile_stats(account_id, profile)
    async with session_scope() as session:
        return await AccountRepository(session).get(account_id)


async def _save_profile_stats(account_id: int, profile) -> None:
    from app.services.account_service import update_account_stats

    await update_account_stats(
        account_id, profile.followers_count, profile.following_count
    )


async def account_is_busy(account_id: int) -> bool:
    """Whether the account currently has a running operation."""
    manager = _get_manager()
    if manager.is_running(account_id):
        return True
    async with session_scope() as session:
        repo = OperationRepository(session)
        return await repo.running_for_account(account_id) is not None


async def start_operation(
    user_id: int,
    account_id: int,
    operation_type: OperationType,
    targets: list[str],
    bot: Bot,
    chat_id: int,
) -> tuple[bool, str | None]:
    """Create the operation record, send a progress message, and start the job."""
    manager = _get_manager()
    if manager.is_running(account_id):
        return False, "⚠️ هذا الحساب قيد المعالجة حاليًا."

    if not targets:
        return False, "لا توجد حسابات للتنظيف."

    async with session_scope() as session:
        repo = OperationRepository(session)
        op = await repo.create(user_id, account_id, operation_type)
        await AccountRepository(session).set_last_operation(
            account_id, operation_type.value
        )
        operation_id = op.id

    from app.keyboards.operations import stop_operation as stop_keyboard
    from app.utils.text import progress_message

    label = _TYPE_LABELS[operation_type]
    sent = await bot.send_message(
        chat_id=chat_id,
        text=progress_message(label, 0, len(targets), 0, 0),
        reply_markup=stop_keyboard(account_id),
    )
    progress = ProgressReporter(bot, chat_id, sent.message_id)

    # Re-fetch the operation object so the job mutates a persisted instance.
    async with session_scope() as session:
        op = await OperationRepository(session).get(operation_id)

    await manager.start_operation(op, targets, progress, label)
    logger.info(
        "Started {} for account {} ({} targets)", operation_type.value, account_id, len(targets)
    )
    return True, None


async def stop_operation(account_id: int) -> bool:
    manager = _get_manager()
    return await manager.stop_operation(account_id)


async def latest_operations(account_id: int, limit: int = 5) -> list[Operation]:
    async with session_scope() as session:
        return await OperationRepository(session).latest_for_account(account_id, limit)


def _get_manager() -> OperationManager:
    from app.dependencies import get_container

    return get_container().operation_manager
