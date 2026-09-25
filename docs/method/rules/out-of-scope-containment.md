---
type: rule
status: current
authority: rationale
---

# A declared out-of-scope path lies outside its declarant's tree

**Gate:** `ci/gates/out_of_scope.py`

A path a change declares out of its own scope may not lie inside that change's own directory under
`openspec/changes/`, nor contain it. The owner of this property is
[D31](../../decisions/d31-out-of-scope-containment.md), not the knowledge-base specification: that
specification holds the byte-unchanged requirement
[its sibling rule](out-of-scope-byte-unchanged.md) enforces, and says nothing about who may declare.

## Why

The byte-unchanged assertion cannot observe which change is editing, so a change that declares its own
artifacts out of scope is refused every revision to them. That is the arrangement `rebuild-plugboard`
carried over its sixteen specifications until task 3.16 emptied the declaration, and every gate stayed
green through it because the field naming the declarant is read for a message and not for a decision.
D31 records the mechanism and what the invariant costs: it constrains who may declare, which is weaker
than the freeze was believed to be.

The gate's failure output names D31, so tripping it hands you the decision rather than a verdict.
Read [`ci/gates/out_of_scope.py`](../../../ci/gates/out_of_scope.py) for exactly what it decides — and,
where it matters, what it deliberately does not.
