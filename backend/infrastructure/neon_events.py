from application.ports.event_publisher import EventPublisher
from domain.events import DomainEvent
from infrastructure.neon_store import NeonStore


class NeonEventPublisher(EventPublisher):
    """Persist domain events in the append-only Neon processing log."""

    def __init__(self, store: NeonStore) -> None:
        self._store = store

    async def publish(self, event: DomainEvent) -> None:
        """Append one domain event without coupling the domain to Neon."""
        await self._store.append(
            {
                "event_type": type(event).__name__,
                "occurred_at": event.occurred_at.isoformat(),
                "payload": vars(event),
            }
        )
