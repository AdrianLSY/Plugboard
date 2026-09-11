---
type: capability
status: current
authority: rationale
---

# Code standards

**`docs/code-standards`** — the code guide as a cited artifact rather than a set of opinions.

The organising property is one line inherited from the methodology: *a rule with no gate is a wish.*
So this capability is arranged by enforcement rather than by topic. Every rule names the gate that
enforces it or is explicitly marked as carrying none, and the correspondence is checked in both
directions — a gate naming no rule note fails, and a rule note claiming a gate that is not run fails
too. One-directional checking would still permit a lint rule nobody can find the rule for, which is
how a check becomes folklore.

Unenforced rules are not banned, because some genuinely are taste. They are quarantined, marked as
preference, and barred from being raised as blocking objections — and the proportion of them is
retrievable, so a guide sliding toward unenforced opinion is a visible number rather than a feeling.

The part that earns its cost: a gate's failure output names its rule note. The contributor who trips
a check is handed the defect it prevents and the citation for it, at the one moment they are
guaranteed to be paying attention.

## What it owns

- Each component's boundary, stated once, with every other mention linking rather than restating
- The rule-to-gate correspondence, in both directions, keyed on one enumeration
- The quarantine for unenforced rules, and the retrievable proportion of them
- Each banned pattern as an individually addressable note with its cited defect
- The procedures for adding a feature and fixing a bug, each naming its own verification
- Testing discipline as rules — the tiers, the latency budget, and the four prohibitions on test shape
- Per-language conventions, keyed on the languages actually present
- The requirement that every gate is demonstrated to fail on a deliberately violating input

## What it does not own

- The documentation surface itself — [the knowledge base](docs-knowledge-base.md)
- Any product behaviour; a rule here constrains how code is written, never what it does

## Depends on

- [the knowledge base](docs-knowledge-base.md) — a rule note is a note, so it carries a
  classification, resolves its links, and may not state owned behaviour

## Shaped by

- [D21 — Rebuild from scratch](../decisions/d21-rebuild-from-scratch.md) — every rule here is derived
  from a cited failure in 27,000 lines of prior art rather than from taste
- [D27 — Observability before the hot path](../decisions/d27-observability-first.md) — the same
  substitution of structure for discipline: assert the handler, not the intention

## The specification

[`docs/code-standards`](../../openspec/specs/docs/code-standards/spec.md)
owns the behaviour. Where this note and it disagree, it wins.

The specification merges two deltas, both archived on 2026-09-12: the structural one from
[restructure-docs-as-vault](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/specs/docs/code-standards/spec.md), and the
gate-soundness one from [harden-vault-harness](../../openspec/changes/archive/2026-09-12-harden-vault-harness/specs/docs/code-standards/spec.md),
which added the requirements that make a check's *enforcement* visible — that a runner executes
it, that a generator is held to a pinned expectation rather than its own re-run, that a fixture
declares the failure it demonstrates, that a coverage line asserts what the run did, and that two
encodings of one set are reconciled.
