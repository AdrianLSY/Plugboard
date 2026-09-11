---
type: capability
status: planned
authority: rationale
---

# Mount points

**`routing/mount-points`** — the hierarchy of paths a tenant registers, and the rule that turns an
inbound request path into exactly one destination plus a leftover.

Every request the proxy handles begins with one question: which registered location does this path
belong to, and what remains of the path once that location's prefix is taken off the front? A **mount
point** is a node in the hierarchy that is eligible to receive proxied traffic; a node that exists but
is not a mount point is reachable by no request at all. The leftover is the **remainder**, and it is
the sole input from which a backend request is later composed. Those three words — node, mount point,
remainder — are defined in [the glossary](../glossary.md#routing) and used in that sense everywhere.

The one idea worth carrying away is that a mount point is **terminal**: it has no children, and that
is a data-model invariant rather than a convention. Terminality is what makes longest-prefix matching
provably unambiguous. If `/a/b` is a mount, no `/a/b/c` mount can exist, so strip-a-segment-and-retry
arrives at the single correct answer with no trie, no ordering and no tie-break rule. The prior art
had the invariant, enforced from both directions by two locking triggers
(`20251031092344_create_paths_table.exs:96-107`), and nowhere recorded that the hot path's correctness
depended on it — the coupling most likely to be lost in a rewrite, per
[carry-forward](../history/carry-forward.md#terminal-mount-invariant).

Matching is deliberately the narrow end of the funnel. It yields a mount and a remainder and stops
there: it chooses no sidecar, opens no connection, and reads nothing from the request but its target.

## What it owns

- the single-parent node hierarchy, and the terminal-mount invariant over it
- longest-prefix matching on undecoded segment boundaries, and the derived remainder
- the closed enumeration of path prefixes the proxy reserves for itself
- segment charset, depth and length bounds, and refusal of traversal sequences
- the lifecycle of a path — rename, subtree move, cascading deletion, recovery
- the per-instance lookup surface, and its convergence, divergence and staleness

## What it does not own

- picking which registered sidecar serves the matched mount — [sidecar registry](tunnel-sidecar-registry.md)
- reaching a mount by hostname instead of by prefix — [custom domains](routing-custom-domains.md)
- composing a backend request out of the remainder — [HTTP fidelity](proxy-http-fidelity.md), then [the sidecar program](sidecar-program.md)
- who may create, move or delete a node — [tenant isolation](tenancy-isolation.md)

## Depends on

- [tenant isolation](tenancy-isolation.md) — fixes *node*, *instance* and *installation* for the whole set, and owns the authority to change a path
- [observability](operability-observability.md) — a staleness or divergence bound that is not visible is not a bound

## Shaped by

- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — every matching instance holds a lookup surface of its own, so convergence and divergence are properties of the installation
- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — a node's tenancy is structural, not a filter a caller remembers
- [D10 — Carry-forward is explicit and cited](../decisions/d10-carry-forward.md) — the invariant and the matching algorithm are re-derived from a citation rather than from memory

## The specification

[`routing/mount-points`](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
