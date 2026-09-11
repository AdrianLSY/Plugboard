---
type: rule
status: current
authority: rationale
---

# Relations are relative markdown links

**Gate:** `ci/gates/wikilinks.py`

Wiki-style link and transclusion syntax do not appear in a tracked note, and neither does an absolute filesystem path or a reader-only URI. One syntax serves a person reading rendered output, an agent resolving a path, and a checker.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/wikilinks.py`](../../../ci/gates/wikilinks.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
