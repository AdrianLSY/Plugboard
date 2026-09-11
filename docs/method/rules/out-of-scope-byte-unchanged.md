---
type: rule
status: current
authority: rationale
---

# An artifact declared out of scope stays byte-unchanged

**Gate:** `ci/gates/out_of_scope.py`

Where a change declares a set of artifacts out of its scope, a gate asserts they are byte-unchanged, run with the other gates rather than as a closing review step. An intention recorded in prose is not a control.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/out_of_scope.py`](../../../ci/gates/out_of_scope.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
