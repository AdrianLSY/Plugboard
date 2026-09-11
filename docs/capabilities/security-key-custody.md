---
type: capability
status: planned
authority: rationale
---

# Key custody

**`security/key-custody`** — where every piece of cryptographic material in the installation lives,
what makes it unusable to anyone who copies the store, which components may hold which of it, and how
each kind of it is replaced and destroyed.

The capability's premise is that unlisted material is unrotatable material. So it begins with a closed
inventory: every kind of key the installation holds is a **custody class**, and each class states its
purpose, who may replace it, whether service can start without it, and — the distinction that does
most of the work — whether a holder may obtain the material at all or may only ask for operations to
be performed with it. A class nobody enumerated has no rotation authority, no destruction path and no
place to be looked for during an incident. See [the glossary](../glossary.md#credentials-and-key-material)
for that term, *protection material* and *root material*.

It sits underneath the capabilities readers usually arrive from. Custom domains decide which
certificate answers a hostname and prove the claim behind it; sidecar credentials decide what a
credential means and when it expires; the listener presents an endpoint identity. Each of those takes
the material as given, and this is where it actually comes from, gets protected, reaches the instances
that serve its subject, and stops existing. Its trust boundary is the installation: material never
crosses the tunnel, and no interface hands back a private key.

The prior art got two pieces of this genuinely right and they are worth re-deriving rather than
reinventing — purpose-scoped derivation with a version suffix, where rotation was designed in from the
start (`crypto.ex:74-79`), and boot-time validation that refused a missing, undersized or literal
dev-default secret before the supervision tree came up (`application.ex:64-97`); both in
[carry-forward](../history/carry-forward.md#purpose-scoped-key-derivation). What it got wrong is the
same lesson from the other side: the test configuration lowered the password-hashing cost until the
property it was protecting was gone (`reference/Plugboard/config/test.exs:4`,
[reference audit](../history/reference-audit.md#the-test-config-deletes-production-properties)).

## What it owns

- the closed inventory of custody classes, and what each class declares about itself
- generation from a strong source, and the allowlist of permitted key parameters
- protection at rest, held apart from what it protects, derived per purpose and versioned
- which classes a holder can obtain, and which it can only have operations performed with
- distribution to the instances that serve a subject, and to no others
- replacement, forced replacement, destruction, and the records that outlive the material

## What it does not own

- issuing a certificate, or proving the hostname claim that precedes issuance — [custom domains](routing-custom-domains.md)
- what a credential authorises, who may hold one, and when it expires — [sidecar credentials](auth-sidecar-credentials.md)
- presenting the endpoint identity on an accepted connection — [the listener](tunnel-listener.md)
- the sidecar's own credential store, which is outside this trust boundary — [the sidecar program](sidecar-program.md)

## Depends on

- [tenant isolation](tenancy-isolation.md) — no operation on one tenant's behalf reaches another tenant's material, which is that capability's promise resting on this one
- [custom domains](routing-custom-domains.md) — a tenant private key that must never terminate another tenant's connection, and certificate state shared across instances
- [sidecar credentials](auth-sidecar-credentials.md) — owns the credential and explicitly excludes the material underneath it, which lands here
- [the listener](tunnel-listener.md) — its endpoint identity has to be replaceable without invalidating a fleet of sidecars pinned to it
- [observability](operability-observability.md) — rotation progress, a stalled rotation and the custody state of every item are visible without the material

## Shaped by

- [D9 — Domain ownership verification precedes certificate issuance](../decisions/d09-domain-ownership.md) — put an ordered gate before issuance, so no path reaches key generation from an unproven claim
- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — made the tenant boundary around material structural rather than a filter a caller remembers
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made distribution between instances, and an isolated instance's behaviour, part of the subject
- [D10 — Carry-forward is explicit and cited](../decisions/d10-carry-forward.md) — the derivation scheme and the boot-time check are re-derived from citations, not from memory

## The specification

[`security/key-custody`](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
