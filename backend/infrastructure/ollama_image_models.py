import asyncio
import base64
import json
from urllib.request import Request, urlopen


class OllamaTextEmbedder:
    """Create text vectors through Ollama's embedding API."""

    def __init__(self, base_url: str, model: str) -> None:
        """Configure the Ollama embedding endpoint and model."""
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def embed(self, text: str) -> list[float]:
        """Return the embedding for a visual query or generated image caption."""
        response = await _post_json(
            f"{self._base_url}/api/embed",
            {"model": self._model, "input": text},
            timeout=120,
        )
        embeddings = response["embeddings"]
        if not embeddings:
            raise ValueError("Ollama returned no embedding")
        return embeddings[0]


class OllamaImageCaptioner:
    """Describe image content using an Ollama vision model."""

    def __init__(self, base_url: str, model: str) -> None:
        """Configure the Ollama vision endpoint and model."""
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def caption(self, image: bytes, content_type: str) -> str:
        """Generate a concise semantic description for vector indexing."""
        image_base64 = base64.b64encode(image).decode("ascii")
        response = await _post_json(
            f"{self._base_url}/api/chat",
            {
                "model": self._model,
                "stream": False,
                "think": False,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Describe the visible content and style of this image "
                            "in a concise sentence for semantic image search."
                        ),
                        "images": [image_base64],
                    }
                ],
                "options": {"temperature": 0.1},
            },
            timeout=180,
        )
        caption = response["message"]["content"].strip()
        if not caption:
            raise ValueError("Ollama vision model returned an empty caption")
        return caption


async def _post_json(url: str, payload: dict, timeout: int) -> dict:
    """POST JSON to Ollama without requiring an additional HTTP package."""
    def send_request() -> dict:
        """Send a blocking standard-library HTTP request in a worker thread."""
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())

    return await asyncio.to_thread(send_request)
