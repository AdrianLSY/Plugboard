---
type: decision
status: current
authority: decision
---

# D3 — Capability negotiation, with refusal rather than degradation

**In force.** A sidecar states what it can do when it joins the tunnel, and a request or a mount the
connected sidecar cannot back is refused outright, with a status and a stated reason. Best-effort
degradation is ruled out: there is no path in which the proxy quietly does less than was asked.

This is the decision that makes "refuse, never degrade" a mechanism rather than a slogan, and the
reason it is load-bearing is topological. Selection already spreads a mount's requests across every
eligible sidecar, so if fidelity could silently vary by sidecar version, two identical requests to
one URL would differ non-deterministically — the failure mode nobody can debug and everybody reports
as "it worked yesterday". Refusal converts that into a single legible answer at the moment of the
request. When reading a specification that seems unhelpfully strict about naming a cause, this is
usually why.

- **Full entry, with rationale and alternatives:** [register D3](../../openspec/changes/rebuild-plugboard/design.md#d3-capability-negotiation-with-refusal-rather-than-degradation)
- **Shapes:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md), [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
