---
type: rule
status: current
authority: rationale
---

# Every note is reachable from an entry point

**Gate:** `ci/gates/reachability.py`

A note or planning artifact reachable from nothing fails, and a planning artifact's inbound link comes from a note rather than from another planning artifact. Reachability is reported as a path, so a contributor is told where the note is missing from.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/reachability.py`](../../../ci/gates/reachability.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
