---
type: rule
status: current
authority: rationale
---

# No submodules, and no gitlink left behind

**Gate:** `ci/gates/no_submodules.py`

The repository holds no `.gitmodules` at its root and no tracked path recorded with mode `160000`.
Both halves are checked, because either survives the other: deleting the declaration leaves the
gitlink, and the gitlink is what pins a revision from a repository nobody here reviews.

This is [D22](../../decisions/d22-one-repository.md) made enforceable. The decision note says a guard
does this "rather than trusting anyone to remember"; this is the guard.

## Why

The prior art was two repositories joined by submodules, with a sync workflow that auto-committed a
pointer update onto the parent's default branch on every push to the sidecar's default branch. A
protocol change therefore reached the parent's `main` having been reviewed by nobody — on a wire
contract whose entire premise is that both halves are generated from one schema
([reference audit](../../history/reference-audit.md)).

What one repository does *not* buy is worth stating beside the rule, because reading it the other way
is the more expensive mistake: a single tree makes this repository internally consistent and does
nothing at all for production, where sidecar versions in tenant infrastructure spread without bound.
That is [version skew](../../why/version-skew.md), and no repository layout touches it.

## What it does not reach

Vendoring by other means — a copied directory, a lockfile pointing at a fork, a build step that clones
at run time. Those are the supply chain's, not this rule's;
[dependencies and supply chain](../../method/supply-chain.md) is where that is owned.
