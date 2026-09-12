---
type: rule
status: current
authority: rationale
---

# The review obligations are stated in one location and enumerated

**Gate:** `ci/gates/review_obligations.py`

Three enumerations — [the review checklist](../reviewing.md#the-review-checklist), [the
change-description questions](../reviewing.md#the-change-description-questions) and [the set of
blocking objections](../reviewing.md#blocking-objections) — are each stated in exactly one location,
numbered so an item is cited by its number. Every other mention links to that anchor rather than
carrying its own copy of the list.

## Why

A checklist is the kind of text that gets pasted into whatever artifact needs it next — a
`CONTRIBUTING.md`, a PR template, an agent context file — and the copies then diverge silently,
because nothing fails when one of them is left behind. The prior art shows both halves of that
failure. `ws_check`, one of the tunnel's own messages, appears nowhere in the 457 lines of prose
documenting that protocol, and where the two ends were documented they had already drifted: the Go
side hardcodes a three-second check timeout (`websocket.go:339`) against a configurable five on the
Elixir side. And a second copy of behaviour can survive as a plain falsehood — `proxy_controller.ex:51`
is a doc comment claiming errors are logged, in a code base whose `lib/` contains no `Logger` call at
all. Both are in [the reference audit](../../history/reference-audit.md).

One copy and a link has no drift to detect. That is why this rule is about location rather than about
wording: numbering exists so a reviewer can say "checklist item 4" and a contributor can find item 4,
without a second list to disagree with the first.

## What the gate decides

The checkable form of the rule is propagation: adding an item to a canonical enumeration fails every
artifact required to enumerate it until that artifact names the new item, and the failure lists each
artifact still missing it. That check needs at least one artifact under the obligation to enumerate,
and until [`CONTRIBUTING.md`](../../../CONTRIBUTING.md) existed there was none — a gate written then
would have passed on every input, which is worse than no gate, because it would read as enforcement
over an unguarded obligation.

Both halves landed together, which is what rebuild-plugboard task 1.3 asks for. The gate reads the
item numbers from [reviewing](../reviewing.md) rather than from a declared count, so the enumerations
cannot drift from the check that propagates them; `ci/vault.json` declares only the canonical note,
the obliged artifacts and the citation form.

What it does **not** decide is wording. An obliged artifact cites an item by number and puts its own
short handle beside it; nothing compares that handle to the canonical text. That is the rule's own
shape — it is about location rather than wording, and a second copy of the wording is what
[the duplication gate](../../method/rules/one-copy-of-requirement-text.md) already refuses.

Beyond the propagated enumerations, the single-sourcing stays a property a reader checks by hand,
and a small one: the three enumerations live in [reviewing](../reviewing.md), and every artifact that
needs one of them —
[adding a feature](../adding-a-feature.md), [fixing a bug](../fixing-a-bug.md),
[testing](../testing.md) — links into that note instead of listing items again.
