from application.ports.result_delivery import ResultDelivery
from application.ports.event_publisher import EventPublisher
from domain.analysis.entities import AnalysisResult
from domain.events import AnalysisCompleted


class TextPipelineService:
    def __init__(self, delivery: ResultDelivery, publisher: EventPublisher) -> None:
        self._delivery = delivery
        self._publisher = publisher

    async def run(self, result: AnalysisResult) -> None:
        await self._delivery.send_text(result)
        await self._publisher.publish(AnalysisCompleted(result=result))
