from abc import ABC, abstractmethod
from domain.analysis.entities import AnalysisResult, VisualQuery


class VisualModel(ABC):
    @abstractmethod
    async def build_query(self, result: AnalysisResult) -> VisualQuery: ...
