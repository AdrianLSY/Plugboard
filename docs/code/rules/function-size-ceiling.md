---
type: rule
status: planned
authority: rationale
---

# A function is at most 60 non-comment lines

**Gate:** planned — rebuild-plugboard task 3.5 builds the module-size and function-size ceiling gate
for both languages
([tasks.md](../../../openspec/changes/rebuild-plugboard/tasks.md), task 3.5). Until it runs, the
ceiling is an obligation with no automated check.

Sixty non-comment lines per function body, counted per clause rather than per name, so a function
with many clauses is measured clause by clause and a template rendered inline is measured with the
function it sits in. Crossing it is refused, not warned.

## Why

The prior art contains an 813-line `render/1` ([harness](../../method/harness.md),
`docs/method/harness.md:65`). Nothing in it was hard; it was one markup block for four unrelated
resources, and the only reason it reached 813 lines is that no number existed to cross.

**Where 60 comes from.** It is low enough that the case being made unwritable is unwritable by an
order of magnitude rather than by a margin, and rebuild-plugboard's own verification plants a
400-line function ([tasks.md](../../../openspec/changes/rebuild-plugboard/tasks.md), task 3.5) — so
the ceiling has to sit well under 400 for that fixture to be a test of the gate rather than of the
threshold.

**What it would have caught.** The 813-line `render/1`, at more than thirteen times the ceiling. It
would also have caught the twenty `handle_event` clauses' host module long before the
[module ceiling](module-size-ceiling.md) did, because a clause-by-clause count starts failing while
each clause is still individually small.

**A gap in the citation, stated rather than hidden.** Neither [the reference
audit](../../history/reference-audit.md) nor [carry-forward](../../history/carry-forward.md) records
a `file:line` for `render/1`; the figure is recorded in the harness note at the line cited above,
without a path. The function is retrievable from the pinned prior art via
[the obtaining instructions](../../history/obtaining-the-reference.md), and task 3.5's violating
input is what pins the case once the gate lands.
