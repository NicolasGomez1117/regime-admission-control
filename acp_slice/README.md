# ACP Slice

This is a recruiter-safe, minimal slice of the Admissible Control Plane (ACP) runtime.
It demonstrates a deterministic lifecycle engine, append-only telemetry, and post-run replay/consistency validation.
The slice is self-contained under `acp_slice/` and avoids importing broader lab/control-plane sprawl.

## Components
- `contracts/`: lifecycle states, event types, and transition contracts.
- `runners/`: deterministic queue runner loop.
- `telemetry/`: append-only events writer plus replay and consistency validators.
- `tests/`: focused validator and telemetry tests.
- `tasks/`: one example task payload (`echo_task.json`).

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip pytest
pytest -q acp_slice/tests
# optional
python -m acp_slice.runners.acp_run_loop --help
```

## What to look for
- deterministic lifecycle transitions (contract-enforced)
- append-only event emission
- replay-based lifecycle validation and queue/event consistency checks
