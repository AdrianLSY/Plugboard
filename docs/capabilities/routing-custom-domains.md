---
type: capability
status: planned
authority: rationale
---

# Custom domains

**`routing/custom-domains`** — a tenant bringing their own hostname: claiming it against one of their
mounts, proving they control it, and the certificate that terminates connections for it.

This is the capability where a routing mistake stops being a routing mistake. Everywhere else in the
set, getting the matching wrong sends a request to the wrong backend; here it means a publicly
trusted certificate issued for somebody else's hostname, which is an incident no rollback undoes.
That single asymmetry is why verification is a gate rather than a step: a claim confers nothing until
ownership is established — no byte served, no certificate requested — and competing claims for one
hostname are resolved by which claimant proved control, never by which arrived first
([D9](../decisions/d09-domain-ownership.md)).

The rest follows from taking that gate seriously. A challenge is unpredictable and bound to one
claim, so it cannot be replayed against another. The responder that answers it belongs to the edge
and never to a tenant, so no tenant can answer a challenge for a hostname they do not hold.
Verification lapses and is re-checked, because control of a hostname changes hands. A wildcard is
provable by delegation only, and loses to an exact match wherever both apply. And once a hostname is
served, traffic on it is handled identically to traffic on the platform's own hostname — the claim is
selected by the authority the connection established, and nothing downstream can tell which door the
request came through.

The prior art shipped the affinity, not the discipline, and left two instructive holes. Its
domain-affinity request pipeline kept a content-type gate that the path-prefix pipeline had
deliberately removed, so the multi-tenant path was narrower on a custom hostname than on the platform
one (`router.ex:157`); and deleting a path did not cascade to its domain affinities, which stayed
active and permanently squatted the uniqueness index on the hostname (`paths.ex:365-406`). See
[the reference audit](../history/reference-audit.md) and
[the threat model](../how/threat-model.md).

## What it owns

- the claim: one hostname against one mount, normalised the same way everywhere it is compared
- verification — unpredictable challenges bound to one claim, an edge-owned responder, re-checking and lapse, and conflict resolution by proof
- wildcard claims by delegation only, and exact-match precedence over them
- issuance, renewal ahead of expiry, bounded and non-destructive failure, and expiry surfaced before it becomes an outage
- certificate selection by the hostname requested at connection setup, and application-protocol negotiation there
- per-tenant isolation of certificate material, and consistency of verification and certificate state across serving instances
- the unencrypted listener's two behaviours, per-tenant bounds on claims and issuance, and removal that stops service promptly

## What it does not own

- the mount a claim names, and the hierarchy it lives in — [mount points](routing-mount-points.md)
- how a private key is generated, stored, rotated and destroyed — [key custody](security-key-custody.md)
- who may claim, verify or remove a hostname on a tenant's behalf — [tenant isolation](tenancy-isolation.md)
- what happens to a request after its claim is selected — [edge hygiene](proxy-edge-hygiene.md), then [HTTP fidelity](proxy-http-fidelity.md)
- the reserved-prefix enumeration the challenge path is drawn from — [mount points](routing-mount-points.md)

## Depends on

Nothing. Its specification names no other capability.

## Shaped by

- [D9 — Domain ownership verification precedes certificate issuance](../decisions/d09-domain-ownership.md) — made verification the gate the whole capability is built around, rather than a check performed alongside issuance
- [D17 — Five further capabilities are in scope](../decisions/d17-capability-scope.md) — put key custody in the set, which is what lets this capability state isolation and defer the key's lifecycle to a capability that exists
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made consistency of verification and certificate state across serving instances an obligation, since any instance may terminate the connection
- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — makes a claim's tenancy structural, so cross-tenant visibility is not a filter someone remembers to apply
- [D16 — HTTP/2 to clients is in v1, and the edge listener is a separate component](../decisions/d16-http2-to-clients.md) — put certificate selection and protocol negotiation in the same place, at connection setup in the terminating tier

## The specification

[`routing/custom-domains`](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
