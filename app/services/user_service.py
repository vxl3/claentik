"""Business logic for users."""
from __future__ import annotations

from app.database.engine import session_scope
from app.models.user import User, UserRole, UserStatus
from app.repositories.user_repository import UserRepository


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> tuple[User, bool]:
    async with session_scope() as session:
        repo = UserRepository(session)
        return await repo.get_or_create(telegram_id, username, first_name)


async def touch_user(telegram_id: int) -> None:
    async with session_scope() as session:
        repo = UserRepository(session)
        await repo.touch_last_active(telegram_id)


async def set_user_role(telegram_id: int, role: UserRole) -> None:
    async with session_scope() as session:
        repo = UserRepository(session)
        await repo.set_role(telegram_id, role)


async def set_user_status(telegram_id: int, status: UserStatus) -> None:
    async with session_scope() as session:
        repo = UserRepository(session)
        await repo.set_status(telegram_id, status)
