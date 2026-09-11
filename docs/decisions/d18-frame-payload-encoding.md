---
type: decision
status: current
authority: decision
---

# D18 — Frame payloads are encoded from a binary interface definition, with generated codecs

**In force.** The insides of a frame — a request head, a response head, the control frames — are
described in a binary interface definition and their codecs are generated from it, while bodies stay
raw octets throughout. Hand-written encoders per language are ruled out, and so is a JSON envelope
inside the binary frame.

What a reader gets from this is that backward compatibility is a property of the encoding rather than
a habit of reviewers: field numbering makes an additive change additive whether or not anyone
remembers the rule, which is the same trade the rebuild makes everywhere — structure instead of
discipline. It is also what makes "write a sidecar in any language" an offer that can be taken up,
since the codecs come out of the definition rather than out of somebody's afternoon. Two costs were
accepted knowingly: a schema toolchain becomes a build dependency, and a frame is not readable
without a tool — tolerable only because the conformance work has to produce an octet-level inspector
anyway.

- **Full entry, with rationale and alternatives:** [register D18](../../openspec/changes/rebuild-plugboard/design.md#d18--frame-payloads-are-encoded-from-a-binary-interface-definition-with-generated-codecs)
- **Shapes:** [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
