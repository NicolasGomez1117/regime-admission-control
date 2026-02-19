"""Validate consistency between queue task state and replayed lifecycle state."""

import json
import os
from pathlib import Path

from acp_slice.contracts.acp_contracts import FIELD_STATUS, FIELD_TASK_ID
from acp_slice.telemetry.acp_replay_validator import validate_task_lifecycle


SLICE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("ACP_SLICE_RUNTIME_ROOT", str(SLICE_ROOT / ".tmp")))
TASKS_PATH = str(RUNTIME_ROOT / "queue" / "tasks.jsonl")


def _load_queue_tasks() -> list[dict]:
    tasks = []
    if not os.path.exists(TASKS_PATH):
        return tasks
    try:
        with open(TASKS_PATH, "r", encoding="utf-8") as queue_file:
            for line in queue_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    tasks.append(item)
    except Exception:
        return []
    return tasks


def validate_task_consistency(task_id: str) -> dict:
    queue_tasks = _load_queue_tasks()
    queue_task = None
    for task in queue_tasks:
        if isinstance(task, dict) and task.get(FIELD_TASK_ID) == task_id:
            queue_task = task
            break

    if queue_task is None:
        return {"valid": False, "reason": "TASK_NOT_FOUND"}

    replay_result = validate_task_lifecycle(task_id)
    if not replay_result.get("valid"):
        return {"valid": False, "reason": "REPLAY_INVALID", "details": replay_result}

    queue_status = queue_task.get(FIELD_STATUS)
    replay_status = replay_result.get("final_status")
    if queue_status != replay_status:
        return {
            "valid": False,
            "reason": "STATE_MISMATCH",
            "queue_status": queue_status,
            "replay_status": replay_status,
        }

    return {"valid": True, "status": queue_status}
