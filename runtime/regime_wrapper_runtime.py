#!/usr/bin/env python3
"""
Regime wrapper runtime.
Non-claims:
- This wrapper does NOT determine correctness.
- This wrapper does NOT authorize action.
- This wrapper does NOT validate domain truth.
- This wrapper only enforces admission to kernel evaluation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REGIME_ENUM = {
    "SETTLEMENT_RAILS_INCIDENT",
    "STABLECOIN_PEG_EVENT",
    "BANK_LIQUIDITY_EVENT",
}


def refuse(reason: str) -> dict:
    print(f"WRAPPER_REFUSE:{reason}")
    return {"status": "REFUSE", "reason": reason, "provenance": "WRAPPER"}


def invoke_kernel_stub(payload: object) -> dict:
    print("KERNEL_INVOKE_ATTEMPT")
    return {"status": "REFUSE", "reason": "KERNEL_STUB", "provenance": "KERNEL"}


def load_json(arg: str) -> object:
    path = Path(arg)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(arg)


def main() -> int:
    if len(sys.argv) < 3:
        result = refuse("REGIME_MISSING")
        print(json.dumps(result))
        return 0

    try:
        regime = load_json(sys.argv[1])
        payload = load_json(sys.argv[2])
    except Exception:
        result = refuse("REGIME_UNKNOWN")
        print(json.dumps(result))
        return 0

    if regime is None:
        result = refuse("REGIME_MISSING")
        print(json.dumps(result))
        return 0

    regime_status = regime.get("regime_status", "UNKNOWN")
    regime_id = regime.get("regime_id", "UNKNOWN")
    entry_mode = regime.get("entry_mode", "UNKNOWN")

    if regime_status != "REGIME_DECLARED":
        result = refuse("REGIME_MISSING" if regime_status == "REGIME_NOT_DECLARED" else "REGIME_UNKNOWN")
        print(json.dumps(result))
        return 0

    if entry_mode != "OPERATOR_ASSERTED" or regime_id not in REGIME_ENUM:
        result = refuse("REGIME_UNKNOWN")
        print(json.dumps(result))
        return 0

    result = invoke_kernel_stub(payload)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
