Regime Wrapper Cross-Regime Invariance Sweep Test Contract

## 1. Test Scope
- Cross-regime invariance tests only.
- Kernel semantics are opaque and out of scope.

## 2. Sweep Axes
- regime_id: {SETTLEMENT_RAILS_INCIDENT, STABLECOIN_PEG_EVENT, BANK_LIQUIDITY_EVENT}
- Presence: {MISSING, PRESENT}
- Regime status: {REGIME_DECLARED, REGIME_NOT_DECLARED, REGIME_UNKNOWN}
- semantics_version: v0
- scope_id: S₁ (no ordering semantics)

## 3. Invariance Requirement
- For fixed Presence, Regime status, semantics_version, and scope_id: wrapper outcome is identical across all regime_id values.
- regime_id variation MUST NOT:
  - upgrade REGIME_NOT_DECLARED or REGIME_UNKNOWN
  - downgrade REGIME_DECLARED
  - change refusal type
  - influence kernel invocation eligibility

## 4. Expected Outcomes Table
| scope_id | Presence | Regime Status | regime_id | semantics_version | Expected Outcome |
| --- | --- | --- | --- | --- | --- |
| S₁ | MISSING | REGIME_DECLARED | SETTLEMENT_RAILS_INCIDENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_DECLARED | STABLECOIN_PEG_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_DECLARED | BANK_LIQUIDITY_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_NOT_DECLARED | SETTLEMENT_RAILS_INCIDENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_NOT_DECLARED | STABLECOIN_PEG_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_NOT_DECLARED | BANK_LIQUIDITY_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_UNKNOWN | SETTLEMENT_RAILS_INCIDENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_UNKNOWN | STABLECOIN_PEG_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | MISSING | REGIME_UNKNOWN | BANK_LIQUIDITY_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | PRESENT | REGIME_DECLARED | SETTLEMENT_RAILS_INCIDENT | v0 | PROCEED_TO_KERNEL |
| S₁ | PRESENT | REGIME_DECLARED | STABLECOIN_PEG_EVENT | v0 | PROCEED_TO_KERNEL |
| S₁ | PRESENT | REGIME_DECLARED | BANK_LIQUIDITY_EVENT | v0 | PROCEED_TO_KERNEL |
| S₁ | PRESENT | REGIME_NOT_DECLARED | SETTLEMENT_RAILS_INCIDENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | PRESENT | REGIME_NOT_DECLARED | STABLECOIN_PEG_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | PRESENT | REGIME_NOT_DECLARED | BANK_LIQUIDITY_EVENT | v0 | REFUSE:REGIME_MISSING |
| S₁ | PRESENT | REGIME_UNKNOWN | SETTLEMENT_RAILS_INCIDENT | v0 | REFUSE:REGIME_UNKNOWN |
| S₁ | PRESENT | REGIME_UNKNOWN | STABLECOIN_PEG_EVENT | v0 | REFUSE:REGIME_UNKNOWN |
| S₁ | PRESENT | REGIME_UNKNOWN | BANK_LIQUIDITY_EVENT | v0 | REFUSE:REGIME_UNKNOWN |

## 5. Invariants Validated
- regime_id is a semantic label only (no implied rules/thresholds).
- Wrapper behavior is stable under regime label substitution.
- Kernel is never invoked unless REGIME_DECLARED.
- Wrapper refusal provenance remains distinct from kernel refusal.

## 6. Non-Claims
- No claims about admissibility.
- No claims about authorization.
- No claims about decision correctness.
- No claims about kernel gate behavior.

END OF FILE
