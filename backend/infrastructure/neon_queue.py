from application.ports.task_queue import TaskQueue
from domain.analysis.entities import VisualTask
from infrastructure.neon_store import NeonStore


class NeonTaskQueue(TaskQueue):
    """Implement the durable visual queue with Neon PostgreSQL."""

    def __init__(self, store: NeonStore) -> None:
        self._store = store

    async def enqueue(self, task: VisualTask) -> None:
        """Persist a visual task using its analysis idempotency key."""
        await self._store.enqueue_task(task)

    async def dequeue(self) -> VisualTask | None:
        """Return the oldest unclaimed visual task."""
        await self._store.retry_expired_tasks()
        return await self._store.dequeue_task()

    async def ack(self, task_id: str) -> None:
        """Acknowledge a task after its result is durably delivered."""
        await self._store.ack_task(task_id)
