# Architecture

## The primitive collapse

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

  NOT A PRIMITIVE -- see 01-system.md
  ===================================
    WebRTC media/data channels ..... TURN server territory, different product
    Web Push with VAPID ............ nothing traverses the proxy, zero work
    NTLM / Negotiate ............... connection-bound auth, impossible here
```

**The correction to make to anyone who arrives with a protocol list:** stop enumerating protocols.
Every item is either a `Content-Type`, an edge policy, out of scope, or one of five tunnel properties.

## The tunnel: frame-shaped, not message-shaped

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

### What this deletes

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

### Standards option, strongly worth evaluating

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

## Topology and runtime

```
   +--------------------------------------------------------------+
   |  CLIENT EDGE                                                 |
   |  HTTP/1.1 + HTTP/2 (v1) · HTTP/3 (deferred, front terminator)|
   |  TLS with per-tenant SNI + ACME · framing authority           |
   |  hop-by-hop removal · Forwarded/Via · Host bound to SNI       |
   +----------------------------+---------------------------------+
                                |
   +----------------------------v---------------------------------+
   |  PLUGBOARD  --  Elixir / Phoenix                             |
   |  mount projection (tenant-scoped) · sidecar registry with    |
   |  failover · hot-reloadable routing · per-tenant crash        |
   |  containment · LiveView admin console · Postgres             |
   +----------------------------+---------------------------------+
                                |  THE TUNNEL
                                |  versioned contract, frame-multiplexed,
                                |  capability-negotiated
   +----------------------------v---------------------------------+
   |  TELEPHONE  --  Go                                           |
   |  static binary · runs in the tenant's pods                   |
   |  gRPC-Web <-> gRPC bridge lives here (adjacency to h2)       |
   +----------------------------+---------------------------------+
                                |  plain HTTP / WS, loopback or LAN
                                v
                        tenant's backend

   DEFERRED:  +--------------------------------------------------+
              |  H3 / WEBTRANSPORT TERMINATOR  --  Go            |
              |  a CONTRACT SPEAKER, not a rewrite of the proxy. |
              |  Add only when WebTransport or HTTP/2-to-client  |
              |  forces it. Swappable, any language.             |
              +--------------------------------------------------+
```

### Why Elixir for the proxy

This **reverses** an earlier Rust recommendation. The reversal is recorded in full in
[the decision log](05-decision-log.md) — read it before re-litigating, because the premise that
originally forced Rust turned out to be fabricated.

Short version: WebTransport does **not** require HTTP/3 termination in the same process as the tunnel.
The WebTransport WG chair's own answer (`w3c/webtransport#525`) is that reverse proxies should
implement WebTransport over HTTP/2 or HTTP/3 *when speaking to the origin*; Chromium's stated
motivation for WT-over-HTTP/2 is *"a protocol we can use for proxy-to-backend communication"*; and
Caddy PR #7669 bridges bidi streams, uni streams and datagrams across exactly that boundary today.

Once WebTransport stops forcing the runtime, what remains is the work that has to get finished: a
distributed sidecar registry with failover, hot-reloadable routing, per-tenant crash containment, and
a live admin console. The reference already has all four working on the BEAM. The performance argument
does not survive the request path — at minimum two wide-area round trips per request, one into a
network you do not control, around per-request compute that is header parse plus prefix match plus
byte copy.

### The strongest argument against it

**Bandit implements neither HTTP/3 nor RFC 8441 extended CONNECT.** The second bites without
WebTransport ever being mentioned: behind an HTTP/2-terminating CDN, WebSocket upgrades arrive as
extended CONNECT with `:protocol: websocket`, an HTTP/1.1-only upgrade predicate can never match, and
WebSocket fails. Bandit's RFC 8441 issues (#27, #91, #690) are open. HTTP/2 to clients is also where
real per-stream flow control lives — the backpressure mechanism the fidelity contract needs and
WebSocket does not have.

Mitigation is the same as for HTTP/3: put every edge protocol behind the versioned contract, so the
terminator is a contract speaker that can be written in any language and swapped.

### Why Go for the sidecar

Static binary, `GOOS`/`GOARCH` cross-compilation, an HTTP and TLS stack that already handles whatever
a customer backend does, and — underrated — **it is the language a customer's platform team will
actually read before allowing it into their pods.**

Drop `gorilla/websocket`: archived, and message-level only where the contract needs frame-level
fidelity. Use `coder/websocket` or a hand-rolled framer.

Note the sidecar's job grows if WebTransport ships: it must then *dial* the tenant's backend over
HTTP/3 and re-originate streams and datagrams, which means `quic-go` plus `webtransport-go` in the
binary. That changes what "lightweight" can mean.

## Edge responsibilities

Things the edge owns and that never cross the tunnel:

- **Framing authority.** `Content-Length` and `Transfer-Encoding` are per-connection properties, never
  relayed. Each hop generates its own framing. A message arriving with both is rejected with 400, not
  reconciled — **this is the request-smuggling surface.**
- **Hop-by-hop removal**, including parsing `Connection` tokens rather than using a fixed list.
- **Client identity.** `Forwarded` (RFC 7239) or `X-Forwarded-For`, generated at a trusted hop and
  *normalised* — the reference forwards client-supplied `X-Forwarded-*` unchanged, which means the
  values a tenant's backend sees are attacker-controlled.
- **`Host` bound to SNI**, with 421 on mismatch.
- **Proxied traffic terminates before any application middleware** — no body parser, no method
  override, no HEAD folding, no content negotiation, no session, no CSRF. This is the direct cause of
  the reference's worst defect.
- **Cookie scoping across tenants on a shared hostname.** If two tenants mount under the same proxy
  hostname, a backend setting `Set-Cookie: session=…; Path=/` sets it for the whole hostname — so
  tenant A's session cookie is transmitted to tenant B's mount on the next request.
- **Mount-boundary URL rewriting.** A mount means the backend's `/` is the client's
  `/call/<tenant>/`, so every absolute reference the backend emits points outside the tenant's
  namespace: `Location` on 201 and 3xx, RFC 8288 `Link` (including WHIP's `rel=ice-server`), WebDAV
  `Destination` and the `<D:href>` values inside 207 Multi-Status bodies, and HLS/DASH playlist URIs.
  Needs an explicit per-content-type policy with a documented owner.
