from collections import deque
import logging
import os

from application.orchestrator import Orchestrator
from application.ports.analysis_model import AnalysisModel
from application.ports.task_queue import TaskQueue
from domain.analysis.entities import AnalysisResult, Batch, VisualTask
from domain.analysis.policies import BatchPolicy
from infrastructure.ollama_client import OllamaClient
from infrastructure.outbox import OutboxDelivery
from infrastructure.image_catalog import S3ImageCatalog
from infrastructure.s3_image_fetcher import S3ImageFetcher
from infrastructure.s3_storage import S3ObjectStore
from llm.llm2_visual.adapter import LLM2Adapter
from llm.llm2_visual.service import LLM2VisualService

logger = logging.getLogger(__name__)


class LocalAnalysisModel(AnalysisModel):
    """Produce deterministic analysis results for local WebSocket simulations."""

    async def analyze(self, batch: Batch) -> AnalysisResult:
        """Convert the batch segments into the local analysis result."""
        logger.info(
            "analysis.started session_id=%s segment_count=%d",
            batch.session_id,
            len(batch.segments),
        )
        text = " ".join(segment.text for segment in batch.segments)
        logger.info("analysis.completed session_id=%s", batch.session_id)
        return AnalysisResult(
            analysis_id="",
            session_id=batch.session_id,
            idea=text,
            details=[segment.text for segment in batch.segments],
        )


class InMemoryTaskQueue(TaskQueue):
    """Keep visual tasks in FIFO order without an external service."""

    def __init__(self) -> None:
        """Initialize the in-memory FIFO queue."""
        self._tasks: deque[VisualTask] = deque()

    async def enqueue(self, task: VisualTask) -> None:
        """Add a visual task to the end of the queue."""
        self._tasks.append(task)
        logger.info("visual.task.queued task_id=%s", task.task_id)

    async def dequeue(self) -> VisualTask | None:
        """Remove and return the oldest visual task, if any."""
        return self._tasks.popleft() if self._tasks else None

    async def ack(self, task_id: str) -> None:
        """Acknowledge a task already removed from the local queue."""
        return None


class WebSocketManager:
    """Track active WebSockets and deliver analysis events to their sessions."""

    def __init__(self) -> None:
        """Initialize the active connection registry."""
        self._connections = {}

    def register(self, session_id: str, websocket) -> None:
        """Associate a WebSocket with its analysis session."""
        self._connections[session_id] = websocket
        logger.info("websocket.connected session_id=%s", session_id)

    def unregister(self, session_id: str) -> None:
        """Remove a session's WebSocket from the registry."""
        self._connections.pop(session_id, None)
        logger.info("websocket.disconnected session_id=%s", session_id)

    async def send(self, session_id: str, message: dict) -> None:
        """Send a JSON event to a connected session when available."""
        websocket = self._connections.get(session_id)
        if websocket is not None:
            await websocket.send_json(message)
            logger.info(
                "websocket.sent session_id=%s event=%s",
                session_id,
                message.get("event"),
            )

    async def send_bytes(self, session_id: str, data: bytes) -> None:
        """Send binary data to a connected session when available."""
        websocket = self._connections.get(session_id)
        if websocket is not None:
            await websocket.send_bytes(data)


class InMemoryOutbox:
    """Store delivered events in memory for the local simulation."""

    def __init__(self) -> None:
        """Initialize the collection of outbox entries."""
        self.entries = []

    async def save(self, entry: dict) -> None:
        """Persist an event in the local outbox."""
        self.entries.append(entry)
        logger.info(
            "outbox.queued session_id=%s event=%s",
            entry.get("session_id"),
            entry.get("event"),
        )

    async def mark_sent(self, entry: dict) -> None:
        """Mark an outbox event as delivered."""
        entry["sent"] = True
        logger.info(
            "outbox.sent session_id=%s event=%s",
            entry.get("session_id"),
            entry.get("event"),
        )


class _NoopPublisher:
    """Ignore internal events when no processing log is configured."""

    async def publish(self, event) -> None:
        """Discard an internal event in local mode."""
        return None


def build_local_orchestrator(ws_manager: WebSocketManager) -> Orchestrator:
    """Compose the dependency-free orchestrator used by the local WebSocket."""
    logger.info("orchestrator.composed mode=local")
    return Orchestrator(
        analysis_model=LocalAnalysisModel(),
        event_publisher=_NoopPublisher(),
        task_queue=InMemoryTaskQueue(),
        result_delivery=OutboxDelivery(InMemoryOutbox(), ws_manager),
        batch_policy=BatchPolicy(),
    )


def build_local_visual_model() -> LLM2VisualService:
    """Compose LLM 2 with the configured local Ollama model."""
    client = OllamaClient(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.environ.get("LLM2_MODEL", "qwen2.5:1.5b"),
    )
    return LLM2VisualService(LLM2Adapter(client))


def build_s3_image_catalog() -> S3ImageCatalog:
    """Compose the captioned vector image catalog from environment configuration."""
    return S3ImageCatalog.from_env()


def build_s3_image_fetcher() -> S3ImageFetcher:
    """Compose the S3-backed image fetcher from environment configuration."""
    return S3ImageFetcher(S3ObjectStore.from_env())
