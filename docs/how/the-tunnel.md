---
type: essay
status: current
authority: rationale
---

# The tunnel: frame-shaped, not message-shaped

The single largest architectural commitment, and the one the previous attempt got wrong. Everything
below is rationale — [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) and
[tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md) are what state the behaviour, and
[D2 — the tunnel exchange is frame-shaped](../decisions/d02-frame-shaped-tunnel.md) is the decision in
force.

The unit on the wire is a **frame carrying a stream id**, not a message carrying a whole request or
response. This is the central architectural decision and it is what the reference got wrong.

```
  v1 FRAME VOCABULARY -- all reserved at v1, even where unimplemented

    REQ_HEAD        method token, raw target, ordered header pairs
    BODY_DATA       stream id, sequence, opaque octets
    BODY_END        stream id, optional trailer section
    INTERIM_RESP    1xx status + header section (no body, no trailers)
    RESP_HEAD       status, ordered header pairs
    RESET           stream id, application error code, reason
    WINDOW_UPDATE   stream id, credit delta
    DATAGRAM        unreliable class, drop-on-overflow    (v1: reserved, unused)

  Every frame header carries a stream id and participates in a credit window,
  even where v1 grants an effectively infinite window.

  Reserving a frame type costs nothing today.
  Adding one later splits the fleet permanently.
```

## What this deletes

The reference hand-built a request/response multiplexer on top of one ordered stream. Stream ids
subsume all of it:

| the reference hand-built | frames give natively |
|---|---|
| `request_id = Ecto.UUID.generate()` per request | the stream **is** the exchange |
| `waiting_callers` map (`telephone_channel.ex:292`) | gone |
| Go-side `pendingRequests` map + mutex | gone |
| selective `receive` on `^request_id` | gone |
| **the leak**: entries removed only on successful reply, no monitor, no cap, no timeout sweep | gone — no map to leak |
| **mailbox pollution**: late replies accumulating forever in a keep-alive connection's mailbox (`executor.ex:421-441`) | gone — a reset stream is a reset stream |
| `ws_check` two-phase probe — a runtime capability test standing in for a contract that could not express capabilities | gone — see WebSocket below |
| head-of-line blocking between a tenant's 2 GB download and their 50 ms API call | interleaved frames, bounded size, per-stream scheduling |
| **no backpressure anywhere** (the audit found zero, not "weak") | credit windows |

**Carry the idea, delete the implementation.** The audit's carry-forward list originally said "keep
the correlation-id design verbatim". That advice was superseded: one logical exchange independently
multiplexed is right; the UUID-and-map mechanism is not.

## Standards option, strongly worth evaluating

`draft-ietf-webtrans-http2` (WG Last Call, revision 15, 2026-07-06) already specifies a capsule
framing for exactly this shape — WebTransport streams and datagrams multiplexed inside **one reliable
ordered bidirectional stream**:

- §2: *"The stream that carries the CONNECT request is used to exchange bidirectional data for the
  session… Within this stream, WebTransport streams and WebTransport datagrams are multiplexed."*
- §6.4: `WT_STREAM` capsules carry stream id, FIN bit, and stream data.
- §6.11: *"The data in DATAGRAM capsules is not subject to flow control. The receiver MAY discard this
  data if it does not have sufficient space to buffer it."* — i.e. drop-on-overflow is already
  standardised rather than needing invention.

It provides stream ids, FIN, reset with application error codes, session and per-stream flow control,
and a discardable datagram class, **with a standards conformance target** — which pairs naturally with
an already-decided conformance suite.

The reason it is not yet the decision: **no publicly available HTTP/2 WebTransport server library
exists in any language.** The Rust ecosystem (`wtransport`, `moq-dev/web-transport`) is HTTP/3 only;
`quic-go/webtransport-go` implements draft-16 over HTTP/3 only. Adopting it means hand-writing
draft-conformant capsule framing. Resolve before freezing v1.

## Capability negotiation

The sidecar declares its capability set at tunnel join:

```
  binary_bodies · header_lists · response_streaming · request_streaming
  trailers · interim_responses · cancellation · flow_control
  frame_level_ws · datagrams
```

The proxy **refuses** a request or mount that a connected sidecar cannot back, with an explicit status
and reason. It does not silently degrade.

This is load-bearing because sidecar selection round-robins across a mount. Without negotiation, two
identical requests to the same URL behave differently depending on which sidecar version answered, and
"it worked a minute ago" becomes the support load. A v1 sidecar that buffers whole responses will not
*error* on a server-streaming gRPC-Web call — it will hang until the timeout.

## WebSocket: delete the probe

The reference gates every proxied WebSocket behind a two-phase `ws_check` / `ws_check_result`
handshake, so it can learn the negotiated subprotocol before replying `101`. That probe exists because
the tunnel could not defer the `101` until the backend answered. It has **zero test coverage on either
side** and is **absent from all 457 lines** of the spec document meant to guide implementers.

Replace it: tunnel `open` is a request/response that returns **the backend's real handshake
response** — status line, every header including `Set-Cookie`, `Sec-WebSocket-Protocol` and
`WWW-Authenticate`, and body. A non-`101` is relayed verbatim instead of collapsing to a generic
error.

Four properties that must hold, because they are one session:

1. **Deferred 101**, relaying the real handshake response as above.
2. **Frame-level fidelity** — `fin`/`rsv`/`opcode`, so fragmentation and continuation frames survive.
   Message-level libraries cannot express this; this is why `gorilla/websocket` (archived,
   message-level) is not carried forward.
3. **Strict per-connection ordering as an explicit contract guarantee.** Nobody thinks to require it,
   which is exactly why the reference sidecar breaks it with `go handler(msg)` and nobody noticed.
   Every protocol in this family has a mandatory opening message.
4. **Close-code fidelity across the application range 3000–4999.** `graphql-ws` encodes its entire
   error taxonomy in 4400/4401/4403/4408/4409/4429; collapsing those to 1000-series codes destroys it.

Two things that cannot be relayed faithfully, and must be documented rather than pretended:
`Sec-WebSocket-Key`/`Accept` and frame masking are per-hop by construction; and ping/pong is
unavoidably hop-by-hop, because every mainstream library auto-answers pings below the application API.
The consequence is that the backend's heartbeat measures the sidecar and the client's measures the
proxy — so **end-to-end liveness needs its own mechanism.**

`permessage-deflate` (RFC 7692) is likewise per-hop; end-to-end deflate across two WebSocket
connections does not exist. Treat it as a **tenant-isolation** concern rather than a bandwidth
feature: a ~6 MiB compressed frame inflating to ~6 GiB is a whole-node kill.

## What owns the behaviour

- **The frame vocabulary and its encoding:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [D18 — frame payloads are encoded from a binary interface definition](../decisions/d18-frame-payload-encoding.md)
- **The tunnel's own transport:** [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md), [D19 — the v1 tunnel is a WebSocket over TLS on the standard HTTPS port](../decisions/d19-tunnel-transport.md)
- **Refusal rather than degradation:** [D3 — capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md), and the capability scope in [D17](../decisions/d17-capability-scope.md)
- **WebSocket fidelity, including the close-code range:** [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md)
- **`permessage-deflate` as an isolation concern:** [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md)
- **Which sidecar answers, and therefore why negotiation is load-bearing:** [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md)
- **Adjacent notes:** [three primitives](three-primitives.md) · [topology](topology.md)
