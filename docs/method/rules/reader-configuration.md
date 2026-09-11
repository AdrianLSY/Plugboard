---
type: rule
status: current
authority: rationale
---

# Reader settings are tracked; per-person state is not

**Gate:** `ci/gates/reader_config.py`

The settings that change how links resolve and how notes are classified are tracked, with their values checked rather than merely their presence. Pane layout, per-person hotkeys and caches are not repository state.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/reader_config.py`](../../../ci/gates/reader_config.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
