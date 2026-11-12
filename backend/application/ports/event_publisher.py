from abc import ABC, abstractmethod
from domain.events import DomainEvent


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...
