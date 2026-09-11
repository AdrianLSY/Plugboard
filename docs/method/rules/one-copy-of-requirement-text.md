---
type: rule
status: current
authority: rationale
---

# Requirement text has one copy

**Gate:** `ci/gates/duplication.py`

A requirement paragraph does not appear in both the spine and a specification. This decides copy-paste and does not decide paraphrase; drift is owned by the authority-precedence rule and by review.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/duplication.py`](../../../ci/gates/duplication.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
