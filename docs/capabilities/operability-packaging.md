---
type: capability
status: planned
authority: rationale
---

# Packaging

**`operability/packaging`** — what every deployable component owes as a distributed artifact, before
it runs.

One boundary organises the whole capability: this is what a **stopped** artifact declares and
guarantees, and nothing here concerns what a running component reports. So the artifact's own
description of its configuration is generated from the same schema its startup validation reads —
the two cannot drift because they are one source — and the contract and durable-schema version
ranges it speaks are readable without starting it, so a **pairing** can be judged before either half
is deployed. [The glossary](../glossary.md#operation-and-artifacts) fixes *artifact*, *input*,
*identity* and *release gate* in the narrow senses this capability uses, because three of those four
already mean something else elsewhere in the set.

It exists because the prior art's published images could not boot, on both sides at once, and the
workflow that claimed to prove the product ran could not have passed: the proxy raised on a signing
value declared in no packaging artifact, two more were set in a builder stage that never crossed into
the runtime image, the sidecar died on a variable its own image never declared, and the deployment
check asserted a plain-transport success status while the shipped defaults redirected and demanded a
protected durable store the checked deployment did not serve ([reference audit](../history/reference-audit.md)).
None of that is prevented by any amount of correct component behaviour, which is the case for owning
it separately. The one thing that side got right — build provenance fed by ldflags and logged at
startup — is carried forward ([carry-forward](../history/carry-forward.md#build-provenance)).

The enumeration of separately deployed components lives here and nowhere else; every capability that
needs the list refers to this one. The component terminating client-facing protocols is called **the
client-facing terminator** throughout — three names for one component, not three components.

## What it owns

- One self-contained artifact per deployable, with what it needs from outside declared
- The generated configuration declaration and example, retrievable from a stopped artifact
- A release gate that starts the published artifact under its shipped protective defaults and asserts its own readiness
- Fixed provenance, a modified tree distinguishable from a build, and neither restatable by a deployment
- The declared contract and durable-schema ranges, their non-widenability, and pairing viability
- Reproducibility, verifiable content identity, minimality, least privilege, and the absence of secrets
- Pinned inputs, a discoverable inventory, recurring vulnerability screening, and redistribution terms
- A published version identifier never coming to mean different content
- Every gate demonstrated to fail against a deliberately non-conforming artifact, and a gate that did not run counted as a failure

## What it does not own

- The identity of a principal or credential — [sidecar credentials](auth-sidecar-credentials.md) — or of custody-managed material — [key custody](security-key-custody.md)
- The endpoint identity of a listening surface — [the listener](tunnel-listener.md)
- The edge obligations of whichever component terminates the client connection — [edge hygiene](proxy-edge-hygiene.md)

## Depends on

- [observability](operability-observability.md) — owns what a *running* component reports: provenance
  at startup, one-pass configuration validation, liveness and readiness
- [schema migration](operability-schema-migration.md) — owns what running code does about a durable
  schema version it cannot operate against; only the stopped declaration is here
- [the wire contract](tunnel-wire-contract.md) — owns how two connected peers negotiate a version
- [conformance](tunnel-conformance.md) — the authority on the contract, and its own distribution is
  not a deployable governed here
- [the sidecar program](sidecar-program.md) — states none of these obligations twice, only the delta
  that follows from the machine being the tenant's

## Shaped by

- [D17 — Five further capabilities are in scope](../decisions/d17-capability-scope.md) — packaging is
  one of them, and it collects obligations that previously existed only as an assumption
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — tenants pin
  sidecar versions indefinitely, so an identifier's content has to be immutable forever
- [D16 — HTTP/2 to clients is in v1](../decisions/d16-http2-to-clients.md) — makes the client-facing
  terminator a separate deployable, and so a third member of the enumerated set
- [D22 — One repository](../decisions/d22-one-repository.md) — every artifact is built from one tree

## The specification

[`operability/packaging`](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
