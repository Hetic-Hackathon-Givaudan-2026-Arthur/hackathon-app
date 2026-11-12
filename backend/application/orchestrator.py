from application.commands import IngestSegmentCommand
from application.ports.analysis_model import AnalysisModel
from application.ports.event_publisher import EventPublisher
from application.ports.task_queue import TaskQueue
from application.ports.result_delivery import ResultDelivery
from domain.analysis.entities import Batch, VisualTask
from domain.analysis.policies import BatchPolicy
from domain.events import AnalysisCompleted, VisualTaskQueued
import uuid


class Orchestrator:
    def __init__(
        self,
        analysis_model: AnalysisModel,
        event_publisher: EventPublisher,
        task_queue: TaskQueue,
        result_delivery: ResultDelivery,
        batch_policy: BatchPolicy,
    ) -> None:
        self._analysis_model = analysis_model
        self._event_publisher = event_publisher
        self._task_queue = task_queue
        self._result_delivery = result_delivery
        self._batch_policy = batch_policy
        self._batches: dict[str, Batch] = {}

    async def handle(self, command: IngestSegmentCommand) -> None:
        batch = self._batch_policy.accumulate(self._batches, command)
        if not self._batch_policy.should_flush(batch):
            return

        result = await self._analysis_model.analyze(batch)
        result.analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"

        await self._event_publisher.publish(AnalysisCompleted(result=result))
        await self._result_delivery.send_text(result)

        task = VisualTask(analysis_id=result.analysis_id, context=result)
        await self._task_queue.enqueue(task)
        await self._event_publisher.publish(VisualTaskQueued(task=task))

        self._batch_policy.reset(self._batches, command.session_id)
