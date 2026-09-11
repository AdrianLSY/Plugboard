---
type: decision
status: current
authority: decision
---

# D23 — Contract-first, with a conformance suite

**In force.** A versioned schema is the root artifact, every implementation's types are generated
from it, and an executable conformance suite — not either side's own unit tests — is what settles a
claim about wire behaviour. It rules out hand-maintained types on each side and rules out a single
end-to-end test standing in for the suite.

This sets the order of work as much as the tooling: the schema is frozen before breadth is added,
and the suite's adversarial fixtures are written before the code they gate, so a passing
implementation is one that survived a test it did not author. The reason it is mandatory rather
than tidy is worth knowing before arguing about cost — the old codebase asserted its wire contract
twice, on both sides, and each assertion ran against a different fiction: a channel test that
replaced the serializer with a no-op, and Go tests that marshalled struct tags production never
used. Both sides were green while the wire was broken. Two cheaper alternatives were priced and
rejected because they leave drift prevention to discipline, and discipline does not survive
permanent version skew. In the register that has been removed this was `D3`; see the
[collision table](superseded-register.md) for citations written then.

- **Full entry, with rationale and alternatives:** [register D23](../../openspec/changes/rebuild-plugboard/design.md#d23--contract-first-with-a-conformance-suite)
- **Shapes:** [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
