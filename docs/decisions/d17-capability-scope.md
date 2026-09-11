---
type: decision
status: current
authority: decision
---

# D17 — Five further capabilities are in scope; three are deferred with their dependencies named

**In force.** Five capabilities that no earlier spec owned are specified here — the sidecar as a
deployable program, certificate and private-key custody, the tunnel listener, durable schema
migration, and packaging for every deployable — and three others are deferred by name, each with
the dependency its absence leaves behind. It rules out the state that produced it, in which
behaviour existed only in the assumption that some other specification covered it.

The consequence for anyone reading the specs is that ownership is now answerable: if you cannot
find the capability that owns a behaviour, that is a finding worth raising, not a gap to fill
wherever you happen to be working. Two of the deferrals still bind v1 rather than waiting: an
administrative path prefix and a control-surface hostname are reserved now so the later control
plane cannot be locked out of its own namespace, and audit retention carries a contradiction that
is recorded rather than discovered — an append-only, immutable trail against an erasure obligation
— which needs a stated resolution before either side is implemented.

- **Full entry, with rationale and alternatives:** [register D17](../../openspec/changes/rebuild-plugboard/design.md#d17--five-further-capabilities-are-in-scope-three-are-deferred-with-their-dependencies-named)
- **Shapes:** [operability/packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md), [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md), [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md), [security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
