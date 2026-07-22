# Red-Team Review

Run red-team review in an isolated context after deterministic validation. Do not edit while attacking; give reproducible evidence to Terra for authorized remediation. Exercise every applicable threat named in the `red-team` mode, including policy bypass and missing-resource failure behavior.

## Finding record

Record every finding using these fields, including findings resolved in the same cycle:

- **ID:** stable identifier.
- **Severity:** critical, high, medium, low, or informational.
- **Precondition/attack:** required state and exact adversarial action.
- **Evidence:** reproducible command, fixture, output, or path.
- **Impact:** affected contract and realistic consequence.
- **Remediation:** smallest proposed or completed correction.
- **Retest result:** pass/fail result and fresh evidence after remediation.

## Approval gate

Sol cannot approve with unresolved high or critical findings. Any exception requires explicit human authorization and a recorded rationale; it does not convert a failing check into a passing one. Medium and lower findings must be resolved or explicitly accepted with their residual risk before final review.
