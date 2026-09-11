---
type: decision
status: current
authority: decision
---

# D6 — Framing authority is per-hop, never relayed

**In force.** Each hop declares for itself how long the thing it is sending is, or that it is
chunked, and never repeats what the hop before it said. A message that arrives carrying
contradictory framing is refused at the edge. That forecloses reconciling the two declarations, and
it forecloses passing either field through to the next hop as a convenience.

This is the request-smuggling boundary, which makes it the decision most easily undone by a change
that looks harmless: a header collection copied wholesale, or a declared length forwarded
"unchanged" across a path whose octet count is not the same. Several of the banned patterns in
`CLAUDE.md` exist only to catch that, and the reference relayed the length verbatim over exactly
such a path. Anyone touching header handling on either side of the tunnel should read this before
concluding a field is safe to relay — the tunnel frames data explicitly, so nothing downstream needs
the previous hop's framing fields to interpret it. Cited as `D12` before the registers were
consolidated; that number is retired.

- **Full entry, with rationale and alternatives:** [register D6](../../openspec/changes/rebuild-plugboard/design.md#d6-framing-authority-is-per-hop-never-relayed)
- **Shapes:** [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md), [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
