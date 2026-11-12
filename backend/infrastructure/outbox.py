import json
from datetime import datetime, UTC
from application.ports.result_delivery import ResultDelivery
from domain.analysis.entities import AnalysisResult, VisualResult


class OutboxDelivery(ResultDelivery):
    """Persists results before sending; supports replay on reconnect."""

    def __init__(self, store, websocket_manager) -> None:
        self._store = store
        self._ws = websocket_manager

    async def send_text(self, result: AnalysisResult) -> None:
        entry = {
            "event": "analysis_result",
            "session_id": result.session_id,
            "analysis": {
                "analysis_id": result.analysis_id,
                "text": {"idea": result.idea, "details": result.details},
            },
            "queued_at": datetime.now(UTC).isoformat(),
            "sent": False,
        }
        await self._store.save(entry)
        await self._ws.send(result.session_id, entry)
        await self._store.mark_sent(entry)

    async def send_visual(self, result: VisualResult) -> None:
        control = {
            "event": "visual_result",
            "session_id": result.session_id,
            "analysis": {
                "analysis_id": result.analysis_id,
                "images": [
                    {
                        "image_id": img.image_id,
                        "content_type": img.content_type,
                        "byte_length": img.byte_length,
                    }
                    for img in result.images
                ],
            },
            "queued_at": datetime.now(UTC).isoformat(),
            "sent": False,
        }
        await self._store.save(control)
        await self._ws.send(result.session_id, control)
        for img in result.images:
            await self._ws.send_bytes(result.session_id, img.data)
        await self._store.mark_sent(control)
