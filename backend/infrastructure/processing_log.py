from datetime import datetime, UTC
from domain.events import DomainEvent


class ProcessingLog:
    """Append-only log of processing events for traceability."""

    def __init__(self, store) -> None:
        self._store = store

    async def record(self, event: DomainEvent) -> None:
        entry = {
            "event_type": type(event).__name__,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": vars(event),
        }
        await self._store.append(entry)
