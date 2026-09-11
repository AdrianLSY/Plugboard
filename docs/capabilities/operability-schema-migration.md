---
type: capability
status: planned
authority: rationale
---

# Schema migration

**`operability/schema-migration`** — versioning the shape of the durable state, so that state gets
the counterpart of what the wire contract gives the wire.

The symmetry is the whole argument. The wire contract exists because sidecars live in tenants'
infrastructure and are never force-upgraded: it carries an explicit version, negotiates a compatible
one, refuses rather than guesses, and grows additively. Durable state has the same exposure pointed
the other way. The operator's own fleet is upgraded instance by instance, so during every deployment
more than one code version is operating against one durable state — and a projection rebuilt from
that state has to stay correct throughout. This capability is that counterpart: a version recorded
in the state itself, a declared compatibility range, ordered and recorded migrations.

The one idea worth carrying away is the decomposition rule, because it is the part that changes how
work is planned rather than how it is checked. Correctness is owed at every *intermediate* point of
an upgrade, not only at its endpoints — so a rename, a retype, a narrowing or a removal of something
the preceding code version reads is never one migration. It becomes a declared sequence, in one
piece with its steps' compatible ranges stated, and whether the preceding version survives each step
is established by running that version's own suite against the migrated state rather than by reading
the migration's declaration.

The second consequence worth naming: additive changes cost nothing, and unknown stored attributes are
preserved across a write rather than dropped. That is the state-side twin of the contract's relay
rule, and it is what stops an older instance from erasing a value a newer one depends on.

## What it owns

- The version recorded in the durable state, validated against the state it describes
- Initialisation only of a provably empty store, and every store the installation holds checked together
- The supported range the running code declares, and compatibility established before anything is served
- Additive-by-default changes, and preservation of the unrecognised without tolerance of the invalid
- Migration identity, one total order, immutability, at-most-once application, and a durable applied set
- One migration at a time, interruption leaving readable state, and a failure not advancing the version
- The decomposition rule, declared reversibility, rollback across a migration, and confirmation for destructive steps
- Projection rebuild across a version change, store-level enforcement surviving, and progress visible enough not to read as a hang
- The tenancy boundary a migration never crosses, its audit record, and sidecar-local state under the same rules

## What it does not own

- What a stopped artifact declares about the ranges it supports — [packaging](operability-packaging.md)
- The readiness and degraded signals that migration progress feeds — [observability](operability-observability.md)
- Versioning of the wire, whose rules this capability mirrors — [the wire contract](tunnel-wire-contract.md)

## Depends on

- [packaging](operability-packaging.md) — the durable schema range is readable from the artifact
  without running it, and a release is gated on that declaration matching what the code enforces

## Shaped by

- [D17 — Five further capabilities are in scope](../decisions/d17-capability-scope.md) — durable schema
  migration is one of the five, previously covered only by assumption
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — the
  reason two code versions operate against one state at once, and so the reason for decomposition
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — the same
  constraint aimed at state instead of wire, and the source of the additive default
- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — scoping
  is structural, so a migration cannot move a row across a tenancy boundary by omission

## The specification

[`operability/schema-migration`](../../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
