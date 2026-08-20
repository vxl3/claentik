"""Data access for admin logs."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_log import AdminLog


class AdminLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, actor_id: int, action: str, details: str | None = None) -> None:
        self._session.add(AdminLog(actor_id=actor_id, action=action, details=details))
        await self._session.flush()

    async def latest(self, limit: int = 20) -> list[AdminLog]:
        stmt = select(AdminLog).order_by(AdminLog.id.desc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())
