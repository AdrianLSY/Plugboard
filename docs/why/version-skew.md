---
type: essay
status: current
authority: rationale
---

# Version skew

## The defining constraint

**Version skew is permanent and asymmetric.**

You deploy the proxy; tenants deploy sidecars whenever or never. Most of what the rest of the vault
calls irreversible, expensive forever, or negotiated rather than assumed traces back to this page.

## Repo time and deploy time

```
  REPO TIME  (you control)              DEPLOY TIME  (you do not)
  ========================              =========================

  one commit, one tag                   Plugboard v2.3.0    <- you deploy today
    contract/   v2                      ------------------------------------------
    proxy/      v2.3.0                  Telephone v1.8.2    <- tenant A, 8 months
    sidecar/    v2.3.0                                          old, works, will
                                                                not be touched
  always in sync, provably              Telephone v2.1.0    <- tenant B
                                        Telephone v2.3.0    <- tenant C, automated
                                        Telephone v0.9.1    <- pinned in someone's
                                                                Helm chart forever
```

A monorepo makes the *repository* consistent. It does nothing for production, and it is actively
dangerous if it lulls you into assuming the two halves agree.

## Three consequences

1. **The wire schema can never be fixed later.** It is the only irreversible artifact in the system.
2. **Capability negotiation is mandatory, not a nicety.** Sidecar selection round-robins across a
   mount, so without negotiation two identical requests routed to different-version sidecars get
   different fidelity, non-deterministically.
3. **Anything requiring the sidecar to change is expensive forever.** Old sidecars are permanent.

## What this shapes

The consequences above are orientation; each has an artifact that owns it.

- **The decision in force:** [D24 — version skew is the governing constraint](../decisions/d24-version-skew.md).
- **The irreversible artifact:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md),
  and the adversarial suite that gates it,
  [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md).
- **Negotiation, and refusing rather than degrading:** [D3 — capability negotiation](../decisions/d03-capability-negotiation.md),
  with the scope of what is negotiated in [D17](../decisions/d17-capability-scope.md).
- **The selection that makes negotiation mandatory:** [tunnel/sidecar-registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md).

## Read next

- [What it is](what-it-is.md) — the shape this constraint applies to.
- [Scope and refusals](scope-refusals.md) — several refusals are refusals *because* of this page.
- [Architecture](../how/architecture.md) — where the constraint lands in the design.
