---
type: capability
status: planned
authority: rationale
---

# The tunnel listener

**`tunnel/listener`** — the endpoint a sidecar dials, and everything that has to be true of a
connection in the window before anyone knows who is on the other end of it.

That window is the whole capability. Nothing here can lean on an authenticated identity, because none
exists yet, so the bounds and the disclosure rules are stated at the accept path rather than inherited
from whatever takes over afterwards. Two consequences a reader most needs. The trust decision runs
outbound before it runs inbound: the endpoint presents a verifiable identity of its own so a sidecar
can decide whether to offer a credential at all. And every pre-authentication bound keys on the
**observed source** — the origin as derived from the connection itself, never a value the peer states
— which is defined here for exactly that reason. Both terms are in
[the glossary](../glossary.md#the-tunnel).

The second idea is narrowness. The listener serves establishment and nothing else: no client request
reaches it, a tunnel connection is never mistaken for client traffic, it never points a dialling peer
somewhere else, and it occupies a slot in the single reserved prefix enumeration rather than a name of
its own choosing. An accept path is reachable by anyone who can route to it, and narrowness is what
makes that surface small enough to bound.

The endpoint is described without naming a transport, deliberately, even though
[D19](../decisions/d19-tunnel-transport.md) already fixed the v1 answer — so a later move is a change
of transport rather than a redesign. The prior art shows what happens when the pre-authentication
window is unpriced: a sidecar's join loaded every active credential and ran a password hash against
each one, inside a transaction holding a database connection (`telephone_tokens.ex:384-397`,
[reference audit](../history/reference-audit.md#structural-defects)) — unauthenticated work that was
neither cheap nor bounded.

## What it owns

- the verifiable endpoint identity, and its renewal without invalidating a pinned fleet
- confidentiality and integrity before anything is read, above a floor nothing can configure away
- explicit identification at setup of the framing spoken over the connection
- the observed source at this accept path, the enumerated connection phases, and refusals opaque to an unauthenticated peer
- bounds on unauthenticated connections and work, and on established tunnels per tenant, mount and credential
- draining by ceasing to accept, and the discoverable, movable dialling address

## What it does not own

- what is spoken once the connection is up — [the wire contract](tunnel-wire-contract.md)
- deciding who the dialling peer actually is — [sidecar credentials](auth-sidecar-credentials.md)
- the key material behind the endpoint identity, and its replacement — [key custody](security-key-custody.md)
- the same value for a *client* connection, and when an intermediary's claim about it is honoured — [edge hygiene](proxy-edge-hygiene.md)
- what an admitted tunnel becomes eligible to serve — [the sidecar registry](tunnel-sidecar-registry.md)

## Depends on

Nothing. Its specification names no other capability. The dependency runs the other way: it is named
by `security/key-custody`, which owns the material its endpoint identity is presented from.

## Shaped by

- [D19 — The v1 tunnel is a WebSocket over TLS on the standard HTTPS port](../decisions/d19-tunnel-transport.md) — settled the v1 transport on egress-survival grounds while leaving the endpoint transport-agnostic
- [D2 — The tunnel exchange is frame-shaped](../decisions/d02-frame-shaped-tunnel.md) — the framing carried over the connection is the contract's own, so setup has to name it rather than let it be inferred
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — every instance runs an accept path, and a bound applied before the peer is identified is the one exception to installation-wide accounting

## The specification

[`tunnel/listener`](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md)
owns the behaviour. Where this note and it disagree, it wins.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
