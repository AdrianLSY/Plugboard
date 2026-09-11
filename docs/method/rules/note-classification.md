---
type: rule
status: current
authority: rationale
---

# Every note carries a classification

**Gate:** `ci/gates/frontmatter.py`

A note under the spine or a per-component root declares type, status and authority, each from a closed enumeration that names the note class every value covers. A spine note never declares normative authority.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/frontmatter.py`](../../../ci/gates/frontmatter.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
