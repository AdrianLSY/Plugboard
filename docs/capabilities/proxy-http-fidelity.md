---
type: capability
status: planned
authority: rationale
---

# HTTP fidelity

**`proxy/http-fidelity`** — the conduct of one request/response exchange in flight: which deadline
applies to which phase of it, what survives the round trip unaltered, and where the line falls
between a failure the proxy can answer and one it can only truncate.

[The wire contract](tunnel-wire-contract.md) fixes how a request and its response are *represented*;
this capability governs the two ends that surround that representation — the proxy at the client
edge, and the sidecar where the request is originated against the tenant's backend. Its subject is
therefore a single exchange, and the frame of reference for every bound in it is the exchange rather
than the process: an identical request gets identical fidelity, identical bounds and the same
enumerated cause whichever instance admitted it, per
[D20](../decisions/d20-multi-instance.md).

Two ideas carry most of it. The first is that there is no request timeout — there is a taxonomy of
separately named phases, each separately bounded, and one class that permits a genuinely unbounded
total, because a server-sent event stream and a health check are not the same kind of thing
([D7](../decisions/d07-timeout-taxonomy.md)). The second is the **commit point**: the response head.
Before it the proxy can still answer with an error of its own; after it, the only honest failure is a
truncation, and every terminating condition either way is recorded as a distinct cause. Those two
plus a rule of pure conduct — no store, no body transformation, no replay of a forwarded exchange —
are most of what a reader needs.

The prior art is the argument for all of it. A single global timeout capped at three hundred seconds
covered the whole buffered exchange (`path.ex:67`, `proxy_controller.ex:246`), which makes a
long-lived stream unrepresentable rather than merely unsupported; and what was called streaming read
the entire body into a list and only then shipped every piece inside one message
(`telephone.go:829-901`). See [the reference audit](../history/reference-audit.md) and
[the failure taxonomy](../how/failure-taxonomy.md).

## What it owns

- the backend request derived from the mount remainder alone, and nothing else about it
- the separate, independently configurable time bounds — first byte, idle between octets, total — and the timeout class each route carries
- admission of a response whose body never ends, against occupancy rather than arrival rate, and its drain at shutdown
- preservation of partial, conditional and content-coded transfers, and of trailers, exactly as the origin produced them
- the distinction between an unreachable tunnel and an unreachable origin, and a distinct enumerated cause for every terminating condition
- the commit point, and generated error responses that are per-cause distinguishable and bound what they reflect
- the conduct rules: no store, no body transformation, no replay, no body materialised to enforce a size bound

## What it does not own

- what the edge decides for itself about framing, identity and authority — [edge hygiene](proxy-edge-hygiene.md)
- how the exchange is encoded and multiplexed between the hops — [the wire contract](tunnel-wire-contract.md)
- the remainder itself, and which mount produced it — [mount points](routing-mount-points.md)
- the backend hop's own bounds, reuse and failure outcomes — [the sidecar program](sidecar-program.md)
- a bidirectional frame stream, which is a different primitive — [WebSocket](proxy-websocket.md)

## Depends on

Nothing. Its specification names no other capability.

## Shaped by

- [D7 — Timeout taxonomy replaces the single cap](../decisions/d07-timeout-taxonomy.md) — replaced one request timeout with six named bounds and the class that selects between them, which is what admits an unbounded response at all
- [D1 — Three primitives, not twelve protocols](../decisions/d01-three-primitives.md) — fixed this capability's subject as one of the three shapes, so nothing in it keys on a protocol name
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made every bound, phase and cause a property of the exchange, holding unchanged when the admitting instance is not the one holding the tunnel
- [D6 — Framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md) — why a size bound is enforced without materialising a body, and why length is never carried across from the far hop
- [D27 — Observability before the hot path](../decisions/d27-observability-first.md) — the enumerated causes exist to be emitted, so the sink predates the code that fills it

## The specification

[`proxy/http-fidelity`](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
