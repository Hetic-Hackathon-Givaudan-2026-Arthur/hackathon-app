from abc import ABC, abstractmethod
from domain.analysis.entities import Batch, AnalysisResult


class AnalysisModel(ABC):
    @abstractmethod
    async def analyze(self, batch: Batch) -> AnalysisResult: ...
