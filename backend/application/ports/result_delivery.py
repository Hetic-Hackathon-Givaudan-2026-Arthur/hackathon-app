from abc import ABC, abstractmethod
from domain.analysis.entities import AnalysisResult, VisualResult


class ResultDelivery(ABC):
    @abstractmethod
    async def send_text(self, result: AnalysisResult) -> None: ...

    @abstractmethod
    async def send_visual(self, result: VisualResult) -> None: ...
