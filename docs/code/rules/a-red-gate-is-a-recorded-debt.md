---
type: rule
status: current
authority: rationale
---

# A gating test written before its subject is recorded red, and the red is a debt

**Gate:** `ci/gates/expected_outcomes.py`

A test written before the code it gates is **red on purpose**, and its outcome is recorded in
[`ci/expected-outcomes.json`](../../../ci/expected-outcomes.json) rather than left to make the build
fail. [`ci/expected-outcomes.py`](../../../ci/expected-outcomes.py) runs each one and fails when its
outcome differs from the record **in either direction**.

Every red entry names the task that closes it, and that task has to exist in the list it names. An
outcome is `red` or `green` and nothing else. An entry names a test some source actually declares.

## Why both directions

Red-where-green-was-recorded is a regression, and every project checks for it. **Green-where-red-was-recorded
is the direction nobody builds a check for, and it is the one that matters here**: the whole value of
a recorded red is that turning green is an event somebody has to acknowledge. Advancing an entry
therefore only passes in the same change that turns the test green; editing the record alone fails.

## Why the red is allowed to stand at all

[The plan's own cost analysis](../../../openspec/changes/rebuild-plugboard/design.md) sorts work by
reversibility, which puts the irreversible schema first and end-to-end signal late: 270 of 727 tasks
land before the streaming spine begins, and 406 before a response body first reaches a client. That
ordering is accepted, and it carries three obligations rather than a hope. The first is that the two
exact-bytes gates are **committed red from the start**, so the gap is visible in CI from the first
week rather than discovered at section 38.

A permanently red test inside an ordinary tier makes every later change unmergeable under branch
protection, and the usual answer — a skip, a tag, a commented-out assertion — is
[exactly what this repository refuses](no-uncertainty-marker-or-skip.md). Recording the red is the
answer that keeps the test running and keeps the debt visible.

## What it does not decide

Whether a recorded outcome is the right one. The runner decides that, by running the test. Nor
whether the named closing task is the one that will actually close it, which no check can know.
