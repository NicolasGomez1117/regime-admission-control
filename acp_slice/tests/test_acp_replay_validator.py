import tempfile
import unittest
from pathlib import Path
from unittest import mock

from acp_slice.telemetry import acp_event_reader
from acp_slice.telemetry.acp_replay_validator import validate_task_lifecycle


class EventReaderTests(unittest.TestCase):
    def test_malformed_json_line_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "events.jsonl"
            events_path.write_text(
                "\n".join(
                    [
                        '{"event_type":"EVENT_STATUS_CHANGED","task_id":"t1","payload":{"old_status":"QUEUED","new_status":"EVALUATING"}}',
                        "{not-json",
                        '{"event_type":"EVENT_RUN_FINISHED","task_id":"t1","payload":{}}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(acp_event_reader, "EVENTS_LOG_PATH", str(events_path)):
                events = acp_event_reader.get_events()
            self.assertEqual(len(events), 2)


class ReplayValidatorTests(unittest.TestCase):
    def test_bootstrap_not_queued_invalid_bootstrap(self):
        events = [
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "EVALUATING", "new_status": "FAILED"},
            }
        ]
        with mock.patch("acp_slice.telemetry.acp_replay_validator.get_events_for_task", return_value=events):
            result = validate_task_lifecycle("t1")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "INVALID_BOOTSTRAP")
        self.assertEqual(result["from"], "EVALUATING")

    def test_invalid_transition_detected(self):
        events = [
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "QUEUED", "new_status": "COMPLETED"},
            }
        ]
        with mock.patch("acp_slice.telemetry.acp_replay_validator.get_events_for_task", return_value=events):
            result = validate_task_lifecycle("t1")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "INVALID_TRANSITION")

    def test_valid_sequence_passes(self):
        events = [
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "QUEUED", "new_status": "EVALUATING"},
            },
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "EVALUATING", "new_status": "COMPLETED"},
            },
        ]
        with mock.patch("acp_slice.telemetry.acp_replay_validator.get_events_for_task", return_value=events):
            result = validate_task_lifecycle("t1")
        self.assertTrue(result["valid"])
        self.assertEqual(result["final_status"], "COMPLETED")
        self.assertEqual(result["transition_count"], 2)

    def test_transition_after_terminal_invalid_transition(self):
        events = [
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "QUEUED", "new_status": "EVALUATING"},
            },
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "EVALUATING", "new_status": "COMPLETED"},
            },
            {
                "event_type": "EVENT_STATUS_CHANGED",
                "task_id": "t1",
                "payload": {"old_status": "COMPLETED", "new_status": "FAILED"},
            },
        ]
        with mock.patch("acp_slice.telemetry.acp_replay_validator.get_events_for_task", return_value=events):
            result = validate_task_lifecycle("t1")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "INVALID_TRANSITION")
        self.assertEqual(result["index"], 2)


if __name__ == "__main__":
    unittest.main()
