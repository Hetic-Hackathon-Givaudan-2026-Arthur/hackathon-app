from urllib.parse import urlparse

from domain.analysis.entities import ImageRef, ImageRequest
from infrastructure.s3_storage import S3ObjectStore
from pipelines.visual.image_search import ImageFetcher


class S3ImageFetcher(ImageFetcher):
    """Retrieve image bytes selected by the object-storage catalog."""

    def __init__(self, store: S3ObjectStore) -> None:
        """Initialize the fetcher with the S3 object store."""
        self._store = store

    async def fetch(self, request: ImageRequest) -> ImageRef:
        """Fetch an s3://bucket/key request for WebSocket delivery."""
        parsed = urlparse(request.source_url)
        if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
            raise ValueError(
                f"Image source must be an s3://bucket/key URL: {request.source_url}"
            )
        data = await self._store.get_bytes(parsed.netloc, parsed.path.lstrip("/"))
        return ImageRef(
            image_id=request.image_id,
            content_type=request.content_type,
            byte_length=len(data),
            data=data,
        )
