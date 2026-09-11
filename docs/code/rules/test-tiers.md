---
type: rule
status: planned
authority: rationale
---

# Every test runs in one of three declared tiers

**Gate:** planned — the separately invocable tier targets of
[rebuild-plugboard task 2.7](../../../openspec/changes/rebuild-plugboard/tasks.md), whose fast-tier
CI job runs with no Postgres service and no network so a misplaced test fails rather than skips

```
  FAST         no Postgres, no network, no sleeps, fully async. What runs on save.
               Pure functions, changesets, framing, parsing, routing logic.
               Its latency budget is a rule of its own -- see below.

  INTEGRATION  real Postgres, real sockets, committing transactions.
               Notifier delivery lives here, because pg_notify is transactional
               and a test sandbox never commits.

  CONFORMANCE  the wire contract, run against every implementation. The authority.
               Adversarial fixtures, not happy paths.
```

A test belongs to the tier its subject requires, not the tier that is convenient. The tiers are
separately invocable, and a fast-tier test that reaches for a database or a socket is a failure of
the tier rather than a skipped case.

## Why

The prior attempt's split was not by subsystem but by whether the subject was synchronous: 27 of 43
files ran `async: false` (`data_case.ex:46` —
`Sandbox.start_owner!(Repo, shared: not tags[:async])`) and pure-function tests required Postgres
([the audit](../../history/reference-audit.md)). Its 947 lines of notifier tests sat in the tier
that cannot observe a commit, so the mechanism they were written for never ran — the concrete case
is [a helper that repairs awaited state](no-helper-repairing-awaited-state.md).

Tiers are also what makes the fast suite cheap enough to run on save, which is the precondition for
[the latency budget](fast-tier-latency-budget.md) being a correctness control rather than a target.

Orientation, the adversarial fixture list, and mutation thinking as the review standard are in
[testing](../testing.md).
