import unittest
from unittest import mock

from acp_slice.telemetry.acp_consistency_validator import validate_task_consistency


class ConsistencyValidatorTests(unittest.TestCase):
    def test_matching_queue_and_replay_valid(self):
        queue_tasks = [{"task_id": "t1", "status": "COMPLETED"}]
        replay = {"valid": True, "final_status": "COMPLETED", "transition_count": 2}
        with mock.patch(
            "acp_slice.telemetry.acp_consistency_validator._load_queue_tasks",
            return_value=queue_tasks,
        ), mock.patch(
            "acp_slice.telemetry.acp_consistency_validator.validate_task_lifecycle",
            return_value=replay,
        ):
            result = validate_task_consistency("t1")
        self.assertEqual(result, {"valid": True, "status": "COMPLETED"})

    def test_mismatch_invalid(self):
        queue_tasks = [{"task_id": "t1", "status": "FAILED"}]
        replay = {"valid": True, "final_status": "COMPLETED", "transition_count": 2}
        with mock.patch(
            "acp_slice.telemetry.acp_consistency_validator._load_queue_tasks",
            return_value=queue_tasks,
        ), mock.patch(
            "acp_slice.telemetry.acp_consistency_validator.validate_task_lifecycle",
            return_value=replay,
        ):
            result = validate_task_consistency("t1")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "STATE_MISMATCH")
        self.assertEqual(result["queue_status"], "FAILED")
        self.assertEqual(result["replay_status"], "COMPLETED")

    def test_task_not_found_invalid(self):
        with mock.patch(
            "acp_slice.telemetry.acp_consistency_validator._load_queue_tasks",
            return_value=[],
        ):
            result = validate_task_consistency("t1")
        self.assertEqual(result, {"valid": False, "reason": "TASK_NOT_FOUND"})


if __name__ == "__main__":
    unittest.main()
