---
type: decision
status: current
authority: decision
---

# D32 — make check holds every tree property on change, inside a declared budget

**In force.** `make check` is the command run on every commit and repeated by CI, and it decides every
property of the tree on every run, the meta-gate's isolation cross-product included. It carries a
wall-clock budget declared in `ci/vault.json`, printed on every run and failing a run that exceeds it.
Each run also prints the one-minute load average at its start and the CPU time its gates spent,
because a busy machine and a slower tree look the same on a clock, and a breach that started on a
machine loaded to its core count says so first, sending the reader to re-run alone before the remedy
applies. It rules out moving a tree property to the daily schedule to make the command faster while
the cost has another cause.

The part worth reading twice is what the two minutes actually were. Half was one gate running every
other gate a second time: the coverage gate's subject is each gate's own output, and it produced that
output by rerunning them all, the slowest included. Most of the rest was a serial loop over processes
that never depended on one another. Neither was the price of checking anything, and taking both away
brought the run from 126 seconds to 13 on the same machine, with every verdict unchanged. The daily
schedule would have hidden that cost rather than removing it, and taken the property off the local
run and off the required check, so a change that breaks it could merge.

What the budget is for, then, is the part that is structural. The isolation cross-product runs every
per-file gate against every violating tree, so it grows with the product of the two, and concurrency
divides that by a core count without touching the growth. The budget makes the growth visible while it
is still a number, and the register names the remedy for the day it is breached, so that day starts
with a decision already taken rather than an argument.

- **Full entry, with the before and after timings and the alternatives:** [register D32](../../openspec/changes/rebuild-plugboard/design.md#d32--make-check-holds-every-tree-property-on-change-inside-a-declared-budget)
- **What enforces it:** `ci/run-gates.py`, which reads `gate_policy.budget_seconds` from `ci/vault.json` and fails a run over it; [a coverage line is an assertion](../method/rules/coverage-is-an-assertion.md) names the gate whose double run it removed
- **Settled:** [rebuild-plugboard task 3.17](../../openspec/changes/rebuild-plugboard/tasks.md)

> The register wins where this note and it disagree.
