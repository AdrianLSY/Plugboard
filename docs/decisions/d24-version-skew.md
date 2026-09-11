---
type: decision
status: current
authority: decision
---

# D24 — Version skew is the governing constraint

**In force.** You deploy the proxy; tenants deploy sidecars on their own schedule, or never — so
mixed versions are permanent and the asymmetry only runs one way. It rules out any plan that
assumes both halves can be moved together, and it rules out a supported-version window with a
forced-upgrade path.

This is a framing rather than a feature, and it is the reason several other decisions look
expensive: the wire schema is the only artifact you cannot take back, so work is ordered by
reversibility instead of by cost; capability negotiation is mandatory because sidecar selection
will land on old and new versions alike; and anything that requires tenants to change their sidecar
is expensive forever, not once. The rejected alternative is instructive — a version window sounds
like ordinary migration hygiene, but there is no mechanism to force an upgrade of software running
in someone else's infrastructure, so it would be a policy the system cannot enforce and would only
disguise the constraint. This decision was `D4` in the removed register, where `D4` also denoted a
different, once-reversed decision in the surviving one, so an old `D4` citation is ambiguous until
resolved through the [collision table](superseded-register.md).

- **Full entry, with rationale and alternatives:** [register D24](../../openspec/changes/rebuild-plugboard/design.md#d24--version-skew-is-the-governing-constraint)
- **Shapes:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md), [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
