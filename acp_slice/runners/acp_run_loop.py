"""Minimal deterministic ACP queue runner loop."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from acp_slice.contracts.acp_contracts import (
    ALLOWED_TRANSITIONS,
    COMPLETED,
    DEAD_LETTER,
    EVALUATING,
    EVENT_DEAD_LETTERED,
    EVENT_RETRY_SCHEDULED,
    EVENT_RUN_FINISHED,
    EVENT_RUN_STARTED,
    EVENT_STATUS_CHANGED,
    FAILED,
    FIELD_DEAD_LETTER_REASON,
    FIELD_FAILURE_REASON,
    FIELD_INVARIANT_VIOLATION,
    FIELD_LAST_EXIT_CODE,
    FIELD_MAX_RETRIES,
    FIELD_NEXT_ATTEMPT_AT,
    FIELD_RETRIES,
    FIELD_RETRY_DELAY_SECONDS,
    FIELD_STATUS,
    FIELD_TASK_FILE,
    FIELD_TASK_ID,
    FIELD_HARNESS_LOG_PATH,
    INVARIANT_VIOLATION,
    PRECHECK_INVALID,
    QUEUED,
    REPO_PATH_INVALID,
    REFUSED,
    RETRIES_EXHAUSTED,
    RUNNER_EXCEPTION,
    TASK_FILE_INVALID,
    TASK_FILE_MISSING,
    UNKNOWN_FAILURE,
)
from acp_slice.telemetry.acp_consistency_validator import validate_task_consistency
from acp_slice.telemetry.acp_events import append_event
from acp_slice.telemetry.acp_replay_validator import validate_task_lifecycle


SLICE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("ACP_SLICE_RUNTIME_ROOT", str(SLICE_ROOT / ".tmp")))
TASKS_PATH = str(RUNTIME_ROOT / "queue" / "tasks.jsonl")
CONFIG_PATH = str(RUNTIME_ROOT / "config.json")
TERMINAL_STATUSES = {COMPLETED, REFUSED, DEAD_LETTER}
HARNESS_LOG_DIR = str(RUNTIME_ROOT / "logs" / "harness")
TASKFILE_REQUIRED_FIELDS = {"repo_path", "argv"}
TASKFILE_OPTIONAL_FIELDS = {"label"}
TASKFILE_ALLOWED_FIELDS = TASKFILE_REQUIRED_FIELDS | TASKFILE_OPTIONAL_FIELDS


def _load_tasks(path: str) -> list[dict]:
    tasks = []
    with open(path, "r", encoding="utf-8") as tasks_file:
        for line in tasks_file:
            line = line.strip()
            if not line:
                continue
            tasks.append(json.loads(line))
    return tasks


def _write_tasks_atomic(path: str, tasks: list[dict]) -> None:
    directory = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False
    ) as tmp_file:
        for task in tasks:
            tmp_file.write(json.dumps(task, sort_keys=True) + "\n")
        temp_path = tmp_file.name
    os.replace(temp_path, path)


def _load_max_tasks_per_run() -> int:
    default_value = 1
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except Exception:
        return default_value
    if not isinstance(config, dict):
        return default_value
    value = config.get("max_tasks_per_run", default_value)
    if not isinstance(value, int) or value <= 0:
        return default_value
    return value


def _load_json_object(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("task file must be a JSON object")
    return payload


def _resolve_repo_path(raw_repo_path: str) -> str | None:
    if not isinstance(raw_repo_path, str) or raw_repo_path == "":
        return None
    if not os.path.isabs(raw_repo_path):
        normalized = os.path.normpath(raw_repo_path)
        if normalized == ".." or normalized.startswith(".." + os.sep):
            return None
    resolved = os.path.realpath(raw_repo_path)
    if not os.path.isdir(resolved):
        return None
    if not os.path.exists(os.path.join(resolved, ".git")):
        return None
    return resolved


def _validate_task_file_contract(task_file_payload: dict) -> tuple[bool, str | None]:
    if any(key not in TASKFILE_ALLOWED_FIELDS for key in task_file_payload.keys()):
        return False, TASK_FILE_INVALID

    missing = TASKFILE_REQUIRED_FIELDS - set(task_file_payload.keys())
    if missing:
        return False, TASK_FILE_INVALID

    repo_path = task_file_payload.get("repo_path")
    if not isinstance(repo_path, str) or repo_path == "":
        return False, TASK_FILE_INVALID

    argv = task_file_payload.get("argv")
    if not isinstance(argv, list) or len(argv) == 0:
        return False, TASK_FILE_INVALID
    if any(not isinstance(item, str) or item == "" for item in argv):
        return False, TASK_FILE_INVALID

    if "label" in task_file_payload:
        label = task_file_payload.get("label")
        if not isinstance(label, str) or label == "":
            return False, TASK_FILE_INVALID

    resolved_repo = _resolve_repo_path(repo_path)
    if resolved_repo is None:
        return False, REPO_PATH_INVALID
    return True, None


def _harness_log_path(task_id: str) -> str:
    os.makedirs(HARNESS_LOG_DIR, exist_ok=True)
    return os.path.join(HARNESS_LOG_DIR, f"{task_id}.jsonl")


def _run_harness(task_id: str, task_file_payload: dict) -> subprocess.CompletedProcess[str]:
    resolved_repo = _resolve_repo_path(task_file_payload["repo_path"])
    if resolved_repo is None:
        raise ValueError(REPO_PATH_INVALID)
    argv = task_file_payload["argv"]
    label = task_file_payload.get("label")
    resolved_label = label if isinstance(label, str) and label else task_id
    log_path = _harness_log_path(task_id)

    command = [
        "aah",
        "run",
        "--repo",
        resolved_repo,
        "--log",
        log_path,
        "--label",
        resolved_label,
        "--",
    ] + argv
    return subprocess.run(command, capture_output=True, text=True, shell=False)


def _transition(task: dict, new_status: str) -> None:
    current_status = task.get(FIELD_STATUS)
    task_id = task.get(FIELD_TASK_ID) if isinstance(task.get(FIELD_TASK_ID), str) else None
    # Transition checks are critical to preserve a deterministic task lifecycle.
    if not isinstance(current_status, str) or current_status not in ALLOWED_TRANSITIONS:
        task[FIELD_STATUS] = DEAD_LETTER
        task[FIELD_INVARIANT_VIOLATION] = True
        task[FIELD_DEAD_LETTER_REASON] = INVARIANT_VIOLATION
        append_event(
            {
                "event_type": EVENT_STATUS_CHANGED,
                "task_id": task_id,
                "payload": {"old_status": current_status, "new_status": DEAD_LETTER},
            }
        )
        append_event(
            {
                "event_type": EVENT_DEAD_LETTERED,
                "task_id": task_id,
                "payload": {FIELD_DEAD_LETTER_REASON: task.get(FIELD_DEAD_LETTER_REASON)},
            }
        )
        return
    allowed_next = ALLOWED_TRANSITIONS[current_status]
    if new_status not in allowed_next:
        # Invalid moves are dead-lettered to prevent queue corruption and loops.
        task[FIELD_STATUS] = DEAD_LETTER
        task[FIELD_INVARIANT_VIOLATION] = True
        task[FIELD_DEAD_LETTER_REASON] = INVARIANT_VIOLATION
        append_event(
            {
                "event_type": EVENT_STATUS_CHANGED,
                "task_id": task_id,
                "payload": {"old_status": current_status, "new_status": DEAD_LETTER},
            }
        )
        append_event(
            {
                "event_type": EVENT_DEAD_LETTERED,
                "task_id": task_id,
                "payload": {FIELD_DEAD_LETTER_REASON: task.get(FIELD_DEAD_LETTER_REASON)},
            }
        )
        return
    task[FIELD_STATUS] = new_status
    append_event(
        {
            "event_type": EVENT_STATUS_CHANGED,
            "task_id": task_id,
            "payload": {"old_status": current_status, "new_status": new_status},
        }
    )


def _mark_failed(task: dict, reason: str) -> None:
    _transition(task, FAILED)
    if task.get(FIELD_STATUS) == FAILED:
        task[FIELD_FAILURE_REASON] = reason


def _emit_run_finished(task: dict) -> None:
    append_event(
        {
            "event_type": EVENT_RUN_FINISHED,
            "task_id": task.get(FIELD_TASK_ID) if isinstance(task.get(FIELD_TASK_ID), str) else None,
            "payload": {"final_status": task.get(FIELD_STATUS)},
        }
    )


def _apply_retry_if_eligible(task: dict, current_time: float) -> None:
    if task.get(FIELD_STATUS) != FAILED:
        return

    retries = task.get(FIELD_RETRIES, 0)
    max_retries = task.get(FIELD_MAX_RETRIES, 0)
    retry_delay_seconds = task.get(FIELD_RETRY_DELAY_SECONDS, 0.0)
    if not isinstance(retries, int):
        retries = 0
    if not isinstance(max_retries, int):
        max_retries = 0
    if not isinstance(retry_delay_seconds, (int, float)):
        retry_delay_seconds = 0.0

    if retries < max_retries:
        task[FIELD_RETRIES] = retries + 1
        task[FIELD_NEXT_ATTEMPT_AT] = current_time + float(retry_delay_seconds)
        append_event(
            {
                "event_type": EVENT_RETRY_SCHEDULED,
                "task_id": task.get(FIELD_TASK_ID) if isinstance(task.get(FIELD_TASK_ID), str) else None,
                "payload": {
                    FIELD_RETRIES: task.get(FIELD_RETRIES),
                    FIELD_MAX_RETRIES: max_retries,
                    FIELD_NEXT_ATTEMPT_AT: task.get(FIELD_NEXT_ATTEMPT_AT),
                },
            }
        )
        _transition(task, QUEUED)
        if task.get(FIELD_STATUS) == QUEUED:
            task.pop(FIELD_FAILURE_REASON, None)
        return

    _transition(task, DEAD_LETTER)
    if task.get(FIELD_STATUS) == DEAD_LETTER:
        task[FIELD_DEAD_LETTER_REASON] = RETRIES_EXHAUSTED
        append_event(
            {
                "event_type": EVENT_DEAD_LETTERED,
                "task_id": task.get(FIELD_TASK_ID) if isinstance(task.get(FIELD_TASK_ID), str) else None,
                "payload": {FIELD_DEAD_LETTER_REASON: task.get(FIELD_DEAD_LETTER_REASON)},
            }
        )


def _validator_error_message(result: dict) -> str:
    reason = result.get("reason")
    details = result.get("details")
    if isinstance(reason, str) and isinstance(details, dict):
        return f"{reason}:{json.dumps(details, sort_keys=True)}"
    if isinstance(reason, str):
        return reason
    return "VALIDATOR_FAILURE"


def _mark_dead_letter_for_validator_failure(task: dict, code: str, message: str) -> None:
    task_id = task.get(FIELD_TASK_ID) if isinstance(task.get(FIELD_TASK_ID), str) else None
    old_status = task.get(FIELD_STATUS)
    if old_status != DEAD_LETTER:
        task[FIELD_STATUS] = DEAD_LETTER
        append_event(
            {
                "event_type": EVENT_STATUS_CHANGED,
                "task_id": task_id,
                "payload": {"old_status": old_status, "new_status": DEAD_LETTER},
            }
        )
    task[FIELD_DEAD_LETTER_REASON] = INVARIANT_VIOLATION
    task[FIELD_INVARIANT_VIOLATION] = {"code": code, "message": message}
    append_event(
        {
            "event_type": EVENT_DEAD_LETTERED,
            "task_id": task_id,
            "payload": {FIELD_DEAD_LETTER_REASON: task.get(FIELD_DEAD_LETTER_REASON)},
        }
    )


def _run_terminal_validations(task: dict) -> None:
    task_id = task.get(FIELD_TASK_ID)
    if not isinstance(task_id, str):
        return
    if task.get(FIELD_STATUS) not in TERMINAL_STATUSES:
        return

    replay_result = validate_task_lifecycle(task_id)
    if not replay_result.get("valid"):
        _mark_dead_letter_for_validator_failure(
            task,
            "REPLAY_INVALID",
            _validator_error_message(replay_result),
        )
        return

    consistency_result = validate_task_consistency(task_id)
    if not consistency_result.get("valid"):
        _mark_dead_letter_for_validator_failure(
            task,
            "CONSISTENCY_INVALID",
            _validator_error_message(consistency_result),
        )


def main() -> int:
    tasks = _load_tasks(TASKS_PATH)
    max_tasks_per_run = _load_max_tasks_per_run()
    processed_count = 0

    for task in tasks:
        if processed_count >= max_tasks_per_run:
            break
        if task.get(FIELD_STATUS) == QUEUED:
            current_time = time.time()
            next_attempt_at = task.get(FIELD_NEXT_ATTEMPT_AT)
            if isinstance(next_attempt_at, (int, float)) and current_time < float(
                next_attempt_at
            ):
                continue

            if (
                not isinstance(task.get(FIELD_TASK_ID), str)
                or not isinstance(task.get(FIELD_STATUS), str)
                or not isinstance(task.get(FIELD_TASK_FILE), str)
            ):
                _mark_failed(task, PRECHECK_INVALID)
                _apply_retry_if_eligible(task, current_time)
                _write_tasks_atomic(TASKS_PATH, tasks)
                _run_terminal_validations(task)
                _write_tasks_atomic(TASKS_PATH, tasks)
                _emit_run_finished(task)
                processed_count += 1
                continue

            task_file = task.get(FIELD_TASK_FILE)

            _transition(task, EVALUATING)
            _write_tasks_atomic(TASKS_PATH, tasks)

            try:
                append_event(
                    {
                        "event_type": EVENT_RUN_STARTED,
                        "task_id": task.get(FIELD_TASK_ID),
                        "payload": {},
                    }
                )
                if not os.path.exists(task_file):
                    _mark_failed(task, TASK_FILE_MISSING)
                else:
                    try:
                        task_payload = _load_json_object(task_file)
                    except Exception:
                        _mark_failed(task, TASK_FILE_INVALID)
                        task_payload = None

                    if task_payload is not None:
                        valid, failure_reason = _validate_task_file_contract(task_payload)
                        if not valid:
                            _mark_failed(task, failure_reason if isinstance(failure_reason, str) else TASK_FILE_INVALID)
                        else:
                            result = _run_harness(task[FIELD_TASK_ID], task_payload)
                            task[FIELD_LAST_EXIT_CODE] = result.returncode
                            task[FIELD_HARNESS_LOG_PATH] = _harness_log_path(task[FIELD_TASK_ID])
                            if result.returncode == 0:
                                _transition(task, COMPLETED)
                                task.pop(FIELD_FAILURE_REASON, None)
                            else:
                                _mark_failed(task, UNKNOWN_FAILURE)
            except Exception:
                _mark_failed(task, RUNNER_EXCEPTION)
            _apply_retry_if_eligible(task, current_time)
            _write_tasks_atomic(TASKS_PATH, tasks)
            _run_terminal_validations(task)
            _write_tasks_atomic(TASKS_PATH, tasks)
            _emit_run_finished(task)
            processed_count += 1
            continue

    return 0


def run_forever(poll_interval: float) -> int:
    try:
        while True:
            main()
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--loop":
        poll_interval = 2.0
        if len(sys.argv) >= 3:
            poll_interval = float(sys.argv[2])
        raise SystemExit(run_forever(poll_interval))
    raise SystemExit(main())
