---
type: decision
status: current
authority: decision
---

# D8 — Tenant scoping in the data model, not in queries

**In force.** Which tenant a row belongs to is part of how the data is keyed and how a mutation is
called — not a filter a query author is trusted to remember. Every projection is tenant-keyed and
every context mutation names the principal acting, which rules out the ordinary alternative: correct
isolation as a property of each call site adding the right clause and each writer checking permission
by habit.

A reader navigating this project should expect to find tenancy in signatures and keys, and should
treat its absence there as the defect rather than looking for the missing check further in. Two
consequences follow for how code is read: a function that changes tenant-owned state without an actor
in its signature is wrong before its body is read, and a read path whose work grows with the number of
tenants when one tenant changes something is wrong even when it returns the right rows. This decision
is downstream of [D25](d25-positioning.md) rather than a matter of taste — the dev-tunnel positioning
that was recommended and not chosen is the one under which this could have stayed a later feature — so
re-opening it means re-opening the positioning, not just the data model.

- **Full entry, with rationale and alternatives:** [register D8](../../openspec/changes/rebuild-plugboard/design.md#d8-tenant-scoping-in-the-data-model-not-in-queries)
- **Shapes:** [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), [routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md), [auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
