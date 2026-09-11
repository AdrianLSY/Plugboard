---
type: rule
status: current
authority: rationale
---

# A generated artifact is verified against something other than its generator

**Gate:** `ci/gates/generators.py`

Each generator is runnable against a tree root other than this repository, and is pinned to a tracked
oracle: a small input tree, and the exact output it is expected to produce on that tree. A run whose
output differs from the expectation fails, naming the generator, the expectation and the first
differing line. The declaration is keyed on the tool rather than the artifact, and is complete both
ways. Each generator states, in its own module, the class of wrongness its input does not reach.

## Why

[`ci/gates/index_drift.py`](../../../ci/gates/index_drift.py) verifies a generated file by re-running
its generator and byte-comparing. That is sound against a hand edit and no check at all against a
wrong generator, because wrong output is produced consistently and so verifies as current. Replacing
one expression in [`ci/gen/indexes.py`](../../../ci/gen/indexes.py) relabelled every note in the vault
and `make check` exited zero; the same corruption against the pinned expectation fails on the first
differing line. Both halves of that were run rather than reasoned about.

The expectation is tracked rather than computed, because an expectation computed at check time is the
generator again. Each fixture is small enough to verify by reading, which is what makes it an oracle
and not a snapshot — so what it catches is drift from behaviour someone confirmed, and each generator
says where that confirmation stops.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
