"""Business logic for TikTok accounts."""
from __future__ import annotations

from loguru import logger

from app.database.engine import session_scope
from app.models.tiktok_account import AccountStatus, TikTokAccount
from app.repositories.account_repository import AccountRepository
from app.tiktok.base import TikTokClient
from app.tiktok.registry import get as get_client, register, remove
from app.tiktok.session_manager import new_context


async def create_client() -> TikTokClient:
    """Create a fresh browser context + client (not yet registered).

    Raises PlaywrightUnavailableError on platforms where browser automation is
    not supported (e.g. Android/Termux).
    """
    # new_context() raises a clear error if Playwright is unavailable, so call
    # it before importing the Playwright-based client.
    context = await new_context()
    from app.tiktok.playwright_client import PlaywrightTikTokClient  # noqa: PLC0415

    return PlaywrightTikTokClient(context)


def register_client(account_id: int, client: TikTokClient) -> None:
    """Register a live client against a real account id."""
    register(account_id, client)


async def close_client(account_id: int) -> None:
    """Close and unregister the client for an account (drops the session)."""
    client = remove(account_id)
    if client is not None:
        await client.close()
    logger.info("Closed TikTok session for account {}", account_id)


async def add_account(
    user_id: int,
    username: str,
    tiktok_user_id: str | None = None,
    display_name: str | None = None,
) -> TikTokAccount:
    async with session_scope() as session:
        repo = AccountRepository(session)
        existing = await repo.get_by_username(user_id, username)
        if existing is not None:
            return existing
        return await repo.create(user_id, username, tiktok_user_id, display_name)


async def list_accounts(user_id: int) -> list[TikTokAccount]:
    async with session_scope() as session:
        repo = AccountRepository(session)
        return await repo.list_for_user(user_id)


async def get_account(account_id: int) -> TikTokAccount | None:
    async with session_scope() as session:
        repo = AccountRepository(session)
        return await repo.get(account_id)


async def delete_account(account_id: int) -> bool:
    """Delete the account and drop all associated temporary data."""
    await close_client(account_id)
    async with session_scope() as session:
        repo = AccountRepository(session)
        return await repo.delete(account_id)


async def update_account_status(account_id: int, status: AccountStatus) -> None:
    async with session_scope() as session:
        repo = AccountRepository(session)
        await repo.update_status(account_id, status)


async def update_account_stats(
    account_id: int, followers: int, following: int
) -> None:
    async with session_scope() as session:
        repo = AccountRepository(session)
        await repo.update_stats(account_id, followers, following)


async def ensure_client(account_id: int) -> TikTokClient:
    """Return the live client for an account, raising if none exists."""
    client = get_client(account_id)
    if client is None:
        raise RuntimeError("لا توجد جلسة نشطة لهذا الحساب، أعد تسجيل الدخول")
    return client
