import unittest
from unittest.mock import AsyncMock, patch

from domain.analysis.entities import (
    AnalysisResult,
    ImageRef,
    ImageRequest,
    VisualTask,
)
from pipelines.visual.image_search import CatalogImageSearchService
from pipelines.visual.service import VisualPipelineService
from pipelines.visual.rag import PassthroughRAGRetriever


class FakeCatalog:
    """Return one catalog image request for the pipeline test."""

    async def find(self, query, references):
        """Return a deterministic image request selected by the query."""
        return [
            ImageRequest(
                image_id="image-1",
                source_url="https://images.test/image-1.webp",
                content_type="image/webp",
            )
        ]


class FakeVisualModel:
    """Build a deterministic visual query for the pipeline test."""

    async def build_query(self, result):
        """Convert the analysis result into a visual query."""
        from domain.analysis.entities import VisualQuery

        return VisualQuery(analysis_id=result.analysis_id, query=result.idea)


class FakeImageFetcher:
    """Represent the service that downloads the selected image."""

    async def fetch(self, request):
        """Return the bytes that the front-end delivery service will receive."""
        return ImageRef(
            image_id=request.image_id,
            content_type=request.content_type,
            byte_length=4,
            data=b"test",
        )


class FakeDelivery:
    """Capture the visual message sent to the front-end delivery port."""

    def __init__(self):
        """Initialize the captured visual result."""
        self.result = None

    async def send_visual(self, result):
        """Store the visual result sent by the pipeline."""
        self.result = result


class FakePublisher:
    """Provide the event publisher required by the visual pipeline."""

    async def publish(self, event):
        """Ignore events in this focused pipeline test."""


class FakeQueue:
    """Provide task acknowledgement for the visual pipeline test."""

    def __init__(self):
        """Initialize the acknowledgement capture."""
        self.acknowledged = None

    async def ack(self, task_id):
        """Capture the acknowledged task identifier."""
        self.acknowledged = task_id


class VisualPipelineTest(unittest.IsolatedAsyncioTestCase):
    """Verify catalog selection, image retrieval, and front-end delivery."""

    async def test_catalog_search_then_image_delivery(self):
        """Verify the complete visual handoff and task acknowledgement."""
        catalog_search = CatalogImageSearchService(FakeCatalog())
        delivery = FakeDelivery()
        queue = FakeQueue()
        pipeline = VisualPipelineService(
            visual_model=FakeVisualModel(),
            rag=PassthroughRAGRetriever(),
            image_search=catalog_search,
            image_fetcher=FakeImageFetcher(),
            delivery=delivery,
            publisher=FakePublisher(),
            task_queue=queue,
        )
        task = VisualTask(
            analysis_id="analysis_12345678",
            context=AnalysisResult(
                analysis_id="analysis_12345678",
                session_id="session-1",
                idea="minimal natural",
            ),
            task_id="task_12345678",
        )

        await pipeline.run(task)

        self.assertEqual(delivery.result.analysis_id, task.analysis_id)
        self.assertEqual(delivery.result.images[0].data, b"test")
        self.assertEqual(queue.acknowledged, task.task_id)


class OllamaImageCaptionerTest(unittest.IsolatedAsyncioTestCase):
    """Verify vision captions do not enable extended model reasoning."""

    @patch(
        "infrastructure.ollama_image_models._post_json",
        new_callable=AsyncMock,
    )
    async def test_caption_disables_reasoning(self, post_json):
        """Send a non-thinking request to keep image indexing responsive."""
        from infrastructure.ollama_image_models import OllamaImageCaptioner

        post_json.return_value = {"message": {"content": "A floral image"}}
        captioner = OllamaImageCaptioner("http://localhost:11434", "mimo-v2.6")

        caption = await captioner.caption(b"image", "image/jpeg")

        self.assertEqual(caption, "A floral image")
        self.assertFalse(post_json.await_args.args[1]["think"])


class InMemoryObjectStore:
    """Provide deterministic image and vector-index objects for catalog tests."""

    def __init__(self):
        """Initialize sample image objects and an empty bucket."""
        self.objects = {
            "uploads/flower.jpg": (b"flower", "image/jpeg"),
            "uploads/night.png": (b"night", "image/png"),
        }

    async def list_objects(self, bucket, prefix=""):
        """Return keys and ETags currently stored under the requested prefix."""
        return [
            {"Key": key, "ETag": key}
            for key in self.objects
            if key.startswith(prefix)
        ]

    async def get_bytes(self, bucket, key):
        """Read image or index bytes from the in-memory bucket."""
        return self.objects[key][0]

    async def put_bytes(self, bucket, key, data, content_type):
        """Persist the vector index in the in-memory bucket."""
        self.objects[key] = (data, content_type)


class FakeImageCaptioner:
    """Return captions describing the in-memory image fixtures."""

    def __init__(self):
        """Initialize the image caption counter."""
        self.caption_count = 0

    async def caption(self, image, content_type):
        """Describe fixture images based on their bytes."""
        self.caption_count += 1
        return {
            b"flower": "red flower in a garden",
            b"night": "dark night sky",
        }[image]


class FakeTextEmbedder:
    """Map deterministic image captions and queries to semantic vectors."""

    async def embed(self, text):
        """Return stable vectors for the vector-ranking test."""
        return [1.0, 0.0] if "flower" in text else [0.0, 1.0]


class S3VectorCatalogTest(unittest.IsolatedAsyncioTestCase):
    """Verify image caption indexing and vector-based ranking."""

    async def test_vector_search_ranks_images_and_reuses_persisted_index(self):
        """Verify similarity ordering and S3 index reuse on a second search."""
        from infrastructure.image_catalog import S3ImageCatalog
        from domain.analysis.entities import VisualQuery

        store = InMemoryObjectStore()
        captioner = FakeImageCaptioner()
        catalog = S3ImageCatalog(
            store=store,
            bucket="assets",
            captioner=captioner,
            embedder=FakeTextEmbedder(),
        )
        query = VisualQuery(analysis_id="analysis_12345678", query="flower perfume")

        first_results = await catalog.find(query, [])
        self.assertEqual(len(first_results), 1)
        self.assertEqual(first_results[0].image_id, "uploads/flower.jpg")
        self.assertEqual(captioner.caption_count, 2)

        second_results = await catalog.find(query, [])
        self.assertEqual(len(second_results), 1)
        self.assertEqual(second_results[0].image_id, "uploads/flower.jpg")
        self.assertEqual(captioner.caption_count, 2)
        self.assertIn("uploads/.image-vectors.json", store.objects)
