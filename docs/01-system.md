# The system

## What it is

Plugboard is **dynamic ingress for multi-tenant platforms**. It replaces static reverse-proxy
configuration files with routing that applications register for themselves at runtime, over a
persistent outbound tunnel.

A tenant runs a lightweight sidecar (**Telephone**) next to their backend. The sidecar dials out to
the central proxy (**Plugboard**) and holds the connection open. Traffic arriving at the proxy for
that tenant's mount point is forwarded down the tunnel; the sidecar replays it to the local backend
and returns the response the same way.

## What that buys

- **No inbound network path required.** The tenant's backend needs no public IP, no port forward, no
  firewall change, and no inbound security-group rule. The tunnel is outbound-only.
- **Routing changes without restarts.** Mount points live in the database and are projected into an
  in-memory cache; adding a route does not touch a config file or bounce a process.
- **Registration is the deploy.** A backend that starts up and connects a sidecar is routable. A
  backend that dies stops being routable. Autoscaling needs no external service-discovery wiring.
- **Custom domains per tenant**, mapped onto mount points, so a tenant's traffic arrives on their own
  hostname rather than a path prefix under yours.

## Who it is for

Three audiences, and their requirements conflict. Naming the conflict is more useful than pretending
it resolves:

| audience | wants | costs the others |
|---|---|---|
| **Platform operators** (the buyers) | tenant isolation, predictable failure, an audit trail, boring upgrades | slows feature work; forces tenancy into the data model on day one |
| **Contributors** | fast local setup, a fast test suite, small reviewable units, clear module boundaries | rules out "clever"; forces a pure core with a thin database edge |
| **The author's portfolio** | legible judgment, depth, decisions defensible under questioning | tempts over-engineering; the mitigation is that every decision is written down with its rationale, so depth is *documented* rather than *built* |

The operator audience is the one that sets hard requirements. "One tenant cannot affect another" is a
sold promise, which is why tenant scoping is a schema decision rather than a later feature.

## The defining constraint

**Version skew is permanent and asymmetric.**

```
  REPO TIME  (you control)              DEPLOY TIME  (you do not)
  ========================              =========================

  one commit, one tag                   Plugboard v2.3.0    <- you deploy today
    contract/   v2                      ------------------------------------------
    proxy/      v2.3.0                  Telephone v1.8.2    <- tenant A, 8 months
    sidecar/    v2.3.0                                          old, works, will
                                                                not be touched
  always in sync, provably              Telephone v2.1.0    <- tenant B
                                        Telephone v2.3.0    <- tenant C, automated
                                        Telephone v0.9.1    <- pinned in someone's
                                                                Helm chart forever
```

A monorepo makes the *repository* consistent. It does nothing for production, and it is actively
dangerous if it lulls you into assuming the two halves agree. Three consequences:

1. **The wire schema can never be fixed later.** It is the only irreversible artifact in the system.
2. **Capability negotiation is mandatory, not a nicety.** Sidecar selection round-robins across a
   mount, so without negotiation two identical requests routed to different-version sidecars get
   different fidelity, non-deterministically.
3. **Anything requiring the sidecar to change is expensive forever.** Old sidecars are permanent.

## Scope: what it does not do

These are refusals with reasons, not gaps. Document them where users will look, because the
alternative is a tenant spending a day blaming the proxy.

**WebRTC media and data channels.** Media is SRTP, and data channels are SCTP-over-DTLS, both over
ICE-negotiated ephemeral UDP with keys the endpoints derive themselves. The component that relays
that traffic is a **TURN server** (RFC 8656) — a bandwidth-priced UDP relay with a latency SLA, which
is a different product with different economics. RFC 8835 §3.4 requires every WebRTC endpoint to
support TURN, so the boundary is a normal part of every WebRTC deployment rather than a Plugboard
limitation.

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

**Web Push with VAPID.** The browser subscribes against a push service (FCM, Mozilla autopush); the
tenant's app server sends outbound to that service with a VAPID JWT (RFC 8292); the service worker is
served from the tenant's own origin over ordinary HTTPS. Nothing traverses the proxy. **Zero work
required** — this was on the original wish list and needs no support at all.

**NTLM and SPNEGO/Negotiate to tenant backends** (RFC 4559). These authenticate a *TCP connection*,
not a request, via a multi-round-trip handshake pinned to that connection. A tunnel that multiplexes
independent streams cannot express that. The honest "cannot be done" item.

**TLS passthrough.** Encrypted Client Hello (RFC 9849) encrypts the single field such a mode routes
on.

**Full gRPC at the ingress** (as distinct from gRPC-Web, which *is* in scope). `grpc-status` must
travel as an HTTP trailer even on success, and `Plug.Conn` has no trailers API. Blocked before the
tunnel is reached. The gRPC-Web ↔ gRPC bridge belongs **in the sidecar**, which is the only component
adjacent to an HTTP/2 backend — the same position Envoy's `grpc_web` filter occupies.

**Caching.** No response cache in v1, therefore no cache-key design and no cache-poisoning surface.

**Health-probe-based load balancing.** Sidecar selection is registry membership plus liveness, not
active probing.

## Deferred, not refused

- **WebTransport.** Reserved in the contract, shipped later as a separate HTTP/3 terminator that
  speaks the wire contract. Reached Baseline in March 2026 (Safari 26.4); real-world website usage is
  still negligible. See [Architecture](02-architecture.md) for why this does *not* force the tunnel to
  be QUIC.
- **HTTP/3 at the edge** for ordinary HTTP. Buys connection migration, 0-RTT, and no cross-request
  TCP head-of-line blocking. Requires zero tunnel change — it is a front-terminator decision.
- **Trailers, 1xx interim responses, Range/206, WHIP/WHEP, the Connect protocol.** All cheap later
  *because the frame types are reserved in v1*. See [Protocol fidelity](04-protocol-fidelity.md).
