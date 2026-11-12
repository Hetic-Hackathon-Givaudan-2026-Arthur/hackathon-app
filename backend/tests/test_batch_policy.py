import unittest

from application.commands import IngestSegmentCommand
from domain.analysis.entities import Batch
from domain.analysis.policies import BatchPolicy


class BatchPolicyTests(unittest.TestCase):
    """Protect transcript batching and final-segment behavior."""

    def test_final_segment_flushes_before_threshold(self) -> None:
        """A final transcript must not remain buffered."""
        policy = BatchPolicy()
        batch = Batch(session_id="session-1")

        self.assertTrue(policy.should_flush(batch, is_final=True))

    def test_duplicate_segment_is_ignored(self) -> None:
        """A repeated segment id must not duplicate transcript content."""
        policy = BatchPolicy()
        batches: dict[str, Batch] = {}
        command = IngestSegmentCommand("session-1", "segment-1", "text")

        policy.accumulate(batches, command)
        policy.accumulate(batches, command)

        self.assertEqual(len(batches["session-1"].segments), 1)
