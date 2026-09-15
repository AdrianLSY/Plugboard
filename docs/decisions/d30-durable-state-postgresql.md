---
type: decision
status: current
authority: decision
---

# D30 — Durable state is held in PostgreSQL

**In force.** Every durable store the proxy installation itself operates is PostgreSQL. It binds the
proxy and nothing else — no specification gives the client-facing terminator durable state, and a
sidecar starts from local configuration inside the tenant's own infrastructure — so nothing settled
here reaches anything a tenant deploys. It rules out a store embedded in the proxy process, and it
rules out a key-value or document store.

What is worth reading twice is that this was in force before it was decided. The integration tier
names the product, a task requires notification delivery proven against it, and the integration CI job
stands up a container of it — all while the register held no entry and the open list named no
question. By this repository's own rule a thing is decided when the register holds it with its
rationale and open when it is listed as undecided, and
[anything else is neither](../start-here.md#conventions). So the transferable finding is not about
databases: an assumption written into three artifacts and stated in none is a duplication defect whose
original is missing, and every gate here reconciles copies against an original. That is the one shape
they are all blind to, and it is worth going looking for rather than waiting to trip over.

The second thing is where the cost of the choice actually falls, which is not the operational place
people reach for. A database to run, back up and upgrade is real, and its blast radius is bounded:
mutations stop while traffic continues, because a lookup is already obliged to complete against the
last loaded state with the store unreachable. The structural cost is that part of the system's
correctness moves into the store, invisible to the type system and out of reach of the tier a
contributor runs on save — the terminal-mount invariant [D10](d10-carry-forward.md) calls
load-bearing needs a lock on a parent row that a concurrent sibling insert has to respect, and
`routing/mount-points` makes that enforcement the store's rather than any one writer's. That cost has
been paid once already and never collected: every "concurrent" test in the reference ran on a single
shared sandbox connection, so those locks were never once contended. Choosing this store means owning
[the contended test the reference never had](../history/carry-forward.md#the-terminal-mount-invariant-and-its-coupling-to-the-lookup-algorithm).

The third is the one that keeps this off the irreversible list. No tenant pins a database version and
nothing a tenant deploys can observe the choice, so [D24](d24-version-skew.md)'s asymmetry does not
reach it: changing the engine costs one component's rewrite and one migration, paid once, by one
party, with no tenant action at all. Expensive, bounded, and categorically unlike a schema decision,
which cannot be paid at any price.

- **Full entry, with rationale and alternatives:** [register D30](../../openspec/changes/rebuild-plugboard/design.md#d30--durable-state-is-held-in-postgresql)
- **Shapes:** [routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md), [operability/schema-migration](../../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md)

> The register wins where this note and it disagree.
