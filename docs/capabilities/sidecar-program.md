---
type: capability
status: planned
authority: rationale
---

# The sidecar program

**`sidecar/program`** — the sidecar treated as a program a tenant runs inside their own
infrastructure, rather than as a peer that speaks the wire contract.

Two conditions govern everything in it. You cannot upgrade this artifact, cannot see the machine it
runs on, and cannot read its logs; and the tenant's platform team decides whether it is allowed to run
at all. Every obligation here follows from one of those: its configuration is discoverable without a
support conversation, its failures are attributable from inside the tenant's own infrastructure, its
exit statuses tell one failure class from another, and it bounds its own footprint on a machine it
shares with the backend it serves. [The tenant's view](../how/tenant-view.md) is the same system
described from that side.

The one idea worth carrying away: the backend origin comes from local configuration alone. No
component of a received request can influence which origin is dialled, the remainder is validated
before any connection is opened, and a rejection is never quietly repaired into something dialable.
That is what makes the sidecar safe to place next to a backend that trusts its loopback. The prior art
got this part right and is worth porting close to verbatim — a layered traversal guard rejecting
non-slash-prefixed paths, protocol-relative authorities, any scheme, any host and post-normalisation
escapes, with the query preserved (`telephone.go:656-697`), alongside an entrypoint with distinct
non-zero exits per failure class (`reference/Telephone/cmd/telephone/main.go:47`). See
[carry-forward](../history/carry-forward.md#validate-backend-path).

One boundary is load-bearing and easy to misread. [Packaging](operability-packaging.md) owns every
obligation this artifact carries in common with the proxy and the client-facing terminator — being
self-contained, generating what it declares about its configuration from the schema its own startup
validation reads, fixed provenance, readable version ranges while stopped, no undeclared privilege, no
embedded secret. What is left here is only the delta that follows from the machine being somebody
else's. The prior art's published images did not boot, and it was a failure on both sides: the sidecar
died on a variable its own image never declared, which is a packaging property rather than a
configuration one ([reference audit](../history/reference-audit.md)).

## What it owns

- the configuration schema, its validation before anything is touched, and its fixity for the process lifetime
- startup, readiness with an enumerated reason, drain and exactly-one shutdown, with distinct exit statuses per failure class
- the one hop no other capability owns — composed from local configuration and the remainder alone, with its own bounds, reuse, protection, liveness and failure outcomes
- the gRPC-Web to gRPC translation, declared as a capability and otherwise inert
- the credential store on the tenant's disk, and diagnosis without operator access
- its own resource ceilings, bounded on both a count and an octet axis

## What it does not own

- what travels between it and the proxy — [the wire contract](tunnel-wire-contract.md)
- the obligations it shares with every deployable — [packaging](operability-packaging.md)
- issuing, rotating or revoking the credential it holds — [sidecar credentials](auth-sidecar-credentials.md)
- being chosen to serve an exchange at all — [sidecar registry](tunnel-sidecar-registry.md)

## Depends on

- [the wire contract](tunnel-wire-contract.md) — the sidecar occupies one of the contract's two roles, and its backend failures have to be expressible as outcomes the contract can carry
- [packaging](operability-packaging.md) — owns the artifact obligations this capability states only the tenant-specific delta of
- [observability](operability-observability.md) — what a tenant's own operator can see when the sidecar is stuck

## Shaped by

- [D4 — Runtime: Elixir proxy, Go sidecar, Go H3 terminator later](../decisions/d04-runtime.md) — a single static binary is what makes a tenant's platform team likely to permit it
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — this is the artifact you cannot upgrade, which is why its self-description has to be complete
- [D17 — Five further capabilities are in scope](../decisions/d17-capability-scope.md) — added packaging and moved the common deployable obligations out of here
- [D3 — Capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md) — makes translation a declared capability rather than a guess about the backend
- [D6 — Framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md) — the backend hop's framing and extensions are the sidecar's to resolve, not the proxy's to pass through
- [D7 — Timeout taxonomy replaces the single cap](../decisions/d07-timeout-taxonomy.md) — the backend hop gets its own bounds, distinct from the proxy's

## The specification

[`sidecar/program`](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
