---
type: rule
status: current
authority: rationale
---

# A module is at most 300 non-comment lines

**Gate:** `ci/gates/size_ceilings.py` — non-comment lines per file, for every declared source
language. Python is out of scope by declaration in `ci/vault.json`, with the reason printed on every
run beside a live measurement: each tracked Python file counted, and the ones over the ceiling named
with their counts.

Three hundred non-comment lines per file, counted per module rather than per repository, and refused
rather than warned. A file crossing it is split along the responsibilities that made it long, not
padded with comments to move the count.

## Why

The prior art's admin UI held a 1,380-line LiveView handling four unrelated resources with twenty
`handle_event` clauses ([harness](../../method/harness.md), `docs/method/harness.md:65-66`). No
review caught it, because nothing about the file's growth was ever an event — each clause was a small
addition to something already large.

**Where 300 comes from.** It is the size of the best module the prior art produced: `accounts.ex` at
297 lines, untouched generated auth, single responsibility, no duplicated projection and no bolted-on
second resource — recorded as
[the cleanest context in the tree](../../history/carry-forward.md#accounts-ex-quality-baseline). So
the ceiling sits one line above demonstrated good practice rather than at a round number chosen for
comfort.

**What it would have caught.** The 1,380-line LiveView, at more than four times the ceiling — and
caught it at its first crossing of 300, which is the point where splitting it was still cheap. It
would not have caught `accounts.ex`, which is the evidence that the number is set where working code
already sits.

**A gap in the citation, stated rather than hidden.** Neither [the reference
audit](../../history/reference-audit.md) nor [carry-forward](../../history/carry-forward.md) records
a `file:line` for the LiveView itself; the figure is recorded in the harness note at the lines cited
above, without a path. The 297-line figure for `accounts.ex` is cited to its anchor. The module's own
path is retrievable from the pinned prior art via
[the obtaining instructions](../../history/obtaining-the-reference.md), and the gate's own violating
input is what will pin the case once task 3.5 lands.
