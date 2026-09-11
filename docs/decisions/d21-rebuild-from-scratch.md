---
type: decision
status: current
authority: decision
---

# D21 — Rebuild from scratch; the reference is prior art only

**In force.** The system is written new, and the previous codebase is consulted the way you consult
an autopsy — read-only, cited by `file:line`, never a base to repair. It rules out restructuring
that code, and it rules out treating its large test suite as the specification the rebuild has to
satisfy.

What a reader most needs to know is that this was not a preference for greenfield work. The
alternative — keep the code, keep twenty thousand lines of tests as an executable specification —
was taken seriously and rejected only after an audit found the suite split in two, its
asynchronous and distributed half worthless or self-defeating, and found the failures to be
ceilings frozen into the wire schema rather than bugs sitting on top of a sound design. The
salvage that survived that audit is the cited list in [D10](d10-carry-forward.md), which is why a
finding in the old tree is evidence about a defect and not a working example to copy. Note also
that this decision was `D1` in the register that has since been removed; a bare `D1` citation
written before the two registers were consolidated most likely means this one.

- **Full entry, with rationale and alternatives:** [register D21](../../openspec/changes/rebuild-plugboard/design.md#d21--rebuild-from-scratch-the-reference-is-prior-art-only)
- **Shapes:** [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), [operability/packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
