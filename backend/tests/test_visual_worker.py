import unittest
from unittest.mock import AsyncMock

from application.visual_worker import VisualWorker
from domain.analysis.entities import AnalysisResult, VisualTask


class VisualWorkerTests(unittest.IsolatedAsyncioTestCase):
    """Protect FIFO worker processing and empty-queue behavior."""

    async def test_processes_one_task(self) -> None:
        """The worker delegates one task to the visual pipeline."""
        task = VisualTask(
            task_id="task-1",
            analysis_id="analysis-1",
            context=AnalysisResult("analysis-1", "session-1", "idea"),
        )
        queue = AsyncMock()
        queue.dequeue.return_value = task
        pipeline = AsyncMock()
        worker = VisualWorker(queue, pipeline)

        processed = await worker.run_once()

        self.assertTrue(processed)
        pipeline.run.assert_awaited_once_with(task)

    async def test_reports_empty_queue(self) -> None:
        """The worker reports no work when Neon has no pending task."""
        queue = AsyncMock()
        queue.dequeue.return_value = None
        worker = VisualWorker(queue, AsyncMock())

        processed = await worker.run_once()

        self.assertFalse(processed)
