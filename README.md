# Regime Admission Control

A refusal-first admission control layer that enforces explicit regime declaration before decision evaluation.

## What this does

This repository defines an explicit admission boundary that prevents decision evaluation unless a declared and recognized Regime Context is present.

It acts as a wrapper layer only. It does not evaluate decisions, validate domain truth, or determine correctness.

## Why it exists

In many systems, decisions are evaluated even when the surrounding regime is undefined or ambiguous.

This layer exists to ensure that **decision evaluation is refused by default** unless an explicit regime is declared by an operator and recognized by the system.

## What this does NOT do

- Does not authorize actions
- Does not validate domain correctness
- Does not infer regimes or apply heuristics
- Does not evaluate decisions
- Does not modify kernel behavior

## Behavior

- Missing regime → `REFUSE:REGIME_MISSING`
- Unknown or unrecognized regime → `REFUSE:REGIME_UNKNOWN`
- Declared and recognized regime → admission granted; downstream evaluation is out of scope

## Running the wrapper

```bash
python runtime/regime_wrapper_runtime.py <regime_context.json|json> <payload.json|json>
Tests
The tests/ directory contains contract-style sweep tests that specify expected admission behavior, including:

baseline admission/refusal

negative mutation rejection

cross-snapshot stability

cross-regime invariance

These tests define invariants for admission behavior rather than executable test harnesses.
