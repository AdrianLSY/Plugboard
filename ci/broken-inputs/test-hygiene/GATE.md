# Violating input: test-hygiene

- **Gate:** `ci/gates/test_hygiene.py` (`test_hygiene`)
- **Rule note:** `docs/code/rules/no-uncertainty-marker-or-skip.md`
- **Task:** `rebuild-plugboard` task 3.9.
## Violations, one per case

1. `async: false` with no stated reason. Serial is sometimes right; unexplained serial is how 27 of
   43 files came to be serial, which is what made the suite slow enough that assertions got chosen
   for being cheap to satisfy.
2. `@tag :skip` with no linked issue. A skip is a deferred assertion, and one with no creditor is a
   deleted assertion wearing a temporary marker. The prior attempt skipped its only mount-point hook
   success test claiming another file covered it; it did not.
3. An uncertainty marker in the test body — *"actually this shouldn't matter, the other file covers
   it"*. Abandoned reasoning committed as a comment is the audit's signature for a test written
   around a defect rather than at it.

All three are in one file, which is realistic: they arrive together.

## What it does not decide

Whether a stated reason is a good one, or whether a linked issue is real. Both are review's. It
decides that the question was answered somewhere a reader can find it.

## Expected

Exit 1, three violations.
