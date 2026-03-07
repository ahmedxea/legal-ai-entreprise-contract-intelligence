"""
Lightweight async task queue for document processing pipelines.

Provides:
  - Bounded concurrency (configurable worker count)
  - Per-task status tracking (queued → running → done / failed)
  - Automatic retry with exponential back-off
  - Graceful shutdown — drains in-flight tasks before stopping

Usage:
    from app.services.task_queue import task_queue

    # At app startup (inside lifespan):
    task_queue.start()

    # Submit work:
    task_id = await task_queue.submit(my_coroutine, arg1, arg2)

    # Check status:
    info = task_queue.status(task_id)

    # At app shutdown:
    await task_queue.stop()
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class TaskInfo:
    task_id: str
    state: TaskState
    created_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    attempts: int = 0
    error: Optional[str] = None
    result: Any = None


class AsyncTaskQueue:
    """
    In-process async task queue backed by ``asyncio.Queue``.

    Parameters
    ----------
    max_workers : int
        Maximum number of tasks processed concurrently. Each worker is an
        ``asyncio`` Task that pulls from the internal queue.
    max_retries : int
        How many times a failed task is re-attempted before being marked FAILED.
    retry_base_delay : float
        Seconds for the initial retry delay. Doubles on each subsequent attempt.
    """

    def __init__(
        self,
        max_workers: int = 2,
        max_retries: int = 2,
        retry_base_delay: float = 3.0,
    ) -> None:
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay

        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._tasks: Dict[str, TaskInfo] = {}
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Spawn worker tasks.  Call once during app startup."""
        if self._running:
            return
        self._running = True
        loop = asyncio.get_event_loop()
        for i in range(self._max_workers):
            worker = loop.create_task(self._worker_loop(i))
            self._workers.append(worker)
        logger.info(f"[task_queue] Started {self._max_workers} worker(s)")

    async def stop(self, timeout: float = 30.0) -> None:
        """Signal workers to stop and wait for in-flight tasks to drain."""
        if not self._running:
            return
        self._running = False
        # Push sentinel None per worker to unblock queue.get()
        for _ in self._workers:
            await self._queue.put(None)
        # Wait for workers to finish (with timeout)
        done, pending = await asyncio.wait(self._workers, timeout=timeout)
        for t in pending:
            t.cancel()
        self._workers.clear()
        logger.info("[task_queue] Stopped")

    # ── Public API ────────────────────────────────────────────────────────────

    async def submit(
        self,
        coro_fn: Callable[..., Awaitable[Any]],
        *args: Any,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Enqueue a coroutine function for async execution.

        Returns the task_id immediately (the actual work runs later).
        """
        tid = task_id or str(uuid.uuid4())
        info = TaskInfo(task_id=tid, state=TaskState.QUEUED, created_at=time.time())
        self._tasks[tid] = info
        await self._queue.put((tid, coro_fn, args))
        logger.info(f"[task_queue] Submitted task {tid}")
        return tid

    def status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return a JSON-serialisable status dict, or None if unknown."""
        info = self._tasks.get(task_id)
        if not info:
            return None
        return {
            "task_id": info.task_id,
            "state": info.state.value,
            "attempts": info.attempts,
            "error": info.error,
            "created_at": info.created_at,
            "started_at": info.started_at,
            "finished_at": info.finished_at,
        }

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def active_tasks(self) -> int:
        return sum(1 for t in self._tasks.values() if t.state == TaskState.RUNNING)

    def all_statuses(self) -> list[Dict[str, Any]]:
        """Return statuses of all tracked tasks (most recent first)."""
        return sorted(
            [self.status(tid) for tid in self._tasks],
            key=lambda s: s["created_at"],
            reverse=True,
        )

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _worker_loop(self, worker_id: int) -> None:
        """Long-running worker: pull items from the queue and execute them."""
        logger.debug(f"[task_queue] Worker {worker_id} started")
        while self._running or not self._queue.empty():
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if item is None:
                # Sentinel → shutdown
                break
            tid, coro_fn, args = item
            await self._execute(tid, coro_fn, args)
        logger.debug(f"[task_queue] Worker {worker_id} stopped")

    async def _execute(
        self,
        task_id: str,
        coro_fn: Callable[..., Awaitable[Any]],
        args: tuple,
    ) -> None:
        """Run the task, retrying on failure with exponential back-off."""
        info = self._tasks[task_id]
        info.state = TaskState.RUNNING
        info.started_at = time.time()

        last_error: Optional[Exception] = None
        max_attempts = 1 + self._max_retries

        for attempt in range(max_attempts):
            info.attempts = attempt + 1
            try:
                result = await coro_fn(*args)
                info.state = TaskState.DONE
                info.result = result
                info.finished_at = time.time()
                elapsed = info.finished_at - info.started_at
                logger.info(
                    f"[task_queue] Task {task_id} completed in {elapsed:.1f}s"
                )
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"[task_queue] Task {task_id} attempt {attempt + 1}/{max_attempts} "
                    f"failed: {exc}"
                )
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        info.state = TaskState.FAILED
        info.error = str(last_error)
        info.finished_at = time.time()
        logger.error(f"[task_queue] Task {task_id} failed after {max_attempts} attempts: {last_error}")


# Module-level singleton
task_queue = AsyncTaskQueue(max_workers=2, max_retries=2, retry_base_delay=3.0)
