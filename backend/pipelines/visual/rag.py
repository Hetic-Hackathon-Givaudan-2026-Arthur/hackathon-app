from abc import ABC, abstractmethod
from domain.analysis.entities import VisualQuery


class RAGRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: VisualQuery) -> list[str]:
        """Return a list of visual reference descriptions or identifiers."""
        ...
