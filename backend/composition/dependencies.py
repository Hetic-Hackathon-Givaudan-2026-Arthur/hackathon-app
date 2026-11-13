import os
from collections import deque
import logging

import redis.asyncio as redis
from infrastructure.ollama_client import OllamaClient
from llm.llm1_analysis.adapter import LLM1Adapter
from llm.llm1_analysis.service import LLM1AnalysisService
from infrastructure.outbox import OutboxDelivery
from infrastructure.processing_log import ProcessingLog

from application.orchestrator import Orchestrator
from application.ports.analysis_model import AnalysisModel
from application.ports.task_queue import TaskQueue
from domain.analysis.entities import AnalysisResult, Batch, VisualTask
from domain.analysis.policies import BatchPolicy
from llm.llm2_visual.adapter import LLM2Adapter
from llm.llm2_visual.service import LLM2VisualService
import json
from pipelines.visual.rag import PassthroughRAGRetriever

logger = logging.getLogger(__name__)


class LocalAnalysisModel(AnalysisModel):
    """Produce a deterministic analysis for local WebSocket simulations."""

    async def analyze(self, batch: Batch) -> AnalysisResult:
        logger.info(
            "analysis.started session_id=%s segment_count=%d",
            batch.session_id,
            len(batch.segments),
        )


class PassthroughLLM2Client:
    """Emulate a direct LLM2 provider while preserving its completion contract."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        payload = messages[-1]["content"]
        return json.dumps({"query": payload})
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
        self._tasks: deque[VisualTask] = deque()

    async def enqueue(self, task: VisualTask) -> None:
        self._tasks.append(task)
        logger.info("visual.task.queued task_id=%s", task.task_id)

    async def dequeue(self) -> VisualTask | None:
        return self._tasks.popleft() if self._tasks else None

    async def ack(self, task_id: str) -> None:
        return None

def build_orchestrator(ws_manager, outbox_store, redis_url: str) -> Orchestrator:
    redis_client = redis.from_url(redis_url)
    llm_client = OllamaClient(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.environ.get("LLM1_MODEL", "qwen2.5:1.5b"),
    )

class WebSocketManager:
    """Track active WebSockets and deliver analysis events to their sessions."""

    def __init__(self) -> None:
        self._connections = {}

    def register(self, session_id: str, websocket) -> None:
        self._connections[session_id] = websocket
        logger.info("websocket.connected session_id=%s", session_id)

    def unregister(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        logger.info("websocket.disconnected session_id=%s", session_id)

    async def send(self, session_id: str, message: dict) -> None:
        websocket = self._connections.get(session_id)
        if websocket is not None:
            await websocket.send_json(message)
            logger.info(
                "websocket.sent session_id=%s event=%s",
                session_id,
                message.get("event"),
            )

    async def send_bytes(self, session_id: str, data: bytes) -> None:
        websocket = self._connections.get(session_id)
        if websocket is not None:
            await websocket.send_bytes(data)


class InMemoryOutbox:
    """Store delivered events in memory for the local simulation."""

    def __init__(self) -> None:
        self.entries = []

    async def save(self, entry: dict) -> None:
        self.entries.append(entry)
        logger.info(
            "outbox.queued session_id=%s event=%s",
            entry.get("session_id"),
            entry.get("event"),
        )

    async def mark_sent(self, entry: dict) -> None:
        entry["sent"] = True
        logger.info(
            "outbox.sent session_id=%s event=%s",
            entry.get("session_id"),
            entry.get("event"),
        )


class _NoopPublisher:
    """Ignore internal events when no processing log is configured."""

    async def publish(self, event) -> None:
        return None


def build_local_orchestrator(ws_manager: WebSocketManager) -> Orchestrator:
    """Compose the dependency-free orchestrator used by the local WebSocket."""
    from infrastructure.outbox import OutboxDelivery

    logger.info("orchestrator.composed mode=local")
    return Orchestrator(
        analysis_model=LocalAnalysisModel(),
        event_publisher=_NoopPublisher(),
        task_queue=InMemoryTaskQueue(),
        result_delivery=OutboxDelivery(InMemoryOutbox(), ws_manager),
        batch_policy=BatchPolicy(),
    )


def build_local_visual_model() -> LLM2VisualService:
    """Compose LLM2 with the local provider-shaped client for development."""
    return LLM2VisualService(LLM2Adapter(PassthroughLLM2Client()))
