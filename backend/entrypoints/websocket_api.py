import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from application.commands import IngestSegmentCommand
from application.orchestrator import Orchestrator
from composition.dependencies import (
    InMemoryTaskQueue,
    InMemoryOutbox,
    OutboxDelivery,
    WebSocketManager,
    build_local_orchestrator,
    build_local_visual_pipeline,
)
from pipelines.visual.service import VisualPipelineService

router = APIRouter()
logger = logging.getLogger(__name__)


class SegmentPayload(BaseModel):
    """Validate the external WebSocket payload before creating a command."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    segment_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


def _invalid_segment_message(code: str, message: str) -> dict[str, str]:
    """Build the stable error event returned for an invalid segment."""
    return {
        "event": "error",
        "code": code,
        "message": message,
    }


def get_orchestrator(websocket: WebSocket) -> Orchestrator:
    """Retrieve the application service configured during composition."""
    orchestrator = getattr(websocket.app.state, "orchestrator", None)
    if orchestrator is None:
        raise RuntimeError("WebSocket orchestrator is not configured")
    return orchestrator


@router.websocket("/ws/analyse")
async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Receive analysis segments and route all results through this socket."""
    await websocket.accept()
    websocket_manager = websocket.app.state.websocket_manager
    registered_sessions: set[str] = set()
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except ValueError as error:
                await websocket.send_json(
                    _invalid_segment_message("invalid_json", str(error))
                )
                continue

            try:
                payload = SegmentPayload.model_validate(data)
            except ValidationError as error:
                await websocket.send_json(
                    _invalid_segment_message("invalid_segment", str(error))
                )
                continue

            websocket_manager.register(payload.session_id, websocket)
            registered_sessions.add(payload.session_id)
            command = IngestSegmentCommand(
                session_id=payload.session_id,
                segment_id=payload.segment_id,
                text=payload.text,
            )
            logger.info(
                "websocket.segment.received session_id=%s segment_id=%s",
                payload.session_id,
                payload.segment_id,
            )
            await orchestrator.handle(command)
    except WebSocketDisconnect:
        pass
    finally:
        for session_id in registered_sessions:
            websocket_manager.unregister(session_id, websocket)


async def _run_visual_worker(
    queue: InMemoryTaskQueue,
    pipeline: VisualPipelineService,
    websocket_manager: WebSocketManager,
) -> None:
    """Consume visual tasks and deliver their results over the analysis socket."""
    while True:
        task = await queue.wait_for_task()
        try:
            await pipeline.run(task)
        except Exception:
            logger.exception(
                "visual.worker.failed session_id=%s analysis_id=%s",
                task.context.session_id,
                task.analysis_id,
            )
            await websocket_manager.send(
                task.context.session_id,
                {
                    "event": "error",
                    "code": "visual_processing_failed",
                    "message": "Le traitement visuel a échoué.",
                    "analysis_id": task.analysis_id,
                },
            )


def create_app(start_visual_worker: bool = True) -> FastAPI:
    """Compose the single analysis WebSocket and its optional visual worker."""
    websocket_manager = WebSocketManager()
    task_queue = InMemoryTaskQueue()
    delivery = OutboxDelivery(InMemoryOutbox(), websocket_manager)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        """Start and stop the optional visual worker with the application."""
        worker = None
        if start_visual_worker:
            pipeline = build_local_visual_pipeline(task_queue, delivery)
            worker = asyncio.create_task(
                _run_visual_worker(task_queue, pipeline, websocket_manager)
            )
        try:
            yield
        finally:
            if worker is not None:
                worker.cancel()
                try:
                    await worker
                except asyncio.CancelledError:
                    pass

    application = FastAPI(lifespan=lifespan)
    application.state.websocket_manager = websocket_manager
    application.state.task_queue = task_queue
    application.state.orchestrator = build_local_orchestrator(
        websocket_manager,
        task_queue=task_queue,
        result_delivery=delivery,
    )
    application.include_router(router)
    return application


app = create_app()
