---
type: capability
status: planned
authority: rationale
---

# The wire contract

**`tunnel/wire-contract`** — the versioned protocol the proxy and a sidecar speak to each other over
the persistent tunnel, and the one artifact in the system that cannot be corrected after release.

It cannot be corrected because you deploy the proxy and the tenant deploys the sidecar, on their
schedule or never, so an installation permanently faces a spread of sidecar versions it cannot force
forward. That single asymmetry — [version skew](../why/version-skew.md) — explains the shape of the
whole capability: changes are additive by default, what a peer can do is *declared* rather than
inferred from its version, a request no declared capability can back is refused with a stated reason
instead of quietly downgraded, and a version claim means nothing until the conformance suite backs it.

The one idea to take away before opening the specification: the unit on the wire is a **frame carrying
a stream identifier**, not a message carrying a whole exchange. Everything readers usually arrive
looking for follows from that choice and is unrepresentable without it — many exchanges in flight on
one connection without head-of-line blocking, credit-based flow control, a body that moves in pieces
while it is still arriving, interim responses before the final one, trailers after the body,
cancellation travelling in either direction, and each direction closing on its own. The prior art
chose the opposite and hit all of those walls at once: one reply per correlation identifier
(`telephone_channel.ex:302-309`), a body collected into a list and only then shipped inside a single
message (`telephone.go:829-901`), and header fields as a string map, which silently deleted every
`Set-Cookie` past the first (`proxy_controller.ex:496`) — see
[the reference audit](../history/reference-audit.md) and [the tunnel](../how/the-tunnel.md).

The contract's frame of reference is one tunnel and the exchanges on it. It is blind to the proxy's
topology on purpose: nothing on the wire names an instance or reveals how many exist, so a sidecar
cannot come to depend on a deployment shape it has no way to see.

## What it owns

- version negotiation, capability declaration, and refusal rather than degradation
- how a request/response exchange is represented — method token, ordered header pairs, opaque body octets, raw request target, trailers, interim responses
- frames, stream identifier allocation and scope, multiplexing, credit-based flow control, cancellation, half-close
- establishment, liveness, withdrawal and closure, each with an enumerated reason
- the reserved datagram class, defined now so adding it later does not split the fleet
- the binary encoding, the machine-readable error vocabulary, and the additivity rule for changes

## What it does not own

- accepting and terminating the connection a tunnel runs over — [the listener](tunnel-listener.md)
- proving who a sidecar is before it is allowed to speak — [sidecar credentials](auth-sidecar-credentials.md)
- choosing which registered sidecar an exchange is dispatched to — [sidecar registry](tunnel-sidecar-registry.md)
- the executable proof behind a version claim — [conformance](tunnel-conformance.md)

## Depends on

- [sidecar registry](tunnel-sidecar-registry.md) — selection across instances, affinity bindings included, is the registry's; the contract only carries the key and the mount an exchange was matched to

## Shaped by

- [D2 — The tunnel exchange is frame-shaped](../decisions/d02-frame-shaped-tunnel.md) — settled the unit on the wire, and with it multiplexing, streaming and cancellation
- [D3 — Capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md) — made ability declared and unmet requests refused
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — made this the irreversible artifact, so additivity is the default
- [D18 — Frame payloads are encoded from a binary interface definition](../decisions/d18-frame-payload-encoding.md) — settled the encoding and its binary safety
- [D1 — Three primitives, not twelve protocols](../decisions/d01-three-primitives.md) — fixed how many exchange shapes the contract carries, and that the third is reserved
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made topology-blindness an obligation rather than an accident

## The specification

[`tunnel/wire-contract`](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
