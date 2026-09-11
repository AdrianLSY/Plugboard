---
type: rule
status: current
authority: rationale
---

# Every link resolves, anchors included

**Gate:** `ci/gates/links.py`

A link to a repository path resolves to an existing file; a link carrying a fragment resolves to an anchor the target actually provides. Every unresolved link is reported in one run, and a missing anchor is distinguished from a missing file.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/links.py`](../../../ci/gates/links.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
