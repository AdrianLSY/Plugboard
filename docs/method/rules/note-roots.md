---
type: rule
status: current
authority: rationale
---

# Every tracked note lives under a declared root

**Gate:** `ci/gates/note_roots.py`

The declared root set is closed: each root is named governed or exempt, an exempt root records what owns its files instead, and a directory omitted from a traversal without being declared exempt fails. A gate never decides its own subject.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/note_roots.py`](../../../ci/gates/note_roots.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
