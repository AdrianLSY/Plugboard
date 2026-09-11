---
type: decision
status: current
authority: decision
---

# D9 — Domain ownership verification precedes certificate issuance

**In force.** A tenant proves it controls a custom domain before anything asks a certificate
authority for that name, and the proof is a v1 blocker rather than later hardening. It rules out the
shape this most often takes in a young product: accept the domain claim first-come, get routing
working, and add verification once someone asks for it.

The reason to know this before touching custom domains is the size of the failure it prevents. With
issuance layered onto an unverified claim, an ordinary routing mistake stops being a misrouted request
and becomes a publicly trusted certificate for a name the claimant does not own — a mistake that
reaches outside this system and cannot be withdrawn by fixing the bug. So the custom-domain flow has
an ordered gate in it (claim, then proof, then issuance) and no path that can reach the issuance step
from a claim in any other state. This was reclassified rather than merely scheduled: it sat as a v2
feature and was moved into v1 on exactly that argument, which is worth knowing before proposing to
move it back out to get a demo working sooner.

- **Full entry, with rationale and alternatives:** [register D9](../../openspec/changes/rebuild-plugboard/design.md#d9-domain-ownership-verification-precedes-certificate-issuance)
- **Shapes:** [routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md), [security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
