---
type: capability
status: planned
authority: rationale
---

# Tenant isolation

**`tenancy/isolation`** — the promise one tenant cannot observe, affect or degrade another, held as a
property of the data model and of every operation's signature rather than as a check callers remember.

This is the capability the product is sold on. Multi-tenant platform ingress that leaks between
tenants has nothing left to sell, so isolation is not a layer over routing and the tunnel — it is the
constraint they are built inside. It also fixes vocabulary for all sixteen specifications: a
**tenancy** is the boundary other capabilities call a tenant, a **routing entry** is a node in the
path hierarchy whether or not that node is a mount point, an **instance** is one running process and
the **installation** is every instance under one operator's configuration. *Node* is reserved for the
path hierarchy and never means a process. See [the vocabulary triple](../glossary.md#the-vocabulary-triple).

The one idea worth carrying away: isolation here is structural. Every resource belongs to exactly one
tenancy, every read is scoped by the requesting principal's tenancy, and every mutation takes the
acting principal as an argument, so a caller has nothing to forget. The prior art shows what the
alternative costs, and the failures were omissions rather than broken checks: `update_token/2` took no
actor at all while its sibling `revoke_token/2` did (`telephone_tokens.ex:353-363`), and `create_path`
would restore another user's soft-deleted path and hand the caller ownership while the original
owner's grant survived (`paths.ex:219-241`). Neither is a bug in a scoping rule; both are a scoping
rule that was never reached. Cited in [the reference audit](../history/reference-audit.md).

The second idea is what more than one proxy process does to a ceiling. A per-tenant bound is one value
for the installation, not one value per instance — accounted against local observation, a limit would
hand a tenant as many allowances as the operator happens to be running, which falsifies the promise
above. So the bound, the refusal, the accounting across restart and partition, and the total an
operator reads are all stated for the installation.

## What it owns

- attribution of every resource to exactly one tenancy, and reads scoped to the caller's
- authorization carried by the mutation itself, and the role model's bounded, inherited grants
- per-tenant ceilings on every dimension, accounted once for the installation
- fault containment, and refusals that disclose nothing about another tenant
- the audit trail — append-only, one trail for the installation, with a stated ordering
- the vocabulary triple, and the reservation of *node* for the routing hierarchy

## What it does not own

- authenticating the principal whose tenancy is then honoured — [sidecar credentials](auth-sidecar-credentials.md)
- the hierarchy the role model grants authority over — [mount points](routing-mount-points.md)
- custody of the key material a tenant's credentials rest on — [key custody](security-key-custody.md)
- the metrics, traces and readable totals a per-tenant number is served from — [observability](operability-observability.md)

## Depends on

- [the listener](tunnel-listener.md) — the admission surface where a tenant's connections first meet a bound, and the accepting instance a bound is not scoped to
- [observability](operability-observability.md) — a tenant's consumption is only an installation total if it can be read as one

## Shaped by

- [D8 — Tenant scoping in the data model, not in queries](../decisions/d08-tenant-scoping.md) — put the boundary in the schema and the function signature, where it cannot be omitted
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — made a ceiling an installation value and settled the vocabulary this capability fixes
- [D25 — Positioning: multi-tenant platform ingress](../decisions/d25-positioning.md) — made isolation the load-bearing promise rather than a hardening task
- [D27 — Observability before the hot path](../decisions/d27-observability-first.md) — a per-tenant total is a first-class surface, not instrumentation added afterwards

## The specification

[`tenancy/isolation`](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
