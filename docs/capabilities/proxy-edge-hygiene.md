---
type: capability
status: planned
authority: rationale
---

# Edge hygiene

**`proxy/edge-hygiene`** — everything the component terminating the client connection decides for
itself and never delegates to the tunnel or to a sidecar.

A reverse proxy sits between two parties, and the tempting shortcut at every point is to believe
what one of them said. This capability is the collected refusal of that shortcut. Message framing,
the client's identity, the authority a request claims, the length of the thing being sent — each is
resolved from what the edge itself observed on the connection in front of it, and none of it is
inferred from a field a client supplied or from state the tunnel carries. The counterpart idea is
that a *hop* is the unit: framing, hop-by-hop fields and liveness belong to one connection at a time
and are regenerated on the next, per [D6](../decisions/d06-framing-authority.md).

The prior art failed on both halves in ways worth knowing before writing this. Header fields were
carried as a string-keyed map, which silently deleted every `Set-Cookie` past the first
(`proxy_controller.ex:496`), and `Content-Length` was relayed from the far hop verbatim
(`proxy_controller.ex:445-449`) onto a body whose length the transport had already changed. In the
other direction, proxied traffic ran through the host framework's ordinary request pipeline: the body
parser was mounted ahead of the router (`endpoint.ex:118`), and the pipeline custom domains used kept
a content-type gate the path-prefix pipeline had deliberately removed (`router.ex:157`). See
[the reference audit](../history/reference-audit.md) and
[protocol fidelity](../how/protocol-fidelity.md).

These obligations attach to a role rather than to a process. Under
[D16](../decisions/d16-http2-to-clients.md) the client-facing terminator is a separately scaled tier
from the start, so the same rules bind it whether it and the proxy are one component or two, and a
client observes the same outcome either way.

## What it owns

- framing generated per hop, and refusal of framing that is conflicting or ambiguous
- rejection of malformed request lines and field sections, each client protocol's own rules, and bounds on both
- removal of hop-by-hop fields including those `Connection` names; tunnelling and reflecting methods answered at the edge
- client identity and request authority established from the connection, and loop detection in the message path
- isolation of proxied traffic from ordinary application request processing, and of the proxy's own namespace from tenant traffic
- mount-boundary rewriting under a per-content-type policy, and cookie scoping in both directions
- admission limits keyed on unforgeable values, and edge-generated responses that are identifiable and escape what they reflect

## What it does not own

- the conduct of an exchange once admitted — [HTTP fidelity](proxy-http-fidelity.md)
- the handshake and lifetime of a frame stream — [WebSocket](proxy-websocket.md)
- how these messages are represented between the two hops — [the wire contract](tunnel-wire-contract.md)
- which mount a path or a hostname resolves to — [mount points](routing-mount-points.md), [custom domains](routing-custom-domains.md)
- the far hop's framing, bounds and failure outcomes — [the sidecar program](sidecar-program.md)

## Depends on

- [observability](operability-observability.md) — a refusal that happens before dispatch is still traceable, and the component that generated a response is identifiable to an operator without being disclosed to a client
- [packaging](operability-packaging.md) — the terminating component is a deployable like any other, so its artifact obligations are stated once rather than per tier

## Shaped by

- [D16 — HTTP/2 to clients is in v1, and the edge listener is a separate component](../decisions/d16-http2-to-clients.md) — made the terminating component its own tier, so these obligations bind a role and hold across both topologies
- [D6 — Framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md) — settled that each hop declares its own length or streaming, which is what makes relaying a defect rather than a style
- [D5 — Proxied traffic terminates before application middleware](../decisions/d05-pipeline-before-middleware.md) — put tenant traffic on a path of its own, out of reach of parsers, content-type gates, sessions and CSRF
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made a refusal, an admission limit and an established identity properties of the installation rather than of one process

## The specification

[`proxy/edge-hygiene`](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
