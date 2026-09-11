---
type: rule
status: planned
authority: rationale
---

# The fast tier stays inside ten seconds, and its latency is treated as a defect class

**Gate:** planned — the fast-tier latency budget check of
[rebuild-plugboard task 2.8](../../../openspec/changes/rebuild-plugboard/tasks.md), which reports
elapsed time and fails above ten seconds

The fast tier's wall-clock ceiling is ten seconds. Exceeding it is a defect in the suite, addressed
by moving the offending test to [its tier](test-tiers.md) or by fixing the architecture that made it
slow — never by raising the ceiling or by deleting coverage.

## Why

This is a correctness control, not a convenience. The completeness critic's conclusion in the audit,
and the most useful sentence in it:

> When feedback is slow, an agent (or a person) writes assertions that are cheap to satisfy rather
> than assertions that are expensive to satisfy.

So suite latency is upstream of test quality rather than parallel to it. The prior attempt's suite
required Postgres for tests of pure functions and serialised 27 of 43 files
(`data_case.ex:46` — `Sandbox.start_owner!(Repo, shared: not tags[:async])`), and what it produced
was a body of tests that pass against a proxy which forwards no `POST` body
([the audit](../../history/reference-audit.md)).

Speed comes from a pure core with a thin database edge. It never comes from
[weakening a property in test configuration](no-property-weakened-in-test-config.md), which is how
the prior attempt bought its speed.
