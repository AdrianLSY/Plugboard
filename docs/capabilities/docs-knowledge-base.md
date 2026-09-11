---
type: capability
status: planned
authority: rationale
---

# The knowledge base

**`docs/knowledge-base`** — the documentation surface as a checked artifact rather than a set of
habits.

Every other capability in this repository describes how the product behaves. This one describes how
the repository describes itself, and it exists because prose is simultaneously the most valuable
thing here and the largest liability. The prior art carried 148 KB of it against a history of commits
titled `updated code`, and two of its documented claims were verifiably false — not because anyone
lied, but because nothing could tell the difference between a claim and a guess.

So the obligations here are gates rather than conventions. A note carries a classification. A link
resolves, anchors included. A relation is a relative markdown link, so the same syntax serves a
person reading rendered output, an agent resolving a path, and a checker. A cited artifact is
obtainable, with its revision pinned, so a citation is checkable by someone other than its author.
And a note may not state behaviour a specification owns — which is what keeps a second, drifting copy
of the truth from accumulating in the place people actually read.

The one property worth singling out: currency runs in **both** directions. A note whose subject was
deleted fails, and so does a note still marked planned once its subject exists. Only the second
direction will get much exercise here, because almost nothing is built yet and everything is about to
be.

## What it owns

- The vault's root, its spine, and the declared set of governed and exempt roots
- The classification every note carries, and the closed enumerations it draws from
- Link discipline, link resolution, and reachability from a declared entry point
- The authority precedence, and the rule that a note never states owned behaviour
- The single decision register, retired identifiers, and per-change namespacing
- Currency in both directions, and the obtainability of anything cited

## What it does not own

- How code is written or placed — [code standards](docs-code-standards.md)
- Any product behaviour whatsoever; it ranks the artifacts that state behaviour without stating any

## Depends on

- [code standards](docs-code-standards.md) — the two share one convention source, so a rule added to
  the gates without reaching both authoring channels fails

## Shaped by

- [D21 — Rebuild from scratch](../decisions/d21-rebuild-from-scratch.md) — the prior art is prior art,
  which is why its citations need obtaining instructions rather than a working tree
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — sort by
  reversibility; documentation is the most reversible thing here, and its structure is cheap to change
  and expensive to leave wrong

## The specification

[`docs/knowledge-base`](../../openspec/changes/restructure-docs-as-vault/specs/docs/knowledge-base/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
