---
type: guide
status: current
authority: rationale
---

# terminator — the boundary

`terminator/` is the Go component that terminates client connections the Elixir proxy cannot.
[D16](../../decisions/d16-http2-to-clients.md) puts it in v1 rather than later: Bandit implements
neither HTTP/3 nor RFC 8441 extended `CONNECT`, so behind an HTTP/2-terminating CDN a WebSocket
upgrade arrives in a shape an HTTP/1.1-only predicate can never match.

It is a contract speaker, not a second proxy. That is the whole reason it can be a separate component
without splitting the product: it can be rewritten in another language, or replaced, without anything
else changing.

## What it owns

- HTTP/2 from clients in v1, and HTTP/3 with WebTransport when those ship —
  [D26](../../decisions/d26-webtransport-deferred.md).
- Recognising an establishment request that arrives as extended `CONNECT` naming its stream protocol.
- The client-facing half of the credit chain: per-stream flow control at the edge, which WebSocket
  has none of and which the fidelity contract needs something to attach to.

## What it must not own

- **Routing, tenancy and state.** It holds no projection, no credential store and no durable state.
  Everything it needs arrives in the frames it speaks.
- **A second edge policy.** Framing authority, hop-by-hop removal and client-identity normalisation
  are stated once — [D6](../../decisions/d06-framing-authority.md) — and a terminator that reasoned
  about them independently would be a second answer to the request-smuggling question.
- **The schema.** Same as every other speaker: it reads `contract/`.

## Why it is separated this way

The alternative was HTTP/1.1 only at the edge for v1 with the protocol slot reserved and unused. That
ships the prior art's exact silent failure to anyone who puts a CDN in front of the proxy, and leaves
the client-side flow-control story unanswered. Paying for a third deployable now is the cheaper of the
two, and it arrives as a scheduled cost rather than as a surprise
([topology](../../how/topology.md)).

Component root: [`terminator/`](../../../terminator/README.md).
Behaviour: [proxy/websocket](../../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md),
[proxy/edge-hygiene](../../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
