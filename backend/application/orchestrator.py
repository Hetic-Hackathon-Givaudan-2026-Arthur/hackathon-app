from application.commands import IngestSegmentCommand
from application.ports.analysis_model import AnalysisModel
from application.ports.event_publisher import EventPublisher
from application.ports.task_queue import TaskQueue
from application.ports.result_delivery import ResultDelivery
from domain.analysis.entities import Batch, VisualTask
from domain.analysis.policies import BatchPolicy
from domain.events import (
    AnalysisCompleted,
    AnalysisStarted,
    BatchCreated,
    ProcessingFailed,
    TranscriptReceived,
    VisualTaskQueued,
)
import logging
import uuid

logger = logging.getLogger(__name__)


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
        self._completed_segments: dict[str, set[str]] = {}

    async def handle(self, command: IngestSegmentCommand) -> None:
        """Coordinate one segment through analysis, text delivery, and visual queuing."""
        completed_segments = self._completed_segments.setdefault(command.session_id, set())
        if command.segment_id in completed_segments:
            logger.info(
                "segment.duplicate session_id=%s segment_id=%s",
                command.session_id,
                command.segment_id,
            )
            return

        existing_batch = self._batches.get(command.session_id)
        is_new_segment = existing_batch is None or not any(
            segment.segment_id == command.segment_id
            for segment in existing_batch.segments
        )
        if existing_batch and any(
            segment.segment_id == command.segment_id
            for segment in existing_batch.segments
        ) and not self._batch_policy.should_flush(existing_batch):
            return

        batch = self._batch_policy.accumulate(self._batches, command)
        logger.info(
            "segment.accepted session_id=%s segment_id=%s batch_size=%d",
            command.session_id,
            command.segment_id,
            len(batch.segments),
        )

        if is_new_segment:
            await self._event_publisher.publish(
                TranscriptReceived(
                    session_id=command.session_id,
                    segment_id=command.segment_id,
                )
            )
        if not self._batch_policy.should_flush(batch):
            return

        logger.info(
            "batch.ready session_id=%s segment_count=%d",
            batch.session_id,
            len(batch.segments),
        )
        await self._event_publisher.publish(
            BatchCreated(
                session_id=batch.session_id,
                segment_count=len(batch.segments),
            )
        )
        await self._event_publisher.publish(
            AnalysisStarted(session_id=batch.session_id)
        )

        try:
            result = await self._analysis_model.analyze(batch)
            result.analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
            logger.info(
                "analysis.id_assigned session_id=%s analysis_id=%s",
                result.session_id,
                result.analysis_id,
            )

            await self._event_publisher.publish(AnalysisCompleted(result=result))
            await self._result_delivery.send_text(result)
            logger.info(
                "text.delivered session_id=%s analysis_id=%s",
                result.session_id,
                result.analysis_id,
            )

            task = VisualTask(
                analysis_id=result.analysis_id,
                context=result,
                task_id=f"task_{result.analysis_id.removeprefix('analysis_')}",
            )
            await self._task_queue.enqueue(task)
            await self._event_publisher.publish(VisualTaskQueued(task=task))
            logger.info(
                "visual.task.published session_id=%s analysis_id=%s task_id=%s",
                result.session_id,
                result.analysis_id,
                task.task_id,
            )
        except Exception as error:
            logger.exception(
                "processing.failed session_id=%s segment_id=%s",
                command.session_id,
                command.segment_id,
            )
            await self._event_publisher.publish(
                ProcessingFailed(reason=str(error), retryable=True)
            )
            raise
        else:
            completed_segments.update(
                segment.segment_id for segment in batch.segments
            )
            self._batch_policy.reset(self._batches, command.session_id)
