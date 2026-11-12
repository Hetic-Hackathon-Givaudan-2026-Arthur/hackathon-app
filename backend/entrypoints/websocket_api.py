from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from application.commands import IngestSegmentCommand
from application.orchestrator import Orchestrator

app = FastAPI()
router = APIRouter()


class SegmentPayload(BaseModel):
    """Validate the external WebSocket payload before creating a command."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(pattern="^transcript$")
    text: str = Field(min_length=1)
    is_final: bool = Field(alias="isFinal")
    session_id: str = Field(alias="sessionId", min_length=1)
    segment_id: str = Field(alias="segmentId", min_length=1)


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


def configure_orchestrator(orchestrator: Orchestrator) -> None:
    """Register the orchestrator assembled by the composition layer."""
    app.state.orchestrator = orchestrator


@router.websocket("/ws/analyse")
async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Receive segments, validate them, and forward internal commands."""
    await websocket.accept()
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
                session_id=payload.session_id,
                segment_id=payload.segment_id,
                text=payload.text,
                is_final=payload.is_final,
            )
            await orchestrator.handle(command)
    except WebSocketDisconnect:
        pass
