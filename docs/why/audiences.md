---
type: essay
status: current
authority: rationale
---

# Who it is for

Three audiences, and their requirements conflict. Naming the conflict is more useful than pretending
it resolves:

| audience | wants | costs the others |
|---|---|---|
| **Platform operators** (the buyers) | tenant isolation, predictable failure, an audit trail, boring upgrades | slows feature work; forces tenancy into the data model on day one |
| **Contributors** | fast local setup, a fast test suite, small reviewable units, clear module boundaries | rules out "clever"; forces a pure core with a thin database edge |
| **The author's portfolio** | legible judgment, depth, decisions defensible under questioning | tempts over-engineering; the mitigation is that every decision is written down with its rationale, so depth is *documented* rather than *built* |

## Which audience wins a tie

The operator audience is the one that sets hard requirements. "One tenant cannot affect another" is a
sold promise, which is why tenant scoping is a schema decision rather than a later feature.

That is the tie-break, not a slogan: it is why
[D8 — tenant scoping in the data model](../decisions/d08-tenant-scoping.md) was taken on day one, and
what the promise actually obliges is fixed by
[tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md) rather
than by this page. The same tie-break is where the isolation work's cost was priced —
[D25 — positioning](../decisions/d25-positioning.md) records that the argument terminates there.

## Read next

- [What it is](what-it-is.md) — the system, and what it sells.
- [Version skew](version-skew.md) — the constraint the operator audience imposes hardest.
- [Method](../code/contributing.md) — what the contributor audience's requirements became in practice.
