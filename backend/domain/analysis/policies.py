from application.commands import IngestSegmentCommand
from domain.analysis.entities import Batch, Segment

BATCH_SIZE_THRESHOLD = 5


class BatchPolicy:
    def accumulate(self, batches: dict[str, Batch], command: IngestSegmentCommand) -> Batch:
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

    def should_flush(self, batch: Batch) -> bool:
        return len(batch.segments) >= BATCH_SIZE_THRESHOLD

    def reset(self, batches: dict[str, Batch], session_id: str) -> None:
        batches.pop(session_id, None)
