Regime Wrapper Negative Mutation Sweep Test Contract

## 1. Test Scope
- Mutation tests for Regime Context / wrapper boundary.
- Kernel behavior is out of scope.

## 2. Mutation Classes
- Missing required fields.
- Invalid enum values (regime_id, entry_mode, regime_status).
- entry_mode ≠ OPERATOR_ASSERTED.
- Missing or partial non_claims.
- Extra fields resembling diagnostic dimensions.
- semantics_version missing or UNKNOWN where disallowed.
- Scope ambiguity (missing or malformed scope_id).
- Structural corruption (wrong types, nulls).

## 3. Mutation Sweep Table
| Mutation Class | Mutation Description | Expected Wrapper Outcome | Kernel Invoked |
| --- | --- | --- | --- |
| Missing required fields | One or more required fields absent. | REFUSE:REGIME_MISSING | NO |
| Invalid enum values | regime_id, entry_mode, or regime_status not in enum sets. | REFUSE:REGIME_UNKNOWN | NO |
| entry_mode ≠ OPERATOR_ASSERTED | entry_mode present but not OPERATOR_ASSERTED. | REFUSE:REGIME_UNKNOWN | NO |
| Missing or partial non_claims | non_claims missing or incomplete. | REFUSE:REGIME_UNKNOWN | NO |
| Extra fields resembling diagnostic dimensions | Regime Context includes fields matching diagnostic dimension names or symbols. | REFUSE:REGIME_UNKNOWN | NO |
| semantics_version missing or UNKNOWN where disallowed | semantics_version absent or UNKNOWN when required. | REFUSE:REGIME_UNKNOWN | NO |
| Scope ambiguity | scope_id missing, malformed, or ambiguous. | REFUSE:REGIME_UNKNOWN | NO |
| Structural corruption | Wrong types, nulls, or structural violations. | REFUSE:REGIME_UNKNOWN | NO |

## 4. Invariants Validated
- Wrapper rejects contaminated regime inputs.
- No malformed regime input can reach G0.
- No mutation upgrades UNKNOWN to DECLARED.
- No mutation produces PROCEED_TO_KERNEL.

## 5. Non-Claims
- No claims about admissibility.
- No claims about authorization.
- No claims about decision correctness.
- No claims about kernel gate behavior.

END OF FILE
