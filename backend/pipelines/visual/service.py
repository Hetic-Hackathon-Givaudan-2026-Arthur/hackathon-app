from application.ports.visual_model import VisualModel
from application.ports.result_delivery import ResultDelivery
from application.ports.event_publisher import EventPublisher
from application.ports.task_queue import TaskQueue
from domain.analysis.entities import VisualTask, VisualResult
from domain.events import VisualTaskQueued
from pipelines.visual.rag import RAGRetriever
from pipelines.visual.image_search import ImageSearchService


class VisualPipelineService:
    def __init__(
        self,
        visual_model: VisualModel,
        rag: RAGRetriever,
        image_search: ImageSearchService,
        delivery: ResultDelivery,
        publisher: EventPublisher,
        task_queue: TaskQueue,
    ) -> None:
        self._visual_model = visual_model
        self._rag = rag
        self._image_search = image_search
        self._delivery = delivery
        self._publisher = publisher
        self._task_queue = task_queue

    async def run(self, task: VisualTask) -> None:
        query = await self._visual_model.build_query(task.context)
        references = await self._rag.retrieve(query)
        images = await self._image_search.search(query, references)

        result = VisualResult(
            analysis_id=task.analysis_id,
            session_id=task.context.session_id,
            images=images,
        )
        await self._delivery.send_visual(result)
        await self._task_queue.ack(task.task_id)
