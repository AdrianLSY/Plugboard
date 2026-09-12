---
type: rule
status: current
authority: rationale
---

# The fast tier stays inside ten seconds, and its latency is treated as a defect class

**Gate:** `ci/gates/test_tiers.py`

Two artifacts, and the split matters. The **ceiling** is enforced by
[`ci/fast-tier.py`](../../../ci/fast-tier.py), which wraps the real run, prints the elapsed time on
every run including a passing one, and exits non-zero above the budget declared in `ci/vault.json`.
The **wiring** is enforced by the gate named above: that the top-level fast-tier target routes through
that tool at all, and that the path it names and the declared one are the same path.

A gate that timed the suite would put the whole suite inside `make check`, which is the command a
contributor runs on every commit — so the ceiling is enforced where the suite already runs, and what
`make check` holds is that nothing quietly removed the wrapper.

The elapsed time is printed on a passing run for the same reason the ceiling exists: a budget nobody
sees until it is breached gives no warning while the suite creeps toward it, and the creep is the part
that changes what gets written.

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
