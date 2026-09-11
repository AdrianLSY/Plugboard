---
type: rule
status: current
authority: rationale
---

# A published enumeration and the computed one are reconciled

**Gate:** `ci/gates/correspondences.py`

Where one set is resolved twice by encodings that do not read each other, the pair is declared in
`ci/vault.json` as a named correspondence, each side naming the resolver that produces its members.
Both directions are checked, and a divergence names the members that differ rather than the counts. A
side that resolves to nothing fails; a resolver that cannot run is reported, never raised. A
correspondence both of whose sides come to share one resolver is retired from the declaration with
that resolver recorded.

## Why

`docs/rule-index.md` published "42 rules — 20 gated" while `ci/gates/rule_gate_correspondence.py`
counted 43 and 21 over the same set, and a single `make check` run printed both. The member missing
from the published side was [the authority precedence](../authority-precedence.md), a gated rule
appearing in no row of the index [`CLAUDE.md`](../../../CLAUDE.md) routes every reader to.
[`ci/gates/index_drift.py`](../../../ci/gates/index_drift.py) passed over it because it compares a
generator to its own output and never to the gate's count.

The pairs are declared and not discovered, because three discovery triggers were drafted and measured
first. "Published in a tracked artifact a reader is routed to" produced 361 findings with one true
positive — an in-force requirement already makes almost every tracked subject reachable from an entry
point, so the trigger narrowed nothing at all. Which two encodings resolve one set is a fact about how
this repository was built: a person knows it and a regex cannot recover it.

Members rather than counts, because a count says two encodings disagree and cannot say which member
diverged — and the member is the whole diagnosis. "42 against 43" sent nobody to the note that was
missing.

Retirement rather than deletion, because the rule set's own correspondence closed during this change:
both sides now call one resolver in [`_common.py`](../../../ci/gates/_common.py). Recording the
resolver that closed it means re-opening the divergence requires undoing a named decision instead of
quietly adding a second encoding back.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
