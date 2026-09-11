---
type: capability
status: planned
authority: rationale
---

# WebSocket

**`proxy/websocket`** — what the client observes when a bidirectional frame stream is established
through a mount point, and what a shared proxy is protected from while that stream is open.

The second of the three primitives differs from the first in one way that changes everything about
it: it has no end. A request/response exchange is bounded by its own shape, so most of its policy is
about deadlines; a frame stream is bounded only by policy the proxy chooses, so this capability is
mostly about the bounds — origin and concurrency admission, a decompressed-message ceiling, liveness,
idle and lifetime separate from any request bound, backpressure on the client hop, and a close
vocabulary distinct from the tenant application's own so a client can tell which party hung up.

The one idea to carry in is that establishment is **withheld until the backend has accepted**. The
proxy does not complete the upgrade optimistically and then discover there is nothing behind it —
which also settles subprotocol negotiation, since the party choosing the subprotocol is the backend
and the proxy relays a choice rather than making one. Everything else about the handshake is per-hop
and regenerated: masking, compression and the handshake fields themselves, per
[D6](../decisions/d06-framing-authority.md). Frame payloads are opaque octets and are not validated
as text.

Here the prior art is worth porting rather than avoiding, and this is unusual in the set. It holds
the only bounded buffer in the codebase — pre-connect frame buffering capped on both a count and an
octet axis, with a distinguishing overflow reason (`proxy_handler.ex:34-35`) — and a correct
lowercase-keyed hop-by-hop denylist with real subprotocol negotiation on the sidecar side
(`manager.go:19-32`, `manager.go:96-115`). Its close-code mapping is also worth keeping, with the
defect named: an integer arriving from the far hop was echoed to the browser with no range check
(`proxy_handler.ex:195`). See [carry-forward](../history/carry-forward.md#bounded-websocket-frame-buffer)
and [the tunnel](../how/the-tunnel.md).

## What it owns

- establishment: recognised in every form the edge accepts, validated before any tunnel exchange, and withheld until the backend accepts
- the per-hop handshake — masking, compression negotiation, regenerated fields — and subprotocol relay rather than choice
- opaque frame payloads, fragmentation and control-frame interleaving under the edge protocol's rules
- the bounds a shared proxy needs: decompressed message size, concurrency, origin policy, the pre-join buffer on both axes
- liveness per hop and end to end, and idle and lifetime bounds separate from request bounds
- backpressure at the client hop
- the proxy-originated close vocabulary, complete cleanup from every disconnect source, and drain on planned restart

## What it does not own

- how frames and the backend handshake cross between the hops — [the wire contract](tunnel-wire-contract.md)
- what the edge decides for itself about identity, authority and hop-by-hop fields — [edge hygiene](proxy-edge-hygiene.md)
- the request/response primitive and its deadlines — [HTTP fidelity](proxy-http-fidelity.md)
- the backend hop of the stream, inside the tenant's infrastructure — [the sidecar program](sidecar-program.md)
- which mount a stream was established through — [mount points](routing-mount-points.md)

## Depends on

Nothing. Its specification names no other capability.

## Shaped by

- [D1 — Three primitives, not twelve protocols](../decisions/d01-three-primitives.md) — makes this the second primitive rather than one protocol among many, so nothing here branches on a protocol name
- [D6 — Framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md) — settled masking, compression and the handshake fields as properties of one hop, regenerated on the next
- [D3 — Capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md) — makes a frame stream a declared ability, so a sidecar that cannot carry one refuses with a stated reason
- [D7 — Timeout taxonomy replaces the single cap](../decisions/d07-timeout-taxonomy.md) — gave idle and lifetime their own bounds rather than borrowing a request deadline that does not apply
- [D26 — WebTransport is designed for, not shipped](../decisions/d26-webtransport-deferred.md) — keeps the third primitive out of this capability, so its bounds are not generalised ahead of a shipped need

## The specification

[`proxy/websocket`](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
