---
type: rule
status: current
authority: rationale
---

# A cited artifact is obtainable

**Gate:** `ci/gates/citations.py`

Every path:line citation resolves to a tracked file or into an artifact declared obtainable with its revision pinned, and the note stating how to obtain it exists. Separately, a spine note carries no normative modal.

## Why

The reason for saying so here rather than in a commit message: the prior art carried 148 KB of prose containing two verifiably false documented claims, and the lesson recorded was that a check whose limits are undocumented gets read as a guarantee.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/citations.py`](../../../ci/gates/citations.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
