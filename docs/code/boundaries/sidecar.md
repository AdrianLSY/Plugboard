---
type: guide
status: current
authority: rationale
---

# sidecar — the boundary

`sidecar/` is the Go program a tenant runs beside their own backend. It dials out to the proxy, so it
needs no inbound network path and no credential the tenant's platform team cannot read for themselves.
[D4](../../decisions/d04-runtime.md) records why it is Go, and the point is not only the static binary:
it is the language that team will read before allowing the process into their pods.

## What it owns

- Dialling the tenant's backend, including target validation and the refusal to derive an origin from
  request content.
- The translation between the carried frames and whatever the backend speaks, the gRPC-Web to gRPC
  bridge included — it is the one component adjacent to an HTTP/2 backend.
- Its own configuration schema, validated in one pass before anything is accepted, and its process
  lifecycle and signal handling.
- The capability set it declares at tunnel join, which is what lets a request it cannot back be
  refused with a reason rather than served at reduced fidelity —
  [D3](../../decisions/d03-capability-negotiation.md).

## What it must not own

- **Routing and tenancy.** Which mount a request belongs to, and whether a principal may act on it,
  are decided before the frame reaches a tunnel. A sidecar that decided either would be a second
  authority in the tenant's own network.
- **The client edge.** It never terminates a client connection; it only ever receives frames.
- **The schema.** Frame shapes and capability names come from `contract/`. A sidecar inventing a
  capability name is unnegotiable by definition.
- **Durable installation state.** Nothing here outlives the process except the tenant's own
  configuration and its credential at rest.

## Why it is separated this way

The tenant's infrastructure is the constraint that shapes this component. Egress policy belongs to
someone else, which is why the v1 transport is a WebSocket over TLS on 443
([D19](../../decisions/d19-tunnel-transport.md)); and the operator cannot upgrade this binary, which
is why every declared capability is permanent and why
[version skew](../../why/version-skew.md) governs the whole plan.

Component root: [`sidecar/`](../../../sidecar/README.md).
Behaviour: [sidecar/program](../../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md).
