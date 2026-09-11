---
type: decision
status: current
authority: decision
---

# D26 — WebTransport is designed for, not shipped

**In force.** The tunnel is defined in terms of the primitive WebTransport would need —
independent streams plus datagrams — and the datagram frame class is reserved in the contract now.
No WebTransport or HTTP/3 edge ships in v1. It rules out building the first version around whatever
a single ordered TCP connection happens to offer, and equally rules out adding the QUIC edge early
to prove the point.

The trap this exists to avoid is worth knowing before writing any transport code: one ordered
stream invites correlation identifiers, a pending-request map, one reply per request and no
backpressure, and swapping the transport afterwards then means deleting the middle of the tunnel. So
any TCP-based transport is an emulation of the defined primitive, never the shape the primitive is
derived from. Reserved-but-unimplemented is the intended state here, not an unfinished edge, and the
deferred terminator is what would eventually fill it. Note the number: this was `D10` in the
register that has since been removed, so an older citation of `D10` means this decision, while
today's `D10` is a different one about carry-forward.

- **Full entry, with rationale and alternatives:** [register D26](../../openspec/changes/rebuild-plugboard/design.md#d26--webtransport-is-designed-for-not-shipped)
- **Shapes:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
