from dataclasses import dataclass, field
from typing import Any


@dataclass
class Segment:
    session_id: str
    segment_id: str
    text: str


@dataclass
class Batch:
    session_id: str
    segments: list[Segment] = field(default_factory=list)


@dataclass
class AnalysisResult:
    analysis_id: str
    session_id: str
    idea: str
    details: list[str] = field(default_factory=list)


@dataclass
class VisualQuery:
    analysis_id: str
    query: str


@dataclass
class VisualTask:
    analysis_id: str
    context: AnalysisResult
    task_id: str = ""


@dataclass
class ImageRef:
    image_id: str
    content_type: str
    byte_length: int
    data: bytes = field(default_factory=bytes)


@dataclass
class VisualResult:
    analysis_id: str
    session_id: str
    images: list[ImageRef] = field(default_factory=list)
