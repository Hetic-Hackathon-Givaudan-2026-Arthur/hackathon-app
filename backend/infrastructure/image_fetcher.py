import httpx

from domain.analysis.entities import ImageRef, ImageRequest
from pipelines.visual.image_search import ImageFetcher


class HttpImageFetcher(ImageFetcher):
    """Download selected image requests before visual delivery."""

    async def fetch(self, request: ImageRequest) -> ImageRef:
        """Fetch one image and return the bytes expected by the WebSocket outbox."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.source_url)
            response.raise_for_status()
        return ImageRef(
            image_id=request.image_id,
            content_type=request.content_type or response.headers.get(
                "content-type", "application/octet-stream"
            ),
            byte_length=len(response.content),
            data=response.content,
        )
