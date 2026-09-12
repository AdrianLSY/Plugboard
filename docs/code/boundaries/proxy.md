---
type: guide
status: current
authority: rationale
---

# proxy — the boundary

`proxy/` is the Elixir application the operator runs. It is the only component that knows about
tenants, mounts and certificates, and the only one holding durable state.
[D4](../../decisions/d04-runtime.md) records why it is Elixir, including the reversal of an earlier
Rust recommendation.

## What it owns

- The tenant-scoped projections and the mutations over them, with the acting principal in every
  signature rather than in a convention — [D8](../../decisions/d08-tenant-scoping.md).
- The sidecar registry, selection across a mount, failover, and convergence across an installation of
  more than one instance — [D20](../../decisions/d20-multi-instance.md).
- The tunnel endpoint a sidecar dials, and the credential exchange that admits it.
- Routing: longest-prefix matching over the mount hierarchy, and the terminal-mount invariant that
  makes it correct — [D10](../../decisions/d10-carry-forward.md).
- Custom-domain ownership verification and the certificate lifecycle —
  [D9](../../decisions/d09-domain-ownership.md).
- The dedicated proxied-traffic pipeline that runs before any application middleware —
  [D5](../../decisions/d05-pipeline-before-middleware.md).

## What it must not own

- **The client edge for HTTP/2 and later.** That is `terminator/`, from v1 rather than later, because
  Bandit implements neither HTTP/3 nor RFC 8441 extended `CONNECT` —
  [D16](../../decisions/d16-http2-to-clients.md).
- **Dialling a tenant's backend.** The hop from the tunnel to an origin belongs to `sidecar/`, which
  runs inside the tenant's own infrastructure and is the only side that can reach it.
- **The schema.** Frame shapes, capability names and error codes are read from `contract/`. A proxy
  that defines its own is the two-fictions failure again with one fiction renamed.
- **Application middleware on proxied traffic.** No body parser, method override, HEAD folding,
  content negotiation, session or CSRF layer touches a proxied request.

## Why it is separated this way

The prior art put the routing projection, the credential store and the hooks subsystem in one place
and let each reach into the others: a global full-table read plus a full-keyspace diff ran on any
tenant's change, and a token update took no actor at all, yielding a cross-tenant write
([reference audit](../../history/reference-audit.md)). Separating the edge and the origin hop leaves
the proxy owning exactly the state that has to be tenant-keyed, which is what makes the isolation
promise checkable.

Component root: [`proxy/`](../../../proxy/README.md).
Behaviour: [routing/mount-points](../../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md),
[tunnel/sidecar-registry](../../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md),
[tenancy/isolation](../../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md).
