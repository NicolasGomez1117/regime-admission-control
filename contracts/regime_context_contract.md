Regime Context Contract

## Purpose
Define the minimal Regime Context object required to invoke the kernel meaningfully.

## Field Definitions (All Required)
- regime_id: enum from `regimes/regime_registry.md`.
- scope_id: case + snapshot identifier.
- entry_mode: OPERATOR_ASSERTED only.
- semantics_version: string.
- asserted_at: ISO timestamp field placeholder.
- non_claims: must include `no_inference`, `no_permission`, `no_admissibility_guarantee`.

## Guardrails
- Regime Context is not executable input for actions.
- Regime Context does not override UNKNOWN.
- Absence of Regime Context yields pre-G0 refusal: REGIME_MISSING.

## Non-Claims
- No inference.
- No permission.
- No admissibility guarantee.
- No kernel modification.

END OF FILE
