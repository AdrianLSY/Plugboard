---
type: rule
status: planned
authority: rationale
---

# A test asserts the intended behaviour, never the defective behaviour it found

<a id="no-test-accommodating-a-defect"></a>

**Gate:** planned — the fixture-to-requirement coverage gate of rebuild-plugboard task 12.15, where
a case counts as proven only once it rejects a paired defective counterpart from the catalogue of
[task 15.8](../../../openspec/changes/rebuild-plugboard/tasks.md), so a test shaped around a defect
is reported as referencing its requirement rather than proving it

Prohibited: asserting what the code currently does when that differs from what it is supposed to do,
avoiding the obvious case because it fails, and recording the reason in a comment. A defect found
while writing a test opens an issue or is fixed; it is never encoded as the expectation.

## Why

Three tests in the prior attempt were written around defects rather than at them, each explaining in
a comment why it dodged the obvious case: `hooks_test.exs:425` ("Let's just test that changing
target_type works"), `hooks_test.exs:538` (choosing non-overlapping values because the
implementation updates one-by-one), and `executor_test.exs:465`
([the audit](../../history/reference-audit.md)). Transitive cycle detection had no test at all, and
the one cycle test is satisfied at depth 1 (`hooks.ex:261`) before the recursive branch at `:265` is
reached.

A defect a test has been shaped around is a defect nothing will ever fail on: the suite now reports
the bug as intended behaviour, and the next person to fix it breaks a test. That is how the prior
attempt's defects survived 27,000 lines of tests.

The review probe is mutation thinking — name the one-line wrong implementation this test would not
catch ([testing](../testing.md#mutation-thinking-as-the-review-standard)); a test shaped around a
defect cannot answer it.
