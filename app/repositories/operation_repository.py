"""Data access for operations and their results."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation, OperationStatus, OperationType
from app.models.operation_result import OperationResult


class OperationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, operation_id: int) -> Operation | None:
        stmt = select(Operation).where(Operation.id == operation_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        tiktok_account_id: int,
        operation_type: OperationType,
    ) -> Operation:
        op = Operation(
            user_id=user_id,
            tiktok_account_id=tiktok_account_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            total=0,
        )
        self._session.add(op)
        await self._session.flush()
        return op

    async def update(
        self,
        operation_id: int,
        *,
        status: OperationStatus | None = None,
        total: int | None = None,
        processed_count: int | None = None,
        success_count: int | None = None,
        failed_count: int | None = None,
        error_reason: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        op = await self.get(operation_id)
        if op is None:
            return
        if status is not None:
            op.status = status
        if total is not None:
            op.total = total
        if processed_count is not None:
            op.processed_count = processed_count
        if success_count is not None:
            op.success_count = success_count
        if failed_count is not None:
            op.failed_count = failed_count
        if error_reason is not None:
            op.error_reason = error_reason
        if started_at is not None:
            op.started_at = started_at
        if finished_at is not None:
            op.finished_at = finished_at
        await self._session.flush()

    async def add_result(
        self,
        operation_id: int,
        target_username: str,
        action: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        result = OperationResult(
            operation_id=operation_id,
            target_username=target_username,
            action=action,
            success=success,
            error=error,
        )
        self._session.add(result)
        await self._session.flush()

    async def latest_for_account(
        self, tiktok_account_id: int, limit: int = 5
    ) -> list[Operation]:
        stmt = (
            select(Operation)
            .where(Operation.tiktok_account_id == tiktok_account_id)
            .order_by(Operation.id.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def count(self) -> int:
        return (await self._session.execute(select(func.count(Operation.id)))).scalar_one()

    async def count_by_status(self, status: OperationStatus) -> int:
        stmt = select(func.count(Operation.id)).where(Operation.status == status)
        return (await self._session.execute(stmt)).scalar_one()

    async def running_for_account(self, tiktok_account_id: int) -> Operation | None:
        stmt = (
            select(Operation)
            .where(
                Operation.tiktok_account_id == tiktok_account_id,
                Operation.status == OperationStatus.RUNNING,
            )
            .order_by(Operation.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()
