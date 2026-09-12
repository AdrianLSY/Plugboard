---
type: decision
status: current
authority: decision
---

# D28 — Licensing: Apache-2.0 over the authored tree

**In force.** One `LICENSE` at the repository root, Apache-2.0, over the work this repository
authors. It rules out the alternative with the strongest precedent behind it — AGPL-3.0 on the proxy
with Apache-2.0 on everything a third party embeds, split at the deployment boundary, which is what
MongoDB, Element, Grafana and Teleport each converged on.

The reader most needs to know that the unlicensed state this replaces was a defect rather than a
pause. The README asks for a full-history clone and a `make check`, and an unlicensed repository
grants no clear right to perform either — in a project whose whole claim is that its assertions are
checked rather than believed. That collision is internal and needs no market argument to carry it.
[D24](d24-version-skew.md) settles the timing: a licence on published bytes is irreversible and
everything around it is not, so this sorts by reversibility, and the window is widest at zero outside
contributors.

The second thing worth knowing is what the licence does not buy. Its patent grant runs to whoever
uses, copies or embeds these files; someone who reads
[the wire contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) and
writes a sidecar from scratch never becomes a licensee and receives no patent licence at all. The
specification projects that closed that gap reached for a specification instrument rather than a
software licence. The gap is open here, recorded rather than papered over, and becomes live when
`contract/` first ships files a third party embeds.

`.claude/` is outside the grant. It is a vendored agent harness: the openspec skills declare a
licence, and every other skill and slash command declares none — the defect
[the supply-chain rule](../method/supply-chain.md) logs against the prior art, found in this tree
while writing this decision. → [third-party notices](../../.claude/THIRD-PARTY-NOTICES.md)

- **Full entry, with rationale and alternatives:** [register D28](../../openspec/changes/rebuild-plugboard/design.md#d28--licensing-apache-20-over-the-authored-tree)
- **Deferred with it:** [follow-ups](../method/follow-ups.md) — the implementer patent position, the
  provenance of the vendored harness, and the dependency-licence audit, each with the work that ends
  it.

> The register wins where this note and it disagree.
