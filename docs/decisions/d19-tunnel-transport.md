---
type: decision
status: current
authority: decision
---

# D19 — The v1 tunnel is a WebSocket over TLS on the standard HTTPS port

**In force.** For the first release a sidecar reaches the proxy over a WebSocket on 443, and the
contract's own frames ride inside it. An HTTP/2 stream and a raw TLS connection are both ruled out
for v1 — but only for v1, and only as transports.

The choice is not an aesthetic one. The sidecar lives in the tenant's infrastructure, where egress
policy belongs to somebody the operator will never meet, and a WebSocket over TLS on the standard
port is the thing that survives corporate egress rules, transparent proxies and inspecting firewalls
in practice. The two rejected options each lost on a concrete hazard rather than on taste: HTTP/2
would stack its own per-stream flow control underneath the contract's credit windows, and raw TLS is
the most likely of the three to be dropped by a policy that only permits recognisable HTTP. Read this
alongside D2 and note what it does *not* do: the framing stays transport-independent and the listener
specification deliberately describes the endpoint without naming a transport, so a later move is a
change of transport, not a redesign.

- **Full entry, with rationale and alternatives:** [register D19](../../openspec/changes/rebuild-plugboard/design.md#d19--the-v1-tunnel-is-a-websocket-over-tls-on-the-standard-https-port)
- **Shapes:** [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
