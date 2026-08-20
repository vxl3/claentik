"""Aggregate statistics for the owner panel."""
from __future__ import annotations

from app.database.engine import session_scope
from app.models.operation import OperationStatus
from app.repositories.account_repository import AccountRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.user_repository import UserRepository


async def owner_stats() -> dict:
    async with session_scope() as session:
        users = UserRepository(session)
        accounts = AccountRepository(session)
        ops = OperationRepository(session)
        return {
            "users": await users.count(),
            "active_users": await users.count_active(),
            "blocked": await users.count_blocked(),
            "accounts": await accounts.count(),
            "operations": await ops.count(),
            "completed": await ops.count_by_status(OperationStatus.COMPLETED),
            "failed": await ops.count_by_status(OperationStatus.FAILED),
        }
