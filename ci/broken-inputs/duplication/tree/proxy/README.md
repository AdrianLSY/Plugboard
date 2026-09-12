---
type: guide
status: current
authority: rationale
---

# proxy

## Violation H -- the boundary note's paragraph, pasted instead of linked

The proxy owns every projection that is keyed by tenant, and the mutation signatures over them,
because a projection that is not keyed by tenant is one query away from being a cross-tenant read,
and no review catches that reliably enough to rely on.

The remedy is a link to [the boundary note](../docs/code/boundaries/proxy.md), not a second copy.
