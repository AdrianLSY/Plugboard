---
type: essay
status: current
authority: rationale
---

# Alternatives

Five things a reader will reasonably ask about instead: **ngrok**, **cloudflared**, **frp**,
**Tailscale Funnel**, and a **reverse proxy taking dynamic configuration from a provider** (Caddy or
Traefik). For each: what it does that this does not, and what this does that it does not.

## How to read the claims on this page

- **Every claim about another product carries a link to that product's own documentation and the date
  it was checked.** All the dates here are 2026-09-11. Where a claim could not be verified it is
  marked `Unverified` rather than asserted, and one such marker appears below.
- **Claims in the "what this does" halves are obligations, not shipped behaviour.** No product code
  exists in this repository yet — the work that builds it is
  [tasks.md](../../openspec/changes/rebuild-plugboard/tasks.md), at zero of 717. So each one links to
  the specification that owns it; the specification is the claim, and this page is a pointer.
- **This page does not compare performance and does not rank.** There is no benchmark to cite, and
  four of the five are mature shipped products while this one is a plan.

## cloudflared appears twice in this repository, for two different reasons

Read this before the cloudflared section, or the argument looks circular.

| where | what cloudflared is being used as |
|---|---|
| [D4 — runtime](../decisions/d04-runtime.md) | **Runtime evidence.** The register's D4 table rebuts the claim that Go has no production-grade QUIC stack with: *"`quic-go` powers **cloudflared** — structurally this exact product — plus `frp`, `reverst`, Caddy, Traefik"* ([register D4](../../openspec/changes/rebuild-plugboard/design.md#d4-runtime-elixir-proxy-go-sidecar-go-h3-terminator-later)). The argument there is about a **library**: an outbound-tunnel product of this shape already runs on this stack at scale, so the stack is not the risk. |
| this page | **A competing product.** The argument here is about **positioning**: who operates the ingress path, whose network the traffic crosses, and whether the tenant is a first-class entity. |

The two do not support each other and neither weakens the other. That `quic-go` is proven is a fact
about a dependency; whether Cloudflare Tunnel is the right thing for a platform operator to buy is a
different question, answered below. A reader who collapses them will think the project cites its own
competitor as support — it does not. The distinction is load-bearing rather than pedantic: the
*library* half is what [topology](../how/topology.md) leans on when it says a shipped WebTransport
would mean *"`quic-go` plus `webtransport-go` in the binary"*, and none of that has any bearing on
whether Cloudflare Tunnel is a good purchase.

## The axis that separates all five

The positioning is **multi-tenant platform ingress**, not a developer tunnel — and that was a
decision taken *against* the recommendation, with its cost priced rather than discovered:
[D25 — positioning](../decisions/d25-positioning.md). The reason the axis matters is in
[who it is for](audiences.md): the operator audience sets the hard requirements, and *"one tenant
cannot affect another"* is a sold promise, which is why tenancy is a schema decision. What that
promise obliges is
[tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md), not
this page.

So the recurring question below is not "which is faster" but: **is the tenant a first-class entity,
and who operates the path?**

## ngrok

**What it does that this does not.** ngrok runs the ingress path for you as a global service:
*"ngrok's globally distributed cloud service runs on points of presence all around the world to
enable fast, low latency traffic to your applications"*
([Points of Presence](https://ngrok.com/docs/gateway/points-of-presence), checked 2026-09-11), across
eight named regions on that page. It carries protocols this project refuses: *"TCP endpoints enable
you to deliver any network service with a TCP-based protocol"*
([TCP Agent Endpoints](https://ngrok.com/docs/universal-gateway/tcp), checked 2026-09-11) — whereas
here there are [three primitives](../how/three-primitives.md) and TLS passthrough is a stated refusal
([scope and refusals](scope-refusals.md)). And it has a policy language for edge behaviour:
*"ngrok's Traffic Policy is a configuration language that offers you the flexibility to filter,
match, manage, and orchestrate traffic to your endpoints"*
([Traffic Policy](https://ngrok.com/docs/traffic-policy/), checked 2026-09-11). Nothing here
corresponds to that; edge behaviour is fixed by
[proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md), not
configured per endpoint.

> **Unverified.** Whether ngrok can be run entirely inside an operator's own infrastructure, under an
> enterprise or private-deployment arrangement — needs checking against ngrok's enterprise
> documentation and contract terms. The public documentation cited above describes the agent
> connecting to ngrok's own points of presence; it does not say a data plane can or cannot be
> operated by the buyer, and this page will not guess.

**What this does that it does not.** The operator owns the whole path, and therefore owns the problem
that follows from owning it: the sidecar fleet is permanently version-skewed and cannot be forced to
upgrade ([version skew](version-skew.md), [D24](../decisions/d24-version-skew.md)). For a hosted
service the agent-upgrade question is the vendor's; here it is the buyer's, which is why the wire
schema is the only irreversible artifact and is gated by an adversarial suite written before the code
—
[tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
and
[tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md),
under [D23](../decisions/d23-contract-first.md). The consequence a tenant sees is refusal rather than
quiet loss of fidelity: `tunnel/wire-contract` carries the requirement *"Refusal rather than silent
degradation"*, shaped by [D3](../decisions/d03-capability-negotiation.md).

## cloudflared (Cloudflare Tunnel)

The nearest thing to this system's tunnel half, and the reason the [tunnel](../how/the-tunnel.md)
shape is not novel.

**What it does that this does not.** The same outbound-only property, shipped and operated:
*"`cloudflared` initiates an outbound connection through your firewall from the origin to the
Cloudflare global network"*, and Cloudflare Tunnel *"provides you with a secure way to connect your
resources to Cloudflare without a publicly routable IP address"*
([Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/),
checked 2026-09-11). It runs that tunnel over QUIC by default — the `protocol` parameter
*"[s]pecifies the protocol used to establish a connection between `cloudflared` and the Cloudflare
global network"*, with values `auto`, `http2` and `quic` and a default of `auto`
([Tunnel run parameters](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/),
checked 2026-09-11). This project's v1 tunnel is deliberately not QUIC:
[D19](../decisions/d19-tunnel-transport.md).

**What this does that it does not.** Traffic across a Cloudflare Tunnel transits Cloudflare's
network — *"traffic flows in both directions over the tunnel between your origin and Cloudflare"*
(same page, checked 2026-09-11). Here the operator's own instances are the path, and an installation
is explicitly a set of instances the operator runs: [D20](../decisions/d20-multi-instance.md), with
the shape in [topology](../how/topology.md). The second difference is the tenant: a mount point is
resolved from a tenant-keyed projection
([routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md)),
every mutation takes an acting principal
([auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md),
[D8](../decisions/d08-tenant-scoping.md)), and a tenant's own hostname is mapped only after an
ownership check
([routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md),
[D9](../decisions/d09-domain-ownership.md)).

## frp

Structurally the closest of the five, because in frp the process being routed to is what declares the
route.

**What it does that this does not.** *"frp is a fast reverse proxy that allows you to expose a local
server located behind a NAT or firewall to the Internet"*, and *"[i]t currently supports **TCP** and
**UDP**, as well as **HTTP** and **HTTPS** protocols"*
([frp README](https://github.com/fatedier/frp), checked 2026-09-11). TCP and UDP are outside the
three primitives here — see [scope and refusals](scope-refusals.md). It is also self-hosted and
shipped today, which is two things this is not yet.

**What this does that it does not.** frp's client-to-server authentication is a shared secret:
*"Token authentication is a simple authentication method that only requires configuring the same
token in both the frp client (frpc) and server (frps) configuration files"*
([frp authentication](https://gofrp.org/en/docs/features/common/authentication/), checked
2026-09-11). One credential shared by every client is exactly the property
[D25](../decisions/d25-positioning.md) refused to defer: the operator audience's first question is
what stops tenant A affecting tenant B, so credentials are per-sidecar and per-tenant
([auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md),
[security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md)),
and isolation is a schema property rather than a deployment convention
([tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md)). The
other difference is the contract: what a client may declare, and what happens when it declares
something the peer cannot back, is a versioned negotiated artifact here
([tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)).

## Tailscale Funnel

**What it does that this does not.** Funnel exposes a machine that is already a member of the
operator's own private network — it routes traffic *"from the broader internet to a local service running on a device
in your Tailscale network"* ([Funnel](https://tailscale.com/kb/1223/funnel), checked 2026-09-11) — so
the same node stays reachable privately across the tailnet. Nothing in this project provides a
private overlay network; the tunnel carries only what a mount point routes to it
([the tunnel](../how/the-tunnel.md)).

**What this does that it does not.** Funnel's documented limits are narrow for platform ingress, all
from the same page (checked 2026-09-11): *"Funnel can only listen on ports `443`, `8443`, and
`10000`"*; *"Funnel can only use DNS names in your tailnet's domain"* (`tailnet-name.ts.net`);
*"Traffic sent over a Funnel is subject to non-configurable bandwidth limits"*; and *"Funnel only
works over TLS-encrypted connections"*. Against that, a tenant here arrives on **their own
hostname**, mapped to a mount point after an ownership check that precedes certificate issuance
([routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md),
[D9](../decisions/d09-domain-ownership.md)) — see [what it is](what-it-is.md) for why custom domains
per tenant are part of the product rather than an add-on. The limits are also the operator's to set:
there is no single cap but six separately named and separately configured bounds, and one route class
that deliberately has no total bound at all
([D7 — timeout taxonomy](../decisions/d07-timeout-taxonomy.md), owned by
[proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md)).

## A reverse proxy with dynamic configuration (Caddy, Traefik)

The strongest alternative, and the one worth being most careful about — because "routing changes
without restarts" is **not** a differentiator. Both of these already do it.

**What it does that this does not.** Caddy changes configuration over an HTTP API with rollback:
*"Configuration changes are lightweight, efficient, and incur zero downtime. If the new config fails
for any reason, the old config is rolled back into place without downtime"*
([Caddy API](https://caddyserver.com/docs/api), checked 2026-09-11). Traefik takes its routing from
infrastructure it watches: *"Traefik queries the provider APIs in order to find relevant information
about routing, and when Traefik detects a change, it dynamically updates the routes"*, where a
provider is an *"infrastructure component, whether orchestrators, container engines, cloud providers,
or key-value stores"*
([Traefik providers](https://doc.traefik.io/traefik/reference/install-configuration/providers/overview/),
checked 2026-09-11) — seventeen of them on that page, including Kubernetes, Docker, Consul and etcd.
That is a breadth of integration, plus a whole middleware and certificate feature surface, that this
project has no plan to match.

**What this does that it does not.** The difference is the **direction of the connection and the
source of the configuration**. A Traefik service names its backends by URL — the `url` field
*"[p]oints to a specific instance"*
([Traefik service configuration](https://doc.traefik.io/traefik/reference/routing-configuration/http/load-balancing/service/),
checked 2026-09-11) — so the routing arrives from an infrastructure API the proxy watches, and the
proxy is the side that opens the connection to the instance. Here the routing arrives from the
process being routed to, over the same connection that will carry the traffic, and that connection is
outbound from the tenant: registration *is* the deploy ([what it is](what-it-is.md)), membership and
liveness are the registry's
([tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md)),
and the tenant's backend needs no inbound path
([sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)). Which is
why the comparison to make is not Caddy-versus-this but **Caddy plus a tunnel product** versus this —
and at that point the question is back on the axis above: is the tenant a first-class entity in the
thing doing the routing?

## The honest summary

Four of these five ship today and this one does not. The claim is not that they are inadequate at
what they do; it is that none of them is sold as multi-tenant platform ingress with tenant isolation
as a structural promise, which is the position [D25](../decisions/d25-positioning.md) chose against
the recommendation and priced on the way in. If that promise is not what you need, one of the five
above is very likely the better answer, and [scope and refusals](scope-refusals.md) is the faster way
to find out.

## Read next

- [What it is](what-it-is.md) — the positioning this page defends.
- [Who it is for](audiences.md) — the three audiences, and which one wins a tie.
- [D25 — positioning](../decisions/d25-positioning.md) — the decision, with its cost.
- [D4 — runtime](../decisions/d04-runtime.md) — where cloudflared appears as evidence rather than as
  a competitor.
- [Scope and refusals](scope-refusals.md) — the protocols the comparisons above keep running into.
