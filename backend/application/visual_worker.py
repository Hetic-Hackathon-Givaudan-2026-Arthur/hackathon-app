import asyncio

from application.ports.task_queue import TaskQueue
from pipelines.visual.service import VisualPipelineService


class VisualWorker:
    """Consume visual tasks sequentially and acknowledge durable results."""

    def __init__(
        self,
        task_queue: TaskQueue,
        pipeline: VisualPipelineService,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._task_queue = task_queue
        self._pipeline = pipeline
        self._poll_interval_seconds = poll_interval_seconds

    async def run_once(self) -> bool:
        """Process the oldest available task and report whether work was done."""
        task = await self._task_queue.dequeue()
        if task is None:
            return False
        await self._pipeline.run(task)
        return True

    async def run_forever(self) -> None:
        """Consume tasks in FIFO order until the worker is cancelled."""
        while True:
            processed = await self.run_once()
            if not processed:
                await asyncio.sleep(self._poll_interval_seconds)
