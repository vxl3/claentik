"""A single cleanup operation executed sequentially with conservative pacing."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable

from loguru import logger

from app.config.pacing import Pacer
from app.database.engine import session_scope
from app.models.operation import Operation, OperationStatus
from app.repositories.operation_repository import OperationRepository
from app.tiktok.errors import (
    TikTokAccountUnavailableError,
    TikTokAuthError,
    TikTokLoggedOutError,
    TikTokRateLimitError,
    TikTokTimeoutError,
)
from app.workers.progress import ProgressReporter

ActionFn = Callable[[str], Awaitable[None]]


class OperationJob:
    """Runs one operation (unfollow non-followers / remove followers)."""

    def __init__(
        self,
        operation: Operation,
        targets: list[str],
        action: ActionFn,
        pacer: Pacer,
        cancel_event: asyncio.Event,
        progress: ProgressReporter,
        progress_interval: int,
        progress_every: int,
        type_label: str,
    ) -> None:
        self._operation = operation
        self._targets = targets
        self._action = action
        self._pacer = pacer
        self._cancel_event = cancel_event
        self._progress = progress
        self._progress_interval = progress_interval
        self._progress_every = progress_every
        self._type_label = type_label

    async def run(self) -> None:
        op = self._operation
        total = len(self._targets)
        processed = 0
        success = 0
        failed = 0
        started = time.monotonic()

        async with session_scope() as session:
            repo = OperationRepository(session)
            await repo.update(
                op.id,
                status=OperationStatus.RUNNING,
                total=total,
                started_at=datetime.now(timezone.utc),
            )
        op.status = OperationStatus.RUNNING
        op.total = total

        last_report = 0.0
        for i, target in enumerate(self._targets):
            if self._cancel_event.is_set():
                logger.info("Operation {} cancelled by user", op.id)
                break

            try:
                await self._action(target)
                success += 1
                action_failed = False
            except (TikTokRateLimitError, TikTokAuthError, TikTokLoggedOutError,
                    TikTokAccountUnavailableError) as exc:
                # Non-retryable / stop-the-world conditions.
                failed += 1
                processed += 1
                await self._flush_counts(processed, success, failed)
                await self._finalize(OperationStatus.STOPPED, error=exc.user_message)
                logger.warning("Operation {} stopped: {}", op.id, exc.user_message)
                return
            except TikTokTimeoutError as exc:
                # Temporary network issue -> count as failure, keep going.
                failed += 1
                action_failed = True
                logger.warning("Operation {} timeout on {}: {}", op.id, target, exc)
            except Exception as exc:  # noqa: BLE001 - defensive boundary
                failed += 1
                action_failed = True
                logger.error("Operation {} error on {}: {}", op.id, target, exc)

            processed += 1

            # Conservative pacing between actions.
            delay = self._pacer.next_delay(failed=action_failed)
            if self._pacer.should_stop:
                await self._flush_counts(processed, success, failed)
                await self._finalize(
                    OperationStatus.STOPPED,
                    error="توقف العملية بعد تكرار الأخطاء — قد يكون TikTok يحدّ من العمليات.",
                )
                logger.warning("Operation {} stopped: max consecutive failures", op.id)
                return

            now = time.monotonic()
            if (processed % self._progress_every == 0) or (now - last_report >= self._progress_interval):
                await self._report(processed, success, failed)
                last_report = now

            # Interruptible sleep.
            if not self._cancel_event.is_set() and i < len(self._targets) - 1:
                try:
                    await asyncio.wait_for(self._cancel_event.wait(), timeout=delay)
                    if self._cancel_event.is_set():
                        break
                except asyncio.TimeoutError:
                    pass

        await self._flush_counts(processed, success, failed)
        if self._cancel_event.is_set():
            await self._finalize(OperationStatus.STOPPED)
        else:
            await self._finalize(OperationStatus.COMPLETED, duration=time.monotonic() - started)

    # ------------------------------------------------------------------ #
    async def _flush_counts(self, processed: int, success: int, failed: int) -> None:
        async with session_scope() as session:
            repo = OperationRepository(session)
            await repo.update(
                self._operation.id,
                processed_count=processed,
                success_count=success,
                failed_count=failed,
            )

    async def _report(self, processed: int, success: int, failed: int) -> None:
        from app.utils.text import progress_message

        text = progress_message(
            self._type_label,
            processed,
            self._operation.total,
            success,
            failed,
        )
        await self._progress.update(text)

    async def _finalize(
        self,
        status: OperationStatus,
        error: str | None = None,
        duration: float | None = None,
    ) -> None:
        from app.utils.text import result_message, stopped_message

        async with session_scope() as session:
            repo = OperationRepository(session)
            await repo.update(
                self._operation.id,
                status=status,
                error_reason=error,
                finished_at=datetime.now(timezone.utc),
            )
            # Clear last_operation flag on the account when done.
            from app.repositories.account_repository import AccountRepository
            acct_repo = AccountRepository(session)
            await acct_repo.set_last_operation(self._operation.tiktok_account_id, None)

        op = self._operation
        if status == OperationStatus.STOPPED:
            text = stopped_message(op.processed_count, op.total, op.success_count, op.failed_count)
        else:
            text = result_message(
                self._type_label,
                op.total,
                op.success_count,
                op.failed_count,
                duration,
            )
        from app.keyboards.main import back_to_menu

        await self._progress.finalize(text, back_to_menu())
