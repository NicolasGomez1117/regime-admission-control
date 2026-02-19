"""Append-only ACP event telemetry writer."""

import datetime
import json
import os
import sys
import uuid
from pathlib import Path


SLICE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("ACP_SLICE_RUNTIME_ROOT", str(SLICE_ROOT / ".tmp")))
EVENTS_LOG_PATH = str(RUNTIME_ROOT / "logs" / "events.jsonl")
EVENT_VERSION = "v0"
EVENT_WRITE_ERRORS_TOTAL = 0
RUN_ID = str(uuid.uuid4())


def append_event(event: dict) -> None:
    """Append one structured event line and never raise."""
    global EVENT_WRITE_ERRORS_TOTAL
    try:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        record = {
            "event_version": EVENT_VERSION,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "run_id": RUN_ID,
            "event_type": event.get("event_type"),
            "task_id": event.get("task_id"),
            "payload": payload,
        }
        os.makedirs(os.path.dirname(EVENTS_LOG_PATH), exist_ok=True)
        with open(EVENTS_LOG_PATH, "a", encoding="utf-8") as events_file:
            events_file.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:
        EVENT_WRITE_ERRORS_TOTAL += 1
        if os.getenv("ACP_EVENTS_WARN") == "1":
            print("ACP event logging failed", file=sys.stderr)
        return
