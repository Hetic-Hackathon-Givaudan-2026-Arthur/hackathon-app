from dataclasses import dataclass, field
from datetime import datetime, UTC
from domain.analysis.entities import AnalysisResult, VisualTask


@dataclass
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TranscriptReceived(DomainEvent):
    session_id: str = ""
    segment_id: str = ""


@dataclass
class BatchCreated(DomainEvent):
    session_id: str = ""
    segment_count: int = 0


@dataclass
class AnalysisStarted(DomainEvent):
    session_id: str = ""


@dataclass
class AnalysisCompleted(DomainEvent):
    result: AnalysisResult | None = None


@dataclass
class VisualTaskQueued(DomainEvent):
    task: VisualTask | None = None


@dataclass
class ProcessingFailed(DomainEvent):
    reason: str = ""
    retryable: bool = True
