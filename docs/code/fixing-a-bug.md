---
type: procedure
status: planned
authority: rationale
---

# Fixing a bug, starting from a case that fails

**Gate:** planned — the absent-artifact check that keeps this procedure honest now runs, and step 1
is already enforced for the vault's own gates by
[every gate is demonstrated to fail](../method/rules/gates-are-demonstrated-to-fail.md). What is
still unenforced is the procedure's own ordering, which needs
[rebuild-plugboard task 1.10](../../openspec/changes/rebuild-plugboard/tasks.md).

Three steps, the first of which is the whole procedure: **the failing case is committed and observed
failing before the fix exists.** A fix arriving with its test proves only that the test runs.

## 1. Demonstrate the failure, and say what the case discriminates

Add the case, run it, and read its failure: the message names the defect rather than a bare
mismatch, so a contributor who trips it later reads the bug from the output. For a defect in this
repository's own gates that demonstration exists today — the case is a deliberately violating input
under `ci/broken-inputs/<gate>/`, whose `GATE.md` names the gate it exercises and the rule note that
gate enforces, and `make check-gates` runs it; a gate passing on its own violating input fails the
build. For a component defect it is a conformance fixture where the wire contract broke, and a test
in the owning component otherwise — both in directories that are planned, below.

Then the change description names the wrong implementation this case rejects, judged against
[mutation thinking](testing.md#mutation-thinking-as-the-review-standard). "It reproduces the bug" is
not an answer; "it fails against any implementation that reads the body before forwarding it" is.

## 2. Fix it, and change nothing else

The smallest change in the component that owns the behaviour; a refactor alongside hides the edit.

## 3. Re-run, and update what travels with the change

The case passes and nothing else changed its result. Then the notes: a defect that existed because a
note was wrong corrects that note in the same change, or the change says `docs: n/a` with a reason —
[as in step 4 of adding a feature](adding-a-feature.md#4-update-what-travels-with-the-change).

## Two shapes this procedure refuses

Each is its own rule note, citable from [the blocking objections](reviewing.md#blocking-objections)
— as is this note, which the refusal of a fix with no prior failing case names:

- [A test helper never performs the state transition it is written to wait for](rules/no-helper-repairing-awaited-state.md#no-helper-repairing-awaited-state)
  — a helper waits, observes, and fails.
- [A test asserts the intended behaviour, never the defective behaviour it found](rules/no-test-accommodating-a-defect.md#no-test-accommodating-a-defect)
  — a test shaped around a bug, usually with a comment explaining why it avoids the obvious case, is
  a defect nothing will ever fail on. It opens an issue instead, and its review-side signature is in
  [AI-generated PR review](reviewing.md#ai-generated-pr-review).

**This procedure's own verification** — a contributor followed it when all four hold:

- The case exists in a commit that does not contain the fix, and failed in that commit.
- The change description names the wrong implementation the case rejects.
- `make check` exits zero, and `make check-gates` too if the defect was in a gate.
- Neither refused shape above appears in the change.

## Named here, not yet provided

| named | provided by | what stands in today |
|---|---|---|
| a runnable `conformance/` suite | [rebuild-plugboard task 2.6](../../openspec/changes/rebuild-plugboard/tasks.md) | `ci/broken-inputs/` with `make check-gates`, for gate defects. The component directories arrived with task 1.1 and hold no source yet |
| the per-component test targets | [rebuild-plugboard task 1.7](../../openspec/changes/rebuild-plugboard/tasks.md) | `make check` |

## Why

The previous attempt's wait helper called `MountStore.reload_all()` on timeout and reported success,
so 947 lines of tests for a cache-invalidation mechanism passed while the mechanism had never run
under test: `mount_notifier_test.exs:554-560` is the fallback, and both tests claiming to prove
`NOTIFY` route through it. Three others were written around defects rather than at them —
`hooks_test.exs:425` carries abandoned reasoning as committed comments, and `executor_test.exs:465`
skips the only mount-point hook success test behind a false coverage claim. All four are in
[the audit](../history/reference-audit.md), the constraints in
[the finding table](../method/harness.md#the-finding-to-constraint-table).

> Orientation, not behaviour. The specifications win.
