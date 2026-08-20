"""Data access for users."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> tuple[User, bool]:
        """Return the user, creating it if missing. Second value = created?"""
        user = await self.get(telegram_id)
        if user is not None:
            return user, False
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self._session.add(user)
        await self._session.flush()
        return user, True

    async def touch_last_active(self, telegram_id: int) -> None:
        await self._session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_active=datetime.now(timezone.utc))
        )

    async def set_role(self, telegram_id: int, role: UserRole) -> None:
        await self._session.execute(
            update(User).where(User.telegram_id == telegram_id).values(role=role)
        )

    async def set_status(self, telegram_id: int, status: UserStatus) -> None:
        await self._session.execute(
            update(User).where(User.telegram_id == telegram_id).values(status=status)
        )

    async def count(self) -> int:
        return (await self._session.execute(select(func.count(User.telegram_id)))).scalar_one()

    async def count_active(self) -> int:
        stmt = select(func.count(User.telegram_id)).where(User.status == UserStatus.ACTIVE)
        return (await self._session.execute(stmt)).scalar_one()

    async def count_blocked(self) -> int:
        stmt = select(func.count(User.telegram_id)).where(User.status == UserStatus.BLOCKED)
        return (await self._session.execute(stmt)).scalar_one()

    async def all_ids(self) -> list[int]:
        stmt = select(User.telegram_id).where(User.status == UserStatus.ACTIVE)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_recent(self, limit: int = 50) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_blocked(self) -> list[User]:
        stmt = select(User).where(User.status == UserStatus.BLOCKED)
        return list((await self._session.execute(stmt)).scalars().all())
