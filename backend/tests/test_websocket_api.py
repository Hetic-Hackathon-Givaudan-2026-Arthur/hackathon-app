import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from entrypoints.websocket_api import create_app, router
from domain.analysis.entities import ImageRef, ImageRequest, VisualQuery
from pipelines.visual.service import VisualPipelineService


class AnalysisWebSocketContractTest(unittest.TestCase):
    """Verify the single analysis WebSocket request and response contract."""

    def test_analysis_route_accepts_segments_and_returns_text_result(self):
        """Validate five segments, one analysis result, and a queued visual task."""
        app = create_app(start_visual_worker=False)
        routes = [route.path for route in router.routes]
        self.assertEqual(routes, ["/ws/analyse"])

        with TestClient(app) as client:
            with client.websocket_connect("/ws/analyse") as websocket:
                websocket.send_json(
                    {
                        "type": "transcript",
                        "text": "old request format",
                        "isFinal": True,
                        "sessionId": "session-1",
                    }
                )
                self.assertEqual(
                    websocket.receive_json()["code"], "invalid_segment"
                )

                for number in range(1, 6):
                    websocket.send_json(
                        {
                            "session_id": "session-1",
                            "segment_id": f"segment-{number}",
                            "text": f"confirmed segment {number}",
                        }
                    )

                result = websocket.receive_json()
                self.assertEqual(result["event"], "analysis_result")
                self.assertEqual(result["session_id"], "session-1")
                self.assertIn("analysis_id", result["analysis"])
                self.assertEqual(
                    len(result["analysis"]["text"]["details"]), 5
                )

            task = asyncio.run(app.state.task_queue.dequeue())
            self.assertIsNotNone(task)
            self.assertEqual(task.context.session_id, "session-1")

    def test_visual_result_uses_the_same_analysis_socket(self):
        """Run mocked LLM2, RAG, search, fetch, and delivery in sequence."""
        trace = []

        class FakeVisualModel:
            """Produce a visual query from the completed text analysis."""

            async def build_query(self, result):
                """Record the LLM2 stage and return its deterministic query."""
                trace.append("llm2")
                return VisualQuery(result.analysis_id, "best matching image")

        class FakeRAG:
            """Provide one reference for the visual search."""

            async def retrieve(self, query):
                """Record RAG and return a deterministic reference."""
                trace.append("rag")
                return ["reference"]

        class FakeImageSearch:
            """Select the single best matching image request."""

            async def search(self, query, references):
                """Record vector search and return one matching image."""
                self_query = query.query
                if self_query != "best matching image" or references != ["reference"]:
                    raise AssertionError("visual search received an invalid query")
                trace.append("search")
                return [
                    ImageRequest(
                        "best-image",
                        "s3://assets/best-image.webp",
                        "image/webp",
                    )
                ]

        class FakeImageFetcher:
            """Return deterministic image bytes for the selected request."""

            async def fetch(self, request):
                """Record retrieval and return the image transport payload."""
                if request.image_id != "best-image":
                    raise AssertionError("unexpected image selected")
                trace.append("fetch")
                data = b"fake-image"
                return ImageRef(
                    request.image_id,
                    request.content_type,
                    len(data),
                    data,
                )

        class FakePublisher:
            """Satisfy the visual pipeline's event publisher port."""

            async def publish(self, event):
                """No-op because this test verifies WebSocket delivery."""

        class RecordingDelivery:
            """Record delivery while forwarding through the real outbox adapter."""

            def __init__(self, delivery):
                """Store the real adapter used by the analysis socket."""
                self._delivery = delivery

            async def send_visual(self, result):
                """Send the visual result and record the successful stage."""
                trace.append("delivery")
                await self._delivery.send_visual(result)

        class RecordingQueue:
            """Record the acknowledgement performed after delivery."""

            def __init__(self, queue):
                """Store the application's task queue."""
                self._queue = queue

            async def ack(self, task_id):
                """Acknowledge the task only after the image has been sent."""
                trace.append("ack")
                await self._queue.ack(task_id)

        def build_pipeline(queue, delivery):
            """Compose the real visual pipeline around deterministic adapters."""
            return VisualPipelineService(
                visual_model=FakeVisualModel(),
                rag=FakeRAG(),
                image_search=FakeImageSearch(),
                image_fetcher=FakeImageFetcher(),
                delivery=RecordingDelivery(delivery),
                publisher=FakePublisher(),
                task_queue=RecordingQueue(queue),
            )

        with patch(
            "entrypoints.websocket_api.build_local_visual_pipeline",
            side_effect=build_pipeline,
        ):
            app = create_app()
            with TestClient(app) as client:
                with client.websocket_connect("/ws/analyse") as websocket:
                    for number in range(1, 6):
                        websocket.send_json(
                            {
                                "session_id": "session-2",
                                "segment_id": f"segment-{number}",
                                "text": f"confirmed segment {number}",
                            }
                        )

                    text_result = websocket.receive_json()
                    visual_result = websocket.receive_json()
                    image_bytes = websocket.receive_bytes()

        self.assertEqual(text_result["event"], "analysis_result")
        self.assertEqual(visual_result["event"], "visual_result")
        self.assertEqual(
            visual_result["analysis"]["analysis_id"],
            text_result["analysis"]["analysis_id"],
        )
        self.assertEqual(
            visual_result["analysis"]["images"][0]["byte_length"],
            len(image_bytes),
        )
        self.assertEqual(image_bytes, b"fake-image")
        self.assertEqual(
            trace,
            ["llm2", "rag", "search", "fetch", "delivery", "ack"],
        )