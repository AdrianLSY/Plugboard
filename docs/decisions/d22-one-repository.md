---
type: decision
status: current
authority: decision
---

# D22 — One repository

**In force.** Every component lives in a single tree, and the two git submodules it replaces are
gone along with the sync workflow that auto-committed unreviewed pointer updates onto the parent's
default branch. It rules out submodules returning, and
[a CI guard](../code/rules/no-submodules.md) enforces that rather than trusting anyone to
remember — both the declaration file and the gitlink entry, because either survives the other.

The part worth reading twice is what this decision explicitly does *not* buy. One tree makes the
repository internally consistent and does nothing whatever for production, where the sidecar
versions in tenant infrastructure spread without bound; reading a monorepo as evidence that the two
halves agree is precisely the mistake the entry warns against, which is why it is recorded next to
[D24](d24-version-skew.md) rather than offered as a mitigation of it. The cheaper alternative —
keep the submodules and put a human approval in front of the pointer-update workflow — was rejected
for leaving a two-repository release surface under a contract whose whole point is one schema
generating both sides. This was `D2` in the register since removed, so check the
[collision table](superseded-register.md) before trusting an old `D2` citation.

- **Full entry, with rationale and alternatives:** [register D22](../../openspec/changes/rebuild-plugboard/design.md#d22--one-repository)
- **Shapes:** [operability/packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
