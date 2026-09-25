---
type: essay
status: current
authority: rationale
---

# Scope: what it does not do

These are refusals with reasons, not gaps. Document them where users will look, because the
alternative is a tenant spending a day blaming the proxy.

A refusal here is a refusal, not a maybe. Where a request cannot be backed it is refused with a
stated reason rather than served at lower fidelity — that shape is
[D3 — capability negotiation](../decisions/d03-capability-negotiation.md), and what a refusal must
actually say is fixed by the specifications named at the end of this page, not here.

## The refusals

### WebRTC media and data channels

Media is SRTP, and data channels are SCTP-over-DTLS, both over ICE-negotiated ephemeral UDP with keys
the endpoints derive themselves. The component that relays that traffic is a **TURN server**
(RFC 8656) — a bandwidth-priced UDP relay with a latency SLA, which is a different product with
different economics. RFC 8835 §3.4 requires every WebRTC endpoint to support TURN, so the boundary is
a normal part of every WebRTC deployment rather than a Plugboard limitation.

*What is supported, and should be advertised instead of "no":* every WebRTC **control plane** in
production. WHIP (RFC 9725) and WHEP are plain HTTP `POST`/`PATCH`/`DELETE`/`OPTIONS` signalling that
the request/response primitive already fits. SIP-over-WebSocket (RFC 7118) and XMPP-over-WebSocket
(RFC 7395) — which is how most telephony-adjacent WebRTC actually signals — are ordinary
bidirectional streams. Two specifics that decide whether a browser WHIP client works at all:
`Access-Control-Expose-Headers` must be honoured or the client cannot read `Location` or `Link`
(RFC 9725 §4.2 mandates CORS), and trickle ICE makes per-connection message **ordering** a
correctness requirement rather than a performance one.

*The real risk here is silence.* Every other unsupported thing in this system fails loudly — a 404, a
406, a 504. WebRTC media fails with a `201 Created` and then nothing, about thirty seconds later,
with clean logs on both sides.

### Web Push with VAPID

The browser subscribes against a push service (FCM, Mozilla autopush); the tenant's app server sends
outbound to that service with a VAPID JWT (RFC 8292); the service worker is served from the tenant's
own origin over ordinary HTTPS. Nothing traverses the proxy. **Zero work required** — this was on the
original wish list and needs no support at all.

### NTLM and SPNEGO/Negotiate to tenant backends

These authenticate a *TCP connection*, not a request, via a multi-round-trip handshake pinned to that
connection (RFC 4559). A tunnel that multiplexes independent streams cannot express that. The honest
"cannot be done" item.

### TLS passthrough

Encrypted Client Hello (RFC 9849) encrypts the single field such a mode routes on.

### Full gRPC at the ingress

As distinct from gRPC-Web, which *is* in scope. The gRPC-Web ↔ gRPC bridge belongs **in the
sidecar**, the only component adjacent to an HTTP/2 backend — the same position Envoy's `grpc_web`
filter occupies. The reason first given for the refusal — `grpc-status` travels as an HTTP trailer
even on success, and `Plug.Conn` has no trailers API — was retired by
[D16](../decisions/d16-http2-to-clients.md) for any deployment fronted by the contract-speaking
terminator it places in v1, the proxy-alone edge remaining a defined topology. What stands is a
refusal of **scope**: no section of the plan builds an ingress gRPC path, and whether it survives on
any other ground is carried as an open question in [the change's design
register](../../openspec/changes/rebuild-plugboard/design.md).

### Caching

No response cache in v1, therefore no cache-key design and no cache-poisoning surface.

### Health-probe-based load balancing

Sidecar selection is registry membership plus liveness, not active probing.

## Deferred, not refused

- **WebTransport.** Reserved in the contract, shipped later as a separate HTTP/3 terminator that
  speaks the wire contract. Reached Baseline in March 2026 (Safari 26.4); real-world website usage is
  still negligible. See [Architecture](../how/architecture.md) for why this does *not* force the tunnel to
  be QUIC.
- **HTTP/3 at the edge** for ordinary HTTP. Buys connection migration, 0-RTT, and no cross-request
  TCP head-of-line blocking. Requires zero tunnel change — it is a front-terminator decision.
- **WHIP/WHEP and the Connect protocol.** Cheap later, and neither needs a frame type the contract
  does not already reserve. Trailers, 1xx interim responses and Range/206 are *not* deferred — they
  are v1 work. See [Protocol fidelity](../how/protocol-fidelity.md).

The deferral of WebTransport is itself a decision on the record:
[D26 — WebTransport is designed for, not shipped](../decisions/d26-webtransport-deferred.md). Which
capabilities are in scope and which are deferred with their dependencies named is
[D17](../decisions/d17-capability-scope.md).

## Where these boundaries are specified

This page says what is out and why. What is *in*, and exactly how faithfully, is owned elsewhere:

- The control-plane traffic named above — WHIP/WHEP signalling and method handling —
  [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md)
  and [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
  **CORS is a gap, not an owned requirement:** no specification names CORS or
  `Access-Control-Expose-Headers`. RFC 9725 §4.2 requires a WHIP endpoint to support `OPTIONS`
  requests for CORS; it does not itself state which response headers must be exposed, so the
  consequence for a browser client reading `Location` follows from the Fetch standard rather than
  from RFC 9725. Recorded as a known hole rather than an assumed owner.
- Bidirectional streams and per-connection ordering —
  [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md).
- Membership and liveness, in place of active probing —
  [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md).
- Which frame types are reserved, so a deferral stays cheap —
  [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md).

## Read next

- [Version skew](version-skew.md) — why a deferral has to be reserved in the contract now.
- [Protocol fidelity](../how/protocol-fidelity.md) — the per-family detail behind "in scope".
- [What it is](what-it-is.md) — the shape all of this sits inside.
