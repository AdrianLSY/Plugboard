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

`.claude/` and `.agents/` are outside the grant, and the exclusion is stated in
[`LICENSE`](../../LICENSE) itself rather than only in notices: §4(d) of the Apache text says a
`NOTICE` cannot modify the License, so an exclusion carried only there sits where the licence
disclaims it. Both are vendored agent harnesses. The Claude harness retains the provenance gap
[the supply-chain rule](../method/supply-chain.md) exposed; the Codex harness records its OpenSpec,
Matt Pocock and HumanLayer sources, Matt Pocock content hashes and required MIT notices. → [Claude notice](../../.claude/THIRD-PARTY-NOTICES.md)
· [Codex notice](../../.agents/THIRD-PARTY-NOTICES.md) · [Codex lock](../../skills-lock.json)

- **Full entry, with rationale and alternatives:** [register D28](../../openspec/changes/rebuild-plugboard/design.md#d28--licensing-apache-20-over-the-authored-tree)
- **Deferred with it:** [follow-ups](../method/follow-ups.md) — the implementer patent position, the
  provenance of the vendored harness, and the dependency-licence audit, each with the work that ends
  it.

> The register wins where this note and it disagree.
