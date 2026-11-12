from abc import ABC, abstractmethod
from domain.analysis.entities import VisualTask


class TaskQueue(ABC):
    @abstractmethod
    async def enqueue(self, task: VisualTask) -> None: ...

    @abstractmethod
    async def dequeue(self) -> VisualTask | None: ...

    @abstractmethod
    async def ack(self, task_id: str) -> None: ...
