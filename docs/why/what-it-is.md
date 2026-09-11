---
type: essay
status: current
authority: rationale
---

# What it is

Plugboard is **dynamic ingress for multi-tenant platforms**. It replaces static reverse-proxy
configuration files with routing that applications register for themselves at runtime, over a
persistent outbound tunnel.

That positioning was a decision rather than an obvious starting point, and the alternative it beat is
recorded in [D25 — positioning](../decisions/d25-positioning.md).

## The outbound-tunnel shape

A tenant runs a lightweight sidecar (**Telephone**) next to their backend. The sidecar dials out to
the central proxy (**Plugboard**) and holds the connection open. Traffic arriving at the proxy for
that tenant's mount point is forwarded down the tunnel; the sidecar replays it to the local backend
and returns the response the same way.

This page is orientation. What the tunnel carries, and in what order, is fixed by
[tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md);
what a mount point resolves to is fixed by
[routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md);
and the shape of the sidecar itself by
[sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md).

## What that buys

- **No inbound network path required.** The tenant's backend needs no public IP, no port forward, no
  firewall change, and no inbound security-group rule. The tunnel is outbound-only.
- **Routing changes without restarts.** Mount points live in the database and are projected into an
  in-memory cache; adding a route does not touch a config file or bounce a process.
- **Registration is the deploy.** A backend that starts up and connects a sidecar is routable. A
  backend that dies stops being routable. Autoscaling needs no external service-discovery wiring.
- **Custom domains per tenant**, mapped onto mount points, so a tenant's traffic arrives on their own
  hostname rather than a path prefix under yours.

The last two are the ones with the most machinery behind them:
[tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md)
owns membership and liveness, and
[routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md)
owns the hostname mapping and the ownership check that precedes it.

## Read next

- [Who it is for](audiences.md) — three audiences whose requirements conflict.
- [Version skew](version-skew.md) — the constraint that decides the order of the work.
- [Scope and refusals](scope-refusals.md) — what it will not do, and why.
- [Architecture](../how/architecture.md) — how the pieces fit together.
