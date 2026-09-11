---
type: decision
status: current
authority: decision
---

# D16 — HTTP/2 to clients is in v1, and the edge listener is a separate component from the start

**In force.** The proxy speaks HTTP/2 to clients in the first release, and because the Elixir web
server it would otherwise use cannot do that, the component terminating client connections is a
separate contract-speaking process from day one. It rules out an HTTP/1.1-only edge with the
protocol slot reserved but unused, and it rules out treating a second edge component as later work.

This overturns the project's earlier instinct. The risk register had said not to add a separate
terminator until HTTP/3 or WebTransport forced one; D16 concludes that HTTP/2 already does, so the
cost lands now, on purpose, instead of arriving as a surprise. Two consequences a reader should
carry: the terminator is real v1 scope rather than speculation, and the edge obligations in the
specifications are written to bind whichever component terminates the connection, not "the proxy".
The decision was also written down because the specifications had begun to assume it by
implication, which is not how the edge topology gets decided. Before reopening "could the edge just
be HTTP/1.1 for now" — that alternative was considered and rejected, because behind a CDN that
terminates HTTP/2 a WebSocket handshake never looks like an HTTP/1.1 upgrade and the feature fails
silently, which is precisely the reference's defect.

- **Full entry, with rationale and alternatives:** [register D16](../../openspec/changes/rebuild-plugboard/design.md#d16--http2-to-clients-is-in-v1-and-the-edge-listener-is-a-separate-component-from-the-start)
- **Shapes:** [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md), [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
