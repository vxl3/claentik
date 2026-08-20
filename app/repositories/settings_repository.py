"""Data access for system settings."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> str | None:
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        setting = (await self._session.execute(stmt)).scalar_one_or_none()
        return setting.value if setting else None

    async def set(self, key: str, value: str) -> None:
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        setting = (await self._session.execute(stmt)).scalar_one_or_none()
        if setting is None:
            self._session.add(SystemSetting(key=key, value=value))
        else:
            setting.value = value
        await self._session.flush()
