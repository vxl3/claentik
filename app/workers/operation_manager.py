"""Coordinates cleanup jobs: one isolated job per account, no concurrency on
the same account, conservative global concurrency."""
from __future__ import annotations

import asyncio

from aiogram import Bot
from loguru import logger

from app.config.pacing import Pacer, build_pacing_config
from app.models.operation import Operation, OperationType
from app.tiktok.registry import get as get_client
from app.workers.job import OperationJob
from app.workers.progress import ProgressReporter

# Maximum number of browser-driven operations running at once across all users.
MAX_CONCURRENT_OPERATIONS = 2


class OperationManager:
    """Owns the lifecycle of running operations and their cancel signals."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._tasks: dict[int, asyncio.Task] = {}  # account_id -> task
        self._cancels: dict[int, asyncio.Event] = {}  # account_id -> event
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_OPERATIONS)

    def is_running(self, account_id: int) -> bool:
        task = self._tasks.get(account_id)
        return task is not None and not task.done()

    def running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if not t.done())

    async def start_operation(
        self,
        operation: Operation,
        targets: list[str],
        progress: ProgressReporter,
        type_label: str,
    ) -> None:
        """Start a cleanup operation for the given account (must be idle)."""
        account_id = operation.tiktok_account_id
        if self.is_running(account_id):
            raise RuntimeError("account already has a running operation")

        client = get_client(account_id)
        if client is None:
            raise RuntimeError("no active TikTok session for this account")

        if operation.operation_type == OperationType.CLEANUP_FOLLOWING:
            action = client.unfollow
        else:
            action = client.remove_follower

        cancel_event = asyncio.Event()
        self._cancels[account_id] = cancel_event
        pacer = Pacer(build_pacing_config())

        job = OperationJob(
            operation=operation,
            targets=targets,
            action=action,
            pacer=pacer,
            cancel_event=cancel_event,
            progress=progress,
            progress_interval=build_pacing_config().progress_update_interval,
            progress_every=build_pacing_config().progress_update_every,
            type_label=type_label,
        )

        task = asyncio.create_task(self._run_wrapped(job))
        self._tasks[account_id] = task
        task.add_done_callback(lambda t: self._on_done(account_id, t))

    async def _run_wrapped(self, job: OperationJob) -> None:
        async with self._semaphore:
            try:
                await job.run()
            except Exception as exc:  # noqa: BLE001 - never let a job crash the bot
                logger.exception("Unhandled error in operation job: {}", exc)

    def _on_done(self, account_id: int, task: asyncio.Task) -> None:
        self._tasks.pop(account_id, None)
        self._cancels.pop(account_id, None)

    async def stop_operation(self, account_id: int) -> bool:
        """Request a graceful stop for a running operation."""
        event = self._cancels.get(account_id)
        if event is None:
            return False
        event.set()
        return True

    async def shutdown(self) -> None:
        """Cancel all running operations on bot shutdown."""
        for event in self._cancels.values():
            event.set()
        tasks = list(self._tasks.values())
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._cancels.clear()
        logger.info("OperationManager shut down")
