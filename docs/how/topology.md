---
type: essay
status: current
authority: rationale
---

# Topology and runtime

Where each piece sits, what it owns, and why it is written in the language it is written in. The
runtime choice is [D4](../decisions/d04-runtime.md) — read the reversal recorded there before re-litigating
it. This note is rationale; the components' behaviour is owned by the specifications named at the
foot of it.

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

   IN V1:     +--------------------------------------------------+
              |  EDGE TERMINATOR  --  Go                         |
              |  a CONTRACT SPEAKER, not a rewrite of the proxy. |
              |  Fronts the CLIENT EDGE above: HTTP/2 from       |
              |  clients in v1 (D16), because Bandit cannot.     |
              |  H3 / WebTransport land on it later. Swappable.  |
              +--------------------------------------------------+
```

## Why Elixir for the proxy

This **reverses** an earlier Rust recommendation. The reversal is recorded in full in
[the decision register](../../openspec/changes/rebuild-plugboard/design.md) — read it before re-litigating, because the premise that
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

## The strongest argument against it

**Bandit implements neither HTTP/3 nor RFC 8441 extended CONNECT.** The second bites without
WebTransport ever being mentioned: behind an HTTP/2-terminating CDN, WebSocket upgrades arrive as
extended CONNECT with `:protocol: websocket`, an HTTP/1.1-only upgrade predicate can never match, and
WebSocket fails. Bandit's RFC 8441 issues (#27, #91, #690) are open. HTTP/2 to clients is also where
real per-stream flow control lives — the backpressure mechanism the fidelity contract needs and
WebSocket does not have.

Mitigation is the same as for HTTP/3: put every edge protocol behind the versioned contract, so the
terminator is a contract speaker that can be written in any language and swapped.

## Why Go for the sidecar

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

## What owns the behaviour

- **The client edge:** [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md), [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md), and [D5 — proxied traffic terminates before application middleware](../decisions/d05-pipeline-before-middleware.md)
- **Framing authority:** [D6 — framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md)
- **HTTP/2 to clients, and the separate edge listener:** [D16](../decisions/d16-http2-to-clients.md)
- **Mount-boundary rewriting:** [routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md)
- **Cookie scoping across tenants:** [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md)
- **Per-tenant SNI and ACME:** [routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md)
- **The sidecar binary:** [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md), [operability/packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md)
- **A multi-instance installation:** [D20](../decisions/d20-multi-instance.md)
- **Adjacent notes:** [three primitives](three-primitives.md) · [the tunnel](the-tunnel.md)
