Regime Wrapper / Runner Contract

## 1. Wrapper Invariant
Name: REGIME_DECLARED_BEFORE_KERNEL
Definition: Kernel invocation is permitted only when a Regime Context is explicitly declared and conforms to the Regime Context Contract.
Violation condition: Any attempt to invoke G0–G4 without a declared Regime Context.
Scope: Wrapper / runner boundary above G0.
Rationale: Enforces refusal-first behavior and prevents implicit regime inference.

## 2. Runner State Machine
States:
- INIT
- REGIME_CHECK
- REGIME_MISSING_REFUSE
- REGIME_UNKNOWN_REFUSE
- REGIME_DECLARED
- KERNEL_INVOKE
- KERNEL_REFUSE
- KERNEL_BOUNDED_DECISION_SPACE

Transitions:
- INIT -> REGIME_CHECK on runner start.
- REGIME_CHECK -> REGIME_MISSING_REFUSE if Regime Context is absent.
- REGIME_CHECK -> REGIME_UNKNOWN_REFUSE if Regime Context is present but `regime_id` is UNKNOWN or non-enum.
- REGIME_CHECK -> REGIME_DECLARED if Regime Context is present and `regime_id` is a valid enum.
- REGIME_DECLARED -> KERNEL_INVOKE on explicit invocation request.
- KERNEL_INVOKE -> KERNEL_REFUSE if kernel output is REFUSE.
- KERNEL_INVOKE -> KERNEL_BOUNDED_DECISION_SPACE if kernel output is bounded decision space.

Refusal states:
- REGIME_MISSING_REFUSE
- REGIME_UNKNOWN_REFUSE
- KERNEL_REFUSE

## 3. Refusal Provenance Rule
- Wrapper refusals (REGIME_MISSING_REFUSE, REGIME_UNKNOWN_REFUSE) are attributed to wrapper invariant enforcement.
- Kernel refusals (KERNEL_REFUSE) are attributed to G0–G4.
- Kernel outputs do not modify regime status or wrapper state.

## 4. Minimal Execution Contract
Inputs required:
- Regime Context object conforming to `regimes/regime_context_contract.md`.
- Diagnostic snapshot for kernel input (format unspecified here).

Outputs guaranteed:
- One refusal or bounded decision space outcome.
- Provenance tag: WRAPPER_REFUSAL or KERNEL_REFUSAL.

Explicit non-claims:
- No inference.
- No permission.
- No admissibility guarantee.
- No kernel modification.
- UNKNOWN remains absorbing.

END OF FILE
