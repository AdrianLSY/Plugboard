---
type: decision
status: current
authority: decision
---

# D10 — Carry-forward is explicit and cited

**In force.** Whatever the previous attempt got right is reused only when someone names the item
and cites where it lived; nothing is inherited merely because it was already written. That rules
out both a clean start that quietly loses hard-won knowledge and a port that drags the old
implementation along with the idea.

For a reader, this turns prior art into a finite, checkable list rather than a place to browse:
roughly sixty items, each carrying a citation, and one of them load-bearing in a way no comment in
the old code records — a database-level invariant is the reason a cheap routing lookup is correct
at all, and a rebuild that reproduced the lookup without the invariant would be subtly wrong. The
list also records refusals, so bringing back the correlation-id machinery the decision deletes is a
regression rather than a new idea. One warning before citing this number: in the register that was
removed, `D10` denoted the WebTransport decision, which now sits at `D26` — see the
[collision table](superseded-register.md) before trusting a `D10` citation written earlier.

- **Full entry, with rationale and alternatives:** [register D10](../../openspec/changes/rebuild-plugboard/design.md#d10-carry-forward-is-explicit-and-cited)
- **Shapes:** [routing/mount-points](../../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
