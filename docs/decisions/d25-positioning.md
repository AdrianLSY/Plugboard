---
type: decision
status: current
authority: decision
---

# D25 — Positioning: multi-tenant platform ingress

**In force.** What this system is, first sentence and pitch, is ingress for a platform hosting many
tenants. It rules out the alternative that was actually recommended — self-hosted developer tunnels as
the front door, with multi-tenant routing arriving later as an extension.

The reader most needs to know that this went against the recommendation and was decided by the owner
anyway, with the cost named rather than discovered. Dev tunnels would have been demoable in half a
minute and would have let three things be deferred: projections keyed by tenant, authorization carried
in signatures, and per-tenant blast radius with an audit trail behind it. Choosing multi-tenant
ingress made all three foundational instead, because the first question a prospect asks is what stops
one tenant affecting another and the answer has to be structural. So when [D8](d08-tenant-scoping.md)
looks like over-engineering for an early version, this is where that argument terminates: it was
priced here, deliberately, and re-opening the isolation work means re-opening the positioning.

- **Full entry, with rationale and alternatives:** [register D25](../../openspec/changes/rebuild-plugboard/design.md#d25--positioning-multi-tenant-platform-ingress)
- **Shapes:** [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), [routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md), [auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md), [operability/observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
