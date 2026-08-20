"""Tests for operation comparison logic and operation records."""
from __future__ import annotations

from app.models.operation import OperationStatus, OperationType
from app.tiktok.models import ComparisonResult
from app.repositories.operation_repository import OperationRepository
from app.database.engine import session_scope


def test_comparison_i_follow_not_back():
    c = ComparisonResult(
        followers={"a", "b", "c"},
        following={"a", "b", "d", "e"},
    )
    assert c.i_follow_but_not_follow_back == ["d", "e"]


def test_comparison_they_follow_i_dont():
    c = ComparisonResult(
        followers={"a", "b", "c"},
        following={"a", "b"},
    )
    assert c.they_follow_but_i_dont == ["c"]


def test_comparison_mutual():
    c = ComparisonResult(followers={"a", "b"}, following={"a", "b"})
    assert c.i_follow_but_not_follow_back == []
    assert c.they_follow_but_i_dont == []


async def test_operation_record_lifecycle():
    op_id = None
    async with session_scope() as session:
        repo = OperationRepository(session)
        op = await repo.create(1, 1, OperationType.CLEANUP_FOLLOWING)
        op_id = op.id
        assert op.status == OperationStatus.PENDING

        await repo.update(
            op.id,
            status=OperationStatus.RUNNING,
            total=10,
            processed_count=5,
            success_count=4,
            failed_count=1,
        )
        await repo.add_result(op.id, "victim1", "unfollow", True)
        await repo.add_result(op.id, "victim2", "unfollow", False, "blocked")

    async with session_scope() as session:
        repo = OperationRepository(session)
        fetched = await repo.get(op_id)
        assert fetched.status == OperationStatus.RUNNING
        assert fetched.total == 10
        assert fetched.processed_count == 5
        assert fetched.success_count == 4
        assert fetched.failed_count == 1

        from sqlalchemy import func, select

        from app.models.operation_result import OperationResult

        count = (
            await session.execute(
                select(func.count(OperationResult.id)).where(
                    OperationResult.operation_id == op_id
                )
            )
        ).scalar_one()
        assert count == 2


async def test_running_for_account():
    async with session_scope() as session:
        repo = OperationRepository(session)
        op = await repo.create(1, 7, OperationType.CLEANUP_FOLLOWERS)
        await repo.update(op.id, status=OperationStatus.RUNNING)
        running = await repo.running_for_account(7)
        assert running is not None and running.id == op.id

        await repo.update(op.id, status=OperationStatus.COMPLETED)
        assert await repo.running_for_account(7) is None
