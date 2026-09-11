---
type: decision
status: current
authority: decision
---

# D4 — Runtime: Elixir proxy, Go sidecar, Go H3 terminator later

**In force, and it reverses an earlier recommendation.** The proxy is Elixir, the sidecar is Go, and
the HTTP/3 and WebTransport edge — when something finally forces it — is a separate Go terminator
that speaks the versioned contract. Rust for the proxy is ruled out, and so is the assumption that
one process must terminate both the client edge and the tunnel.

Anyone tempted to reopen this should read *why* it was reversed before arguing the merits, because
the reversal is the useful part. The earlier Rust recommendation rested on claims adversarial review
found to be wrong or fabricated: the recommended QUIC stack does not implement WebTransport at all,
and the two quotations that made in-process HTTP/3 termination sound mandatory do not exist on the
pages they were attributed to. Once WebTransport stopped dictating the runtime, what remained was
the work that has to ship — a distributed sidecar registry with failover, hot-reloadable routing,
per-tenant crash containment, a live admin plane — and that is what the BEAM is chosen for, not
throughput. The strongest surviving objection is not about language: the chosen Elixir server speaks
neither HTTP/3 nor extended CONNECT, so behind an HTTP/2-terminating CDN a WebSocket upgrade never
appears — which is why the client-facing terminator may be a separate, swappable contract speaker.

- **Full entry, with rationale and alternatives:** [register D4](../../openspec/changes/rebuild-plugboard/design.md#d4-runtime-elixir-proxy-go-sidecar-go-h3-terminator-later)
- **Shapes:** [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md), [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md), [operability/packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
