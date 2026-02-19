import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from acp_slice.telemetry import acp_events


class EventsWriterTests(unittest.TestCase):
    def test_append_event_never_raises_on_unwritable_path_and_increments_counter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            unwritable_target = Path(tmpdir) / "as_directory"
            unwritable_target.mkdir()

            acp_events.EVENT_WRITE_ERRORS_TOTAL = 0
            with mock.patch.object(acp_events, "EVENTS_LOG_PATH", str(unwritable_target)):
                try:
                    acp_events.append_event(
                        {
                            "event_type": "EVENT_STATUS_CHANGED",
                            "task_id": "t1",
                            "payload": {"old_status": "QUEUED", "new_status": "EVALUATING"},
                        }
                    )
                except Exception as exc:  # pragma: no cover
                    self.fail(f"append_event raised unexpectedly: {exc}")

            self.assertEqual(acp_events.EVENT_WRITE_ERRORS_TOTAL, 1)

    def test_append_event_twice_uses_same_run_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "events.jsonl"
            with mock.patch.object(acp_events, "EVENTS_LOG_PATH", str(events_path)):
                acp_events.append_event(
                    {
                        "event_type": "EVENT_RUN_STARTED",
                        "task_id": "t1",
                        "payload": {},
                    }
                )
                acp_events.append_event(
                    {
                        "event_type": "EVENT_RUN_FINISHED",
                        "task_id": "t1",
                        "payload": {},
                    }
                )

            lines = events_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            first = json.loads(lines[0])
            second = json.loads(lines[1])
            self.assertIn("run_id", first)
            self.assertEqual(first["run_id"], second["run_id"])


if __name__ == "__main__":
    unittest.main()
