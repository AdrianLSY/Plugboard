---
type: rule
status: planned
authority: rationale
---

# A test helper never performs the state transition it is written to wait for

<a id="no-helper-repairing-awaited-state"></a>

**Gate:** planned — the no-repair guard of
[rebuild-plugboard task 3.8](../../../openspec/changes/rebuild-plugboard/tasks.md), which fails CI
when a harness or test helper calls a reload, restart, resync, or reconcile entry point from a wait,
poll, or retry path, naming the file and line

A helper waits, observes, and fails. Prohibited: calling the reload, reconcile, restart, or resync
the awaited transition would have performed — on timeout, in a fallback branch, or anywhere inside
the wait — and prohibited equally is discarding that call's return value so the repair is invisible
at the call site.

## Why

This is the showpiece finding of the audit. `pg_notify` inside a trigger is transactional and the
Ecto sandbox never commits (`20251102153313_add_mount_notify_trigger.exs:18`,
`data_case.ex:46`), so the notifier's `handle_info` was never invoked by any test. The tests passed
because on timeout their own wait helper called `MountStore.reload_all()`
(`mount_notifier_test.exs:554-560`, with both tests claiming to prove NOTIFY at `:56` and `:287`
routing through it; `hook_notifier_test.exs:371-376` repeats the pattern and discards the return
value entirely). **947 lines of tests for the cache-invalidation mechanism, and the mechanism had
never run under test** ([the audit](../../history/reference-audit.md)).

A repairing helper is worse than a missing test, because it reports the mechanism as covered. Prove
delivery in the tier where a transaction commits — see [the tiers](test-tiers.md).

Reviewers reject this rather than fixing it; the review-side signature is in
[reviewing](../reviewing.md#ai-generated-pr-review).
