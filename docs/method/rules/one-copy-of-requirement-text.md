---
type: rule
status: current
authority: rationale
---

# Requirement text has one copy

**Gate:** `ci/gates/duplication.py`

A requirement paragraph appears once, and every other place links it. The check runs across three
sides — the spine, the specifications, and the per-component roots — and fails on a block carried by
two of them. A component README copying its boundary note is the third side's reason for existing:
[a component's boundary is stated once](../../code/rules/component-boundary-stated-once.md) catches
only the heading form of that copy, and a paste under any other heading is invisible to it.

This decides copy-paste and does not decide paraphrase; drift is owned by the authority-precedence
rule and by review.

## Why

Recorded in the gate's own module docstring, which states the defect this prevents and what the check does not decide.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/duplication.py`](../../../ci/gates/duplication.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
