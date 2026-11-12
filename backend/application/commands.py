from dataclasses import dataclass


@dataclass(frozen=True)
class IngestSegmentCommand:
    session_id: str
    segment_id: str
    text: str
