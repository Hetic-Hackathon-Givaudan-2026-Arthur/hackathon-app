from abc import ABC, abstractmethod
from domain.analysis.entities import VisualQuery, ImageRef


class ImageSearchService(ABC):
    @abstractmethod
    async def search(self, query: VisualQuery, references: list[str]) -> list[ImageRef]:
        """Fetch images matching the query and normalize results."""
        ...
