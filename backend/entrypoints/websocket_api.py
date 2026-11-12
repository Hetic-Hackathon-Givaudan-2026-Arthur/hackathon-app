from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from application.commands import IngestSegmentCommand
from application.orchestrator import Orchestrator

app = FastAPI()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, orchestrator: Orchestrator):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            command = IngestSegmentCommand(
                session_id=session_id,
                segment_id=data["segment_id"],
                text=data["text"],
            )
            await orchestrator.handle(command)
    except WebSocketDisconnect:
        pass
