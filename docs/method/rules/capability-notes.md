---
type: rule
status: current
authority: rationale
---

# Every capability has a concept note

**Gate:** `ci/gates/capability_notes.py`

A specification without a concept note fails, and so does a concept note without a specification. Every capability a specification names as a dependency is linked from that capability's note, and a note stays under the declared ceiling.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/capability_notes.py`](../../../ci/gates/capability_notes.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
