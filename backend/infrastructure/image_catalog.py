import json
import logging
import math
import os
from typing import Protocol

from domain.analysis.entities import ImageRequest, VisualQuery
from infrastructure.ollama_image_models import OllamaImageCaptioner, OllamaTextEmbedder
from infrastructure.s3_storage import S3ObjectStore

logger = logging.getLogger(__name__)
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class TextEmbedder(Protocol):
    """Create vectors for search queries and image captions."""

    async def embed(self, text: str) -> list[float]:
        """Return a semantic embedding for text."""
        ...


class ImageCaptioner(Protocol):
    """Describe image content before it is added to the vector index."""

    async def caption(self, image: bytes, content_type: str) -> str:
        """Return a concise semantic description of an image."""
        ...


class S3ImageCatalog:
    """Index image captions as vectors in S3 and rank them by cosine similarity."""

    def __init__(
        self,
        store: S3ObjectStore,
        bucket: str,
        captioner: ImageCaptioner,
        embedder: TextEmbedder,
        prefix: str = "",
        index_key: str = "uploads/.image-vectors.json",
    ) -> None:
        """Initialize the object store and local Ollama model adapters."""
        self._store = store
        self._bucket = bucket
        self._captioner = captioner
        self._embedder = embedder
        self._prefix = prefix
        self._index_key = index_key

    @classmethod
    def from_env(cls) -> "S3ImageCatalog":
        """Compose image indexing with the configured bucket and Ollama models."""
        bucket = os.environ.get("ASSETS_BUCKET")
        if not bucket:
            raise RuntimeError("ASSETS_BUCKET is required for image search")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return cls(
            store=S3ObjectStore.from_env(),
            bucket=bucket,
            captioner=OllamaImageCaptioner(
                base_url,
                os.environ.get("OLLAMA_VISION_MODEL", "mimo-v2.6"),
            ),
            embedder=OllamaTextEmbedder(
                base_url,
                os.environ.get("OLLAMA_EMBEDDING_MODEL", "embeddinggemma"),
            ),
            prefix=os.environ.get("ASSETS_PREFIX", ""),
            index_key=os.environ.get(
                "ASSETS_VECTOR_INDEX_KEY", "uploads/.image-vectors.json"
            ),
        )

    async def find(
        self, query: VisualQuery, references: list[str]
    ) -> list[ImageRequest]:
        """Update the S3 vector index and return its highest-scoring image."""
        query_text = " ".join(dict.fromkeys([query.query, *references])).strip()
        if not query_text:
            return []

        query_vector = await self._embedder.embed(query_text)
        _validate_vector(query_vector)
        objects = await self._store.list_objects(self._bucket, self._prefix)
        index, changed = await self._load_index(objects)
        image_keys = {
            item.get("Key", "")
            for item in objects
            if _is_image_key(item.get("Key", ""))
        }
        logger.info(
            "visual.image_catalog.scanned prefix=%s object_count=%d image_count=%d",
            self._prefix,
            len(objects),
            len(image_keys),
        )
        stale_keys = set(index) - image_keys
        if stale_keys:
            for key in stale_keys:
                del index[key]
            changed = True

        for item in objects:
            key = item.get("Key", "")
            if not _is_image_key(key):
                continue
            etag = item.get("ETag", "")
            saved = index.get(key)
            if saved is not None and saved.get("etag") == etag:
                continue

            content_type = item.get("ContentType") or _content_type(key)
            image_data = await self._store.get_bytes(self._bucket, key)
            caption = await self._captioner.caption(image_data, content_type)
            vector = await self._embedder.embed(caption)
            _validate_vector(vector)
            index[key] = {
                "etag": etag,
                "caption": caption,
                "embedding": vector,
                "content_type": content_type,
            }
            changed = True
            logger.info("visual.image.indexed image_id=%s", key)

        if changed:
            await self._save_index(index)

        ranked = []
        for key, entry in index.items():
            if not key.startswith(self._prefix) or not _is_image_key(key):
                continue
            score = _cosine_similarity(query_vector, entry["embedding"])
            ranked.append((score, key, entry))
        ranked.sort(key=lambda result: result[0], reverse=True)

        requests = [
            ImageRequest(
                image_id=key,
                source_url=f"s3://{self._bucket}/{key}",
                content_type=entry["content_type"],
            )
            for _, key, entry in ranked[:1]
        ]
        logger.info(
            "visual.vector_search.completed indexed_count=%d result_count=%d",
            len(index),
            len(requests),
        )
        return requests

    async def _load_index(
        self, objects: list[dict]
    ) -> tuple[dict[str, dict], bool]:
        """Load the persisted vector index or create an empty one."""
        if not any(item.get("Key") == self._index_key for item in objects):
            return {}, False
        payload = json.loads(
            await self._store.get_bytes(self._bucket, self._index_key)
        )
        if (
            not isinstance(payload, dict)
            or payload.get("version") != 1
            or not isinstance(payload.get("items"), dict)
        ):
            raise ValueError(f"Invalid image vector index: {self._index_key}")
        return payload["items"], False

    async def _save_index(self, index: dict[str, dict]) -> None:
        """Persist image captions and vectors as a JSON object in S3."""
        payload = json.dumps(
            {"version": 1, "items": index},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        await self._store.put_bytes(
            self._bucket,
            self._index_key,
            payload,
            "application/json",
        )


def _is_image_key(key: str) -> bool:
    """Check whether an object key has a supported image extension."""
    return os.path.splitext(key.lower())[1] in _IMAGE_EXTENSIONS


def _content_type(key: str) -> str:
    """Infer an image MIME type from its object key extension."""
    extension = os.path.splitext(key.lower())[1]
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(extension, "application/octet-stream")


def _validate_vector(vector: list[float]) -> None:
    """Reject malformed vectors before persisting or comparing embeddings."""
    if not vector or any(not math.isfinite(value) for value in vector):
        raise ValueError("Embedding model returned an invalid vector")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two vectors with matching dimensions."""
    if len(left) != len(right):
        raise ValueError("Embedding vectors have different dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
