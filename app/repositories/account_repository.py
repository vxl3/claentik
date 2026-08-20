"""Data access for TikTok accounts."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tiktok_account import AccountStatus, TikTokAccount


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, account_id: int) -> TikTokAccount | None:
        stmt = select(TikTokAccount).where(TikTokAccount.id == account_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_username(self, user_id: int, username: str) -> TikTokAccount | None:
        stmt = select(TikTokAccount).where(
            TikTokAccount.user_id == user_id,
            TikTokAccount.username == username,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[TikTokAccount]:
        stmt = (
            select(TikTokAccount)
            .where(TikTokAccount.user_id == user_id)
            .order_by(TikTokAccount.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create(
        self,
        user_id: int,
        username: str,
        tiktok_user_id: str | None = None,
        display_name: str | None = None,
    ) -> TikTokAccount:
        account = TikTokAccount(
            user_id=user_id,
            username=username,
            tiktok_user_id=tiktok_user_id,
            display_name=display_name,
            status=AccountStatus.CONNECTED,
        )
        self._session.add(account)
        await self._session.flush()
        return account

    async def update_status(self, account_id: int, status: AccountStatus) -> None:
        account = await self.get(account_id)
        if account is not None:
            account.status = status
            await self._session.flush()

    async def update_stats(
        self,
        account_id: int,
        followers_count: int,
        following_count: int,
    ) -> None:
        account = await self.get(account_id)
        if account is not None:
            account.followers_count = followers_count
            account.following_count = following_count
            await self._session.flush()

    async def set_last_operation(self, account_id: int, op: str | None) -> None:
        account = await self.get(account_id)
        if account is not None:
            account.last_operation = op
            await self._session.flush()

    async def delete(self, account_id: int) -> bool:
        account = await self.get(account_id)
        if account is None:
            return False
        await self._session.delete(account)
        await self._session.flush()
        return True

    async def count(self) -> int:
        return (await self._session.execute(select(func.count(TikTokAccount.id)))).scalar_one()

    async def list_recent(self, limit: int = 50) -> list[TikTokAccount]:
        stmt = select(TikTokAccount).order_by(TikTokAccount.created_at.desc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())
