---
type: guide
status: current
authority: rationale
---

# proxy -- the boundary

The canonical statement of what this component owns. A README beside the component links here.

## Violation H -- the paragraph a README copies

The proxy owns every projection that is keyed by tenant, and the mutation signatures over them,
because a projection that is not keyed by tenant is one query away from being a cross-tenant read,
and no review catches that reliably enough to rely on.

See [the component root](../../../proxy/README.md).
