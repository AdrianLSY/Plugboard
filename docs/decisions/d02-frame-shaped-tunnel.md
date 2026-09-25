---
type: decision
status: current
authority: decision
---

# D2 — The tunnel exchange is frame-shaped

**In force.** What crosses the tunnel is a frame carrying a stream identifier, never a message
carrying a whole request or a whole response. That forecloses any design in which one exchange is
one unit on the wire, and with it the correlation-id bookkeeping such a design needs.

The practical consequence is that the frame vocabulary is fixed up front and larger than v1 uses:
every frame type is reserved at v1 even where nothing implements it, and every body octet
participates in both credit windows even where a window is effectively infinite; the liveness exchange
and the datagram class are exempt from credit. Reserving costs nothing now; adding a
frame type after sidecars are deployed splits the fleet, which is the asymmetry the whole contract is
organised around. One thing is deliberately still open, and a reader should know it before treating
the vocabulary as final: the register records a standards-track alternative — capsule framing from
the HTTP/2 WebTransport draft — as strongly recommended for evaluation while `tunnel/wire-contract`
is being built, held back only because no server library implements it yet. The frame *shape* is
settled; which encoding of that shape ships is a question that work is expected to answer.

- **Full entry, with rationale and alternatives:** [register D2](../../openspec/changes/rebuild-plugboard/design.md#d2-the-tunnel-exchange-is-frame-shaped)
- **Shapes:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md), [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
