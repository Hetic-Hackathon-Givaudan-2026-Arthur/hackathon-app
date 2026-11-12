from application.commands import IngestSegmentCommand
from domain.analysis.entities import Batch, Segment

BATCH_SIZE_THRESHOLD = 5


class BatchPolicy:
    def accumulate(self, batches: dict[str, Batch], command: IngestSegmentCommand) -> Batch:
        """Add a segment once to the session batch."""
        batch = batches.setdefault(command.session_id, Batch(session_id=command.session_id))
        segment = Segment(
            session_id=command.session_id,
            segment_id=command.segment_id,
            text=command.text,
        )
        # idempotence: skip duplicate segment_ids
        if not any(s.segment_id == segment.segment_id for s in batch.segments):
            batch.segments.append(segment)
        return batch

    def should_flush(self, batch: Batch, is_final: bool = False) -> bool:
        """Flush when the batch reaches its threshold or the transcript ends."""
        return is_final or len(batch.segments) >= BATCH_SIZE_THRESHOLD

    def reset(self, batches: dict[str, Batch], session_id: str) -> None:
        """Remove the completed session batch from the in-memory buffer."""
        batches.pop(session_id, None)
