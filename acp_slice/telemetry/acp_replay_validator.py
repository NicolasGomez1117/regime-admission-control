"""Deterministic task lifecycle replay validation from event logs."""

from acp_slice.contracts.acp_contracts import (
    ALLOWED_TRANSITIONS,
    COMPLETED,
    DEAD_LETTER,
    EVENT_STATUS_CHANGED,
    QUEUED,
    REFUSED,
)
from acp_slice.telemetry.acp_event_reader import get_events_for_task


TERMINAL_STATUSES = {DEAD_LETTER, COMPLETED, REFUSED}


def validate_task_lifecycle(task_id: str) -> dict:
    events = get_events_for_task(task_id)

    transitions = []
    for event in events:
        if event.get("event_type") != EVENT_STATUS_CHANGED:
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        from_status = payload.get("old_status")
        to_status = payload.get("new_status")
        if not isinstance(from_status, str) or not isinstance(to_status, str):
            continue
        transitions.append((from_status, to_status))

    if not transitions:
        return {"valid": False, "reason": "NO_STATUS_EVENTS"}

    first_from_status = transitions[0][0]
    if first_from_status != QUEUED:
        return {
            "valid": False,
            "reason": "INVALID_BOOTSTRAP",
            "from": first_from_status,
        }

    current_status = first_from_status
    for index, (from_status, to_status) in enumerate(transitions):
        if current_status in TERMINAL_STATUSES:
            return {
                "valid": False,
                "reason": "INVALID_TRANSITION",
                "from": current_status,
                "to": to_status,
                "index": index,
            }

        if from_status != current_status:
            return {
                "valid": False,
                "reason": "INVALID_TRANSITION",
                "from": current_status,
                "to": to_status,
                "index": index,
            }

        allowed_next = ALLOWED_TRANSITIONS.get(from_status)
        if allowed_next is None:
            return {
                "valid": False,
                "reason": "INVALID_TRANSITION",
                "from": from_status,
                "to": to_status,
                "index": index,
            }
        if to_status not in allowed_next:
            return {
                "valid": False,
                "reason": "INVALID_TRANSITION",
                "from": from_status,
                "to": to_status,
                "index": index,
            }

        current_status = to_status

    return {
        "valid": True,
        "final_status": current_status,
        "transition_count": len(transitions),
    }
