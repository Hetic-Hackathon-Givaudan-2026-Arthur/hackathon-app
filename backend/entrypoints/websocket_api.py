from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
import logging
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from application.commands import IngestSegmentCommand
from application.orchestrator import Orchestrator
from composition.dependencies import WebSocketManager, build_local_orchestrator

router = APIRouter()
websocket_manager = WebSocketManager()
logger = logging.getLogger(__name__)


class SegmentPayload(BaseModel):
    """Validate the external WebSocket payload before creating a command."""

    model_config = ConfigDict(extra="forbid")

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


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Receive segments, validate them, and forward internal commands."""
    await websocket.accept()
    websocket_manager.register(session_id, websocket)
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

            command = IngestSegmentCommand(
                session_id=session_id, segment_id=payload.segment_id, text=payload.text
            )
            logger.info(
                "websocket.segment.received session_id=%s segment_id=%s",
                session_id,
                payload.segment_id,
            )
            await orchestrator.handle(command)
    except WebSocketDisconnect:
        pass
    finally:
        websocket_manager.unregister(session_id)


app = FastAPI()
app.state.orchestrator = build_local_orchestrator(websocket_manager)
app.include_router(router)
