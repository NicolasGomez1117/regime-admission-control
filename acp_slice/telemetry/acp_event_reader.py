"""Read ACP event logs deterministically in file order."""

import json
import os

from acp_slice.telemetry.acp_events import EVENTS_LOG_PATH


def get_events() -> list[dict]:
    """Return all valid event dicts in file order."""
    events = []
    if not os.path.exists(EVENTS_LOG_PATH):
        return events

    try:
        with open(EVENTS_LOG_PATH, "r", encoding="utf-8") as events_file:
            for line in events_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                if isinstance(event, dict):
                    events.append(event)
    except Exception:
        return []
    return events


def get_events_for_task(task_id: str) -> list[dict]:
    """Return all events whose task_id matches exactly."""
    return [event for event in get_events() if event.get("task_id") == task_id]
