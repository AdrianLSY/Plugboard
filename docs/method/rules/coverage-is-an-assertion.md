---
type: rule
status: current
authority: rationale
---

# A gate's reported coverage is an assertion about the run

**Gate:** `ci/gates/coverage.py`

Every gate reports, on every run including a passing one, how many subjects it examined, what kind of
item it counted, and where that set came from — the tracked index, a directory scan, or a declared key
in `ci/vault.json`. All three are what the run did. The count is produced by the shared reporter from
subjects a gate registers as it examines them, so a gate cannot hand over a number. A run outside a
work tree cannot claim the tracked index. A gate that fails about an item its count excludes has
examined a subject it did not report. An empty subject set is declared, with its reason and the work
that ends it, or it fails — and once that work is complete while the set is still empty, it fails
again.

## Why

A coverage line existed before this rule and nothing read it. That is not a hypothetical gap: a
citation gate once printed `citations checked: 0` and exited zero, and it was caught by a person
reading a line they had added minutes earlier rather than by any check
([`ci/gates/citations.py`](../../../ci/gates/citations.py)). The call was present and correct in
shape; the run examined nothing.

The three-valued source is the part that looks like a detail and is not. Offered only *index* or
*scan*, the six gates whose set comes from a declared manifest key must report something false — and
this rule would then fail them for the report it forced. A rule that manufactures the violation it
punishes gets switched off, so the vocabulary matches the ways a subject set is actually obtained.

The count and the failures are checked against each other rather than against an oracle, because no
oracle exists: nothing outside a gate knows what it looked at. What is decidable is that a gate which
names a file in a failure has examined that file, so the reported count cannot be smaller than the
distinct subjects its own failures name.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/coverage.py`](../../../ci/gates/coverage.py) for exactly what it decides — and what
it deliberately does not.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
