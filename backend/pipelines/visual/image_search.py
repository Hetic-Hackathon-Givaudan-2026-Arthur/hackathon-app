from abc import ABC, abstractmethod
from typing import Protocol

from domain.analysis.entities import ImageRef, ImageRequest, VisualQuery


class ImageCatalog(Protocol):
    """Provide image candidates selected by the configured search index."""

    async def find(
        self, query: VisualQuery, references: list[str]
    ) -> list[ImageRequest]:
        """Find persisted image requests matching the visual query."""
        ...


class ImageSearchService(ABC):
    @abstractmethod
    async def search(
        self, query: VisualQuery, references: list[str]
    ) -> list[ImageRequest]:
        """Find image requests without downloading image content."""
        ...


class CatalogImageSearchService(ImageSearchService):
    """Search an image catalog and return requests for image retrieval."""

    def __init__(self, catalog: ImageCatalog) -> None:
        """Initialize the service with its database catalog port."""
        self._catalog = catalog

    async def search(
        self, query: VisualQuery, references: list[str]
    ) -> list[ImageRequest]:
        """Return persisted image requests matching the visual query."""
        return await self._catalog.find(query, references)


class ImageFetcher(ABC):
    """Retrieve image bytes after the database search has selected them."""

    @abstractmethod
    async def fetch(self, request: ImageRequest) -> ImageRef:
        """Download and normalize one selected image."""
        ...
