---
type: decision
status: current
authority: decision
---

# D7 — Timeout taxonomy replaces the single cap

**In force.** There is no request timeout. There are six separately named and separately
configured bounds, each enforced by whichever hop can actually observe the thing it measures, and a
route class that deliberately has no total bound at all. It rules out one global cap, rules out
deriving one bound from another, and rules out treating a bound honoured at one hop as covering the
other.

What this changes for a reader is which cases count as normal. A response that legitimately never
ends — an event stream, a watch API — is an ordinary route class here, not an exception that has to
be talked past a ceiling, and "the request timed out" is never a complete account of a failure:
every terminating condition names which bound ended it. One of the six is measurable only from
inside the tenant's network, so the sidecar enforces it and the proxy only attributes it; expecting
the proxy to hand that value down is a common wrong turn. The reference's single capped
`request_timeout_ms` assumed every request finishes soon, and this decision is the refusal of that
assumption rather than a larger number.

- **Full entry, with rationale and alternatives:** [register D7](../../openspec/changes/rebuild-plugboard/design.md#d7-timeout-taxonomy-replaces-the-single-cap)
- **Shapes:** [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md), [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md), [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
