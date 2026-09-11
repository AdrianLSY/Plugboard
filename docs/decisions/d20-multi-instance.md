---
type: decision
status: current
authority: decision
---

# D20 — The proxy is a multi-instance installation in v1

**In force.** Version one runs several proxy processes under one operator's configuration, and a
tenant's sidecar holding a tunnel to one of them is served by all of them. That rules out the two
cheaper stories: pinning a tenant's client traffic to whichever process its sidecar dialled, and
redirecting clients to that process — the first makes every process loss a tenant outage, the second
is visible to callers and breaks requests that cannot be retried.

This began as unplanned scope, and that history is the point. The cross-process requirements were
already written into the registry work before anyone asked whether v1 was clustered; an audit of the
task list found them and the decision was to keep them rather than shrink them, so this is confirmed
scope, not an assumption anyone can quietly drop. Two things follow for reading the specifications.
The vocabulary is fixed and was renamed across eight of them: *instance* is one running process,
*installation* is the whole set, and *node* means an entry in the mount-point hierarchy and never a
machine. And any per-tenant ceiling counted against one instance's own observation is a conformance
failure, because it would hand a tenant one allowance per instance; the single exception is a bound
that has to be applied before the other party is even identified, and a capability claiming it must
say so and say why.

- **Full entry, with rationale and alternatives:** [register D20](../../openspec/changes/rebuild-plugboard/design.md#d20--the-proxy-is-a-multi-instance-installation-in-v1)
- **Shapes:** [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md), [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
