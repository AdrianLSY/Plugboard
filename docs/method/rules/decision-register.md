---
type: rule
status: current
authority: rationale
---

# There is exactly one decision register

**Gate:** `ci/gates/decision_register.py`

An identifier in the installation's unnamespaced sequence, introduced anywhere but the declared register, fails. A retired identifier is never reassigned, and a change's own decisions carry a namespace.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/decision_register.py`](../../../ci/gates/decision_register.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
