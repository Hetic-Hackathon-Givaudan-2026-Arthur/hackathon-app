from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("session_id must not be empty")


@dataclass(frozen=True)
class SegmentId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("segment_id must not be empty")


@dataclass(frozen=True)
class AnalysisId:
    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^analysis_[0-9a-f]{8}$", self.value):
            raise ValueError(f"invalid analysis_id format: {self.value}")
