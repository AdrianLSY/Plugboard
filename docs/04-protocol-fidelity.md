# Protocol fidelity

**Method.** Nine research agents over the protocol families, with primary sources (RFCs, W3C specs,
MDN, IETF drafts, library repositories). Two load-bearing conclusions handed to adversarial reviewers:
the WebTransport verdict was *upheld with corrections*, the runtime recommendation was *overturned*.
12 agents, 492 tool calls.

The organising claim: **protocols are not features. Fidelity is the feature.** Get the properties
below right and most of the protocol surface arrives with no protocol-specific code.

## The fidelity contract

Ordered by how much of the protocol surface each property unlocks.

### Tier 1 — free today, unfixable later

These cost nothing on day one and become permanent the moment the first tenant pins a sidecar version.
**They are the urgent ones**, not because they are valuable but because they are irreversible.

**1. Bodies are opaque octet streams, never JSON strings.** If the envelope is JSON, base64 them —
which the reference already does for WebSocket frames and not for HTTP.
*Unlocks:* HLS/DASH segments, gRPC-Web protobuf frames, WebDAV file transfer, images, gzip, every
non-text payload.

**2. Headers are an ordered list of `(name, value)` pairs allowing repeats, in both directions.**
RFC 9110 §5.3 is explicit: *"The order in which field lines with the same name are received is
therefore significant… a proxy MUST NOT change the order of these field line values when forwarding a
message."* Its own note says `Set-Cookie` *"cannot be combined into a single field value"* (see also
RFC 6265 §3).
*Fields that legitimately repeat:* `Set-Cookie` above all, plus `Vary`, `Link`, `Cache-Control`,
`WWW-Authenticate`, `Proxy-Authenticate`, `Accept`, `Accept-Encoding`, `Accept-Language`, `Via`,
`Warning`, `Content-Language`, `Access-Control-Allow-Headers`, `Access-Control-Expose-Headers`,
`Server-Timing`, and the DAV-family `DAV:` and `If:`.
*Note on `Cookie`:* HTTP/2 may split it (RFC 9113 §8.2.3) and it must be rejoined with `"; "`, not
`","`.
*Concrete failure when collapsed:* a login endpoint issuing `Set-Cookie: session=…; HttpOnly` and
`Set-Cookie: csrf=…` returns one. The user appears logged in and every subsequent `POST` fails CSRF
validation.
*Case:* field names are case-insensitive (§5.1), so semantics survive lowercasing — but carry the
received casing anyway; some legacy SOAP and WebDAV stacks string-match on it. Lowercasing is
*mandatory* only when re-emitting on HTTP/2 or HTTP/3 (RFC 9113 §8.2.1, RFC 9114 §4.2: uppercase names
are malformed).

**3. Arbitrary method tokens pass through unmodified, case-sensitively.** RFC 9110 §9.1: *"The set of
common methods for HTTP is open-ended and does not limit intermediaries from supporting request methods
beyond those defined by this specification."* No allowlist.
*The two exceptions:* `CONNECT` is refused, not forwarded — in a multi-tenant edge it means "become a
forward proxy to an arbitrary host", which is an open-relay and SSRF hole. `TRACE` is answered by the
proxy per the `Max-Forwards` rule (§7.6.2) or returns 405 — forwarding it lets a caller reflect any
header the proxy added, including internal auth.
*Equally important, nothing may rewrite the method.* `Plug.MethodOverride` (POST + `_method=DELETE`)
and `Plug.Head` (HEAD → GET) are application conveniences that must not run on proxy traffic. HEAD
must arrive as HEAD so the backend applies §9.3.2 semantics itself; otherwise the backend streams a
full body the client never receives.

**4. The raw request target**, carried as separate scheme / authority / path / query fields, plus a
`:protocol` slot for extended CONNECT. Path segments must survive verbatim — `%2F` inside a segment is
not a separator, and normalising it breaks WebDAV hrefs.

**5. The full frame vocabulary, reserved even where unimplemented.** See
[Architecture](02-architecture.md). Reserving a frame type costs nothing; adding one later splits the
fleet.

**6. Stream ids and credit windows in every frame header**, even if v1 grants an effectively infinite
window.

**7. A capability set exchanged at tunnel join**, with refusal rather than degradation.

**8. An affinity key on the request.** Needed by WebDAV `LOCK`, socket.io/Engine.IO polling sessions
(every request for a `sid`, *including the upgrade*, must reach the same sidecar), and Digest nonces.

### Tier 2 — architecture-defining, and what users actually feel

**Incremental streaming with end-to-end backpressure, both directions.** The single highest-value
item in the entire research. Response headers must be forwardable the instant the backend emits them;
body bytes must flow as they arrive in bounded frames; request bodies must stream so a `PUT` can begin
forwarding before the client finishes. Backpressure must be credit-based and end to end — write
readiness on the client socket throttles tunnel frames, which throttles reads from the origin.

*Unlocks simultaneously:* SSE, HLS and LL-HLS live edges, MPEG-DASH, gRPC-Web server streaming, large
downloads, large uploads.

*Why it is not optional:* it is not a protocol, so it never appears on a protocol list — but it is the
property that decides whether a slow client is a slow download or a node-wide OOM.

**Per-stream multiplexing without head-of-line blocking.** Frames fragmented to a bounded maximum and
interleaved fairly, so one tenant's 2 GB download does not sit in front of their 50 ms API call, their
live WebSocket frames, their token refresh, or their heartbeat — the last of which can starve into a
tunnel teardown. Consider several tunnel connections per sidecar. This is why Cloudflare Tunnel
defaults to QUIC.

*Note:* one TCP connection means their largest download sets the p99 of their smallest API call. This
is a debt the tunnel already has for **plain HTTP** — it is not a WebTransport-specific cost.

**Cancellation and abort propagation (`RESET`).** A reset frame carrying stream id and application
reason, travelling in both directions. Client disconnect, deadline expiry, a video seek superseding an
in-flight range, an `EventSource` close — all must cancel the backend request context.

*Without it, ordinary user behaviour is free amplification aimed at the tenant's own origin.* Every
abandoned download, every navigate-away mid-video, every timed-out browser request leaves the backend
working and streaming into nothing until timeout.

*Also a correctness issue:* the gRPC spec is explicit that *"Unless explicitly defined to be, gRPC
Calls are not assumed to be idempotent."* If the proxy ever re-sends an in-flight request after a
tunnel reconnect, it silently duplicates a non-idempotent call.

**Timeout taxonomy — idle-between-bytes, never total wall clock.** Six separately configurable
timers: tunnel connect, origin connect, time-to-first-byte, idle-between-body-bytes, total, and edge
header-read. Every route carries a class, including an explicit `total = infinite`.

| class | TTFB | idle | total |
|---|---|---|---|
| ordinary API | short | short | short |
| SSE / watch APIs | finite | finite | **infinite** |
| LL-HLS blocking reload, long-poll | **long by design** | finite | bounded |
| large upload / download | short | finite | long |

**Many frames per exchange, not one message per correlation id.** See
[Architecture](02-architecture.md).

**WebSocket session fidelity** — deferred 101, frame shape, strict ordering, application close codes.
See [Architecture](02-architecture.md).

### Tier 3 — deferred, cheap later because the frame type exists

- **Trailer sections.** A distinct trailer frame after the last body frame, kept separate from headers.
  Constraints are tight and help: trailers cannot carry framing, auth or integrity fields, and
  1xx/204/304/HEAD responses have none. **This is the difference between gRPC and gRPC-Web** — and it
  also affects RFC 9530 digests and late `Server-Timing`.
- **Interim responses: 1xx.** N interim responses (status + header section, no body, no trailers) then
  exactly one final response, per stream. `Expect: 100-continue` additionally requires request-body
  flow control: the header section must be forwardable before any body exists. Without it, large
  uploads to an endpoint that would reject them are transferred in full first — and **every WebDAV
  client uses it on `PUT`.** 103 Early Hints (RFC 8297) is the other consumer.
- **Range requests and 206 Partial Content**, including `multipart/byteranges` and `If-Range`. The
  mechanism by which every media player seeks, and by which Finder avoids pulling whole files. An
  open-ended `Range: bytes=N-` into a large file is simultaneously the most common streaming
  interaction and the worst case for whole-response buffering.
- **Conditional requests and 304**, `Content-Encoding` passthrough (the proxy should never
  decompress — double-compression hazards), WHIP/WHEP, the Connect protocol.

## Per-family notes

### Streaming

**SSE** is Primitive 1 where the response half never ends: `Content-Type: text/event-stream`, no
`Content-Length`, incremental flush per event, connection held for hours, `retry` and `Last-Event-ID`
reconnection semantics. Any intermediary buffering kills it.

*In the reference:* `telephone.go:829-901` loops until `io.EOF`, which never comes, so nothing is ever
sent; `request_timeout_ms` fires and the client gets a 504. Even fixing the buffering leaves a 300s
cap (`path.ex:67`) on a protocol designed to run for hours.

**Long-polling is a first-class request class.** Naming it once collapses three items: LL-HLS blocking
playlist reload (`_HLS_msn`/`_HLS_part`), DASH `availabilityTimeOffset` fetches, and classic long-poll
chat fallbacks are all *"the server deliberately holds this request open."*

**Graceful drain across proxy upgrades.** With six-hour streams, every routine deploy simultaneously
disconnects thousands of `EventSource` clients that will all reconnect at once. Same problem when a
*tenant* upgrades its own sidecar: the reference's `CloseAll` kills every WebSocket with 1001 at once,
so each sidecar restart triggers a synchronised reconnect-and-resubscribe stampede.

**Per-tenant stream quotas.** Requests-per-minute limiting is meaningless once one admitted request can
hold a connection, a process and memory for six hours. Streams need their own admission control:
concurrent streams, bytes in flight, buffered bytes per tenant, plus byte-level accounting.

### gRPC-Web

Commit to gRPC-Web (unary + server-streaming) **and** the Connect protocol; put the gRPC-Web ↔ gRPC
bridge **in the sidecar**, where the HTTP/2 backend adjacency is — the position Envoy's `grpc_web`
filter occupies. Full gRPC at the ingress is out of scope until a non-Plug HTTP/2 listener exists.

- gRPC-Web carries **trailers inside the body** (a 5-byte length-prefixed frame) precisely because
  browsers and intermediaries cannot handle HTTP trailers. A UTF-8-coercing wire format destroys it.
- Content types: `application/grpc-web`, `+proto`, `+json`, and the base64 `-text` variant.
- `grpc-status-details-bin` carries rich errors; the spec suggests limiting header and trailer sections
  to 8 KiB each.
- **Connect** is cleaner for a tunnel: unary is plain `POST` with ordinary HTTP status codes for
  errors, streaming uses an `EndStreamResponse` envelope in the body, timeouts ride a header. Both
  Connect and gRPC-Web support `GET` for side-effect-free unary calls.
- Prior art for exactly this constraint: Envoy's `grpc_http1_reverse_bridge`, which converts a gRPC
  call into a unary HTTP/1.1 request/response and reconstructs the trailers on the way back.

### The WebDAV family

**Needs zero new tunnel primitives.** It needs Primitive 1 to stop being method-allowlisted,
JSON-string-bodied, whole-response-buffered, and path-normalised.

- **`REPORT` (RFC 3253 §3.6) is the method CalDAV and CardDAV actually run on** — `calendar-query`,
  `calendar-multiget`, `free-busy-query` (RFC 4791 §7.8–7.10), `addressbook-query`,
  `addressbook-multiget` (RFC 6352 §8). Defined outside both specs, so it is easy to miss.
- **There is no `MKADDRESSBOOK`.** CardDAV §6.3.1 uses the *extended* `MKCOL` of RFC 5689 — a `MKCOL`
  that carries a request body and can return 207.
- **RFC 6764 service discovery reshapes routing**: `/.well-known/caldav` and `/.well-known/carddav`
  must exist at the **origin root** and redirect to the context path. Needs per-tenant hostnames,
  which custom domains already imply.
- Other registered DAV-family methods that appear in real clients: `SEARCH` (RFC 5323),
  `BIND`/`UNBIND`/`REBIND` with 208 Already Reported (RFC 5842), `ORDERPATCH` (RFC 3648), `ACL`
  (RFC 3744). They matter less individually than as proof of the principle: **the list is open-ended,
  so do not enumerate it.**
- CalDAV scheduling (RFC 6638) adds `If-Schedule-Tag-Match`, `Schedule-Tag`, `Schedule-Reply`, and a
  `POST` to a scheduling Outbox carrying a VFREEBUSY iTIP body.
- WebDAV quota (RFC 4331): `DAV:quota-available-bytes` / `quota-used-bytes` are live properties Finder
  and Nextcloud read to show free space, plus the 507 path.
- **Client quirk that decides usability:** macOS `mount_webdav` mounts DAV class 1 servers **read-only**,
  and only read-write when the `DAV:` header advertises class 2 — because it takes a `LOCK` on every
  file opened for write (10-minute lock, refreshed every 5 minutes).
- `Depth: infinity` `PROPFIND` responses can be enormous, which is fatal to whole-response buffering.

### WebTransport

**Verdict: out of v1, reserved in the contract, shipped later as a separate terminator.**

The adversarial review corrected the *reason*. What survives:

- **There is no streams-only WebTransport over HTTP/3.** `draft-ietf-webtrans-http3-16` §3.1 requires
  `SETTINGS_WT_ENABLED=1`, `SETTINGS_ENABLE_CONNECT_PROTOCOL=1`, `SETTINGS_H3_DATAGRAM=1`, a non-zero
  `max_datagram_frame_size`, and an empty `reset_stream_at` transport parameter. An H3 edge cannot
  honestly advertise a datagram-less profile.
- **The browser derives reliability from the client leg.** W3C CR (30 July 2026): an HTTP/3 connection
  sets `[[Reliability]]` to `supports-unreliable`; HTTP/2 sets it to `reliable-only`. So terminating H3
  at the edge over a TCP tunnel tells the application the truth about the edge and a lie about the path.
  `WebTransportOptions.requireUnreliable` is the request-side counterpart an honest reduced-profile edge
  must refuse.
- **RFC 9221 datagram semantics cannot be emulated over TCP** (§5.2: *"Although DATAGRAM frames are not
  retransmitted upon loss detection, they are ack-eliciting"*; flow control §5.3; congestion control
  §5.4).
- **MASQUE is the wrong shape and should be explicitly ruled out.** CONNECT-UDP (RFC 9298) is a
  *forward-proxy* primitive where the client names `target_host:target_port`; here the sidecar dials out
  and the destination is an application session.

What was corrected:

- **Safari 26.4 (March 2026) shipped WebTransport *with* the HTTP/2 fallback**, so an honest reduced
  profile is now browser-reachable — `reliable-only` on Safari, a clean failure (not a lie) on
  Chrome/Firefox, which still do not implement WT/H2. "No honest configuration exists" is dead.
- **`draft-ietf-webtrans-http2` is a blueprint, not just an argument.** See
  [Architecture](02-architecture.md) — it is a ready-made capsule wire format for this exact tunnel
  shape.
- **`webtransport` is not a legacy token.** It is the *current* `:protocol` value for WebTransport over
  HTTP/2 (`http2-15` §11.1); `webtransport-h3` is the HTTP/3 token (`http3-16` §3.2). A conformance
  suite rejecting `webtransport` as legacy would reject every valid H2 session including Safari's
  fallback. `SETTINGS_ENABLE_WEBTRANSPORT` *is* genuinely superseded, by `SETTINGS_WT_ENABLED`.
- **The blocker is the edge, not the tunnel.** Extended CONNECT plus capsules, which Bandit lacks and
  no off-the-shelf terminator proxies through. That work has **zero reuse** for SSE, streaming or
  WebDAV — whereas the tunnel work WebTransport would motivate (incremental emission, binary frames,
  per-stream interleaving, flow control) is *already mandatory* for SSE and large downloads. That is the
  real sequencing argument.

**Adoption context.** Baseline March 2026, ~90% global browser support (caniuse). Website usage is
negligible — w3techs does not track it. Named production consumers are **stream-centric**: the libp2p
WebTransport spec does not mention datagrams at all and uses the first stream for a Noise handshake;
MoQ treats datagram forwarding preference as a per-object option over a stream-oriented model. No
public measurement of the datagram share of sessions exists.

**Also note:** outbound UDP/443 is blocked on many corporate and cloud egress paths. Since the sidecar
lives in the customer's infrastructure, a QUIC tunnel would need a TCP fallback — meaning **two
capability profiles forever.** And `w3c/webtransport#525` is an open issue asking how reverse proxies
should handle WebTransport at all; the sidecar architecture is unusually well-shaped for it because you
control both ends, unlike nginx which must terminate and re-originate HTTP to an arbitrary backend.

### The multi-tenant edge

Not on the original list, and for custom tenant domains it is comparable work to all the protocols
combined.

- **Per-tenant certificates** with SNI-based selection and automated issuance. ACME (RFC 8555):
  HTTP-01 vs DNS-01 vs TLS-ALPN-01, and which is viable when the *tenant* owns the DNS. Wildcards
  require DNS-01. Plus storage, renewal, Let's Encrypt rate limits, OCSP stapling.
- **Domain-ownership verification before issuance.** A v1 blocker: layering ACME onto a first-come
  unverified domain claim escalates a routing bug into obtaining a publicly trusted certificate for
  someone else's domain. Also guard dangling-CNAME takeover.
- **ALPN** negotiation across HTTP/1.1, HTTP/2 and HTTP/3 simultaneously, plus `Alt-Svc` for H3
  discovery.
- **`Host` vs `:authority`**, absolute-form targets, Host-header injection, and routing-confusion risk
  when a proxy trusts `Host`. Bind `Host` to SNI, 421 on mismatch.
- **Cookie scoping** across tenant subdomains of a shared apex — the public suffix list is relevant.
- **Rate limiting keyed on something authenticated.** The reference keys its API limiter on a
  client-supplied `x-api-key` header (`plugs/rate_limiter.ex:86-91`) that no endpoint authenticates
  with, so a fresh random value per request yields a fresh bucket every time — while binding correctly
  for legitimate clients, who never send it.
