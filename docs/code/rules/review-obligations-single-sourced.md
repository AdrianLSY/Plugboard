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

One artifact is required to *name* every item without restating it:
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md), which a contributor reads before they reach the spine.
Adding an item to a canonical enumeration fails the build until that file names it.

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

## The checkable form is propagation

"Nobody copied the list" is not decidable over prose, and a check that tried would fire on every note
that mentions a checklist. The other direction is decidable, and it is the one that fails in practice:
an artifact required to enumerate the list falls behind it. So the gate derives each item's name from
the canonical enumeration itself — leading bold, else leading link text, else the lead clause — and
fails any required enumerator that does not carry it. A list that cannot silently fall behind has
nothing to drift from.

The item names are derived rather than declared for the same reason the rule exists: a list of them in
`ci/vault.json` would be a second encoding of the enumeration, reappearing inside the check meant to
prevent one.

## What the gate does not reach

Order, a stale entry the canonical list has since dropped, and whether the sentence an enumerator
wraps a name in is true. A green run means no item is missing from a required enumerator — not that
nothing anywhere carries a second copy. That residue is owned by review and by
[one copy of requirement text](../../method/rules/one-copy-of-requirement-text.md), which decides
copy-paste across the spine, the specifications and the component roots.
