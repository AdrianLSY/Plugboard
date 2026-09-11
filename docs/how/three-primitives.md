---
type: essay
status: current
authority: rationale
---

# Three primitives, not twelve protocols

This is orientation, not behaviour: the specifications linked at the foot of this note own what the
proxy does with each primitive. What is recorded here is *why* a list of twelve protocols is not a
list of twelve features — so that the next request for "support for protocol X" is answered by
naming the primitive that already carries it instead of by opening a branch. The decision this
argument produced is [D1 — three primitives, not twelve protocols](../decisions/d01-three-primitives.md).

The original requirement was "proxy anything you can find on a website": WebSockets, SSE,
WebTransport, WebRTC, HLS, MPEG-DASH, GraphQL, JSON-RPC, gRPC-Web, Web Push, WebDAV, CalDAV, CardDAV.

That is not twelve features. It is **three primitives, and nine of the twelve are the same one.**

```
  PRIMITIVE 1 -- REQUEST/RESPONSE BYTE STREAM                        9 of 12 items
  ===========================================
    An HTTP message modelled as:
      { opaque method token
      , raw request target (scheme / authority / path / query, plus a
                            :protocol slot for extended CONNECT)
      , ORDERED list of (name, value) header pairs, repeats allowed
      , opaque octet stream that MAY begin before it ends
      , optional trailer section
      , N interim responses, then exactly one final response }

    carries: SSE, HLS, LL-HLS, MPEG-DASH, GraphQL-over-HTTP, JSON-RPC-over-HTTP,
             gRPC-Web, Connect, WebDAV, CalDAV, CardDAV, WHIP/WHEP, Range/206,
             long-polling, ordinary HTTP

    These differ from one another ONLY by Content-Type and method token.
    None of them justifies a line of protocol-specific code.

  PRIMITIVE 2 -- BIDIRECTIONAL FRAME STREAM
  =========================================
    Ordered per connection, binary-safe, frame-shaped (fin/rsv/opcode),
    independently flow-controlled.

    carries: WebSocket + everything riding on it -- Phoenix Channels,
             ActionCable, graphql-ws, MQTT-over-WS, SIP-over-WS (= WebRTC
             signalling), XMPP-over-WS, JSON-RPC-over-WS, LSP

    Also SUPPLIES cancellation and interim responses to Primitive 1.

  PRIMITIVE 3 -- QUIC STREAMS + UNRELIABLE DATAGRAMS
  ==================================================
    carries: WebTransport. Exactly one item. Deferred; reserved in contract.

  NOT A PRIMITIVE -- see why/scope-refusals.md
  ============================================
    WebRTC media/data channels ..... TURN server territory, different product
    Web Push with VAPID ............ nothing traverses the proxy, zero work
    NTLM / Negotiate ............... connection-bound auth, impossible here
```

**The correction to make to anyone who arrives with a protocol list:** stop enumerating protocols.
Every item is either a `Content-Type`, an edge policy, out of scope, or one of five tunnel properties.

## What owns the behaviour

- **Primitive 1:** [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md)
- **Primitive 2:** [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md)
- **All three, as they cross the tunnel:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Primitive 3, reserved rather than built:** [D26 — WebTransport is designed for, not shipped](../decisions/d26-webtransport-deferred.md)
- **The shape of the exchange:** [the tunnel](the-tunnel.md) · **where the pieces sit:** [topology](topology.md)
