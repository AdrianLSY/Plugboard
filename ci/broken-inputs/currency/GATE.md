# Violating input: currency

- **Gate:** `ci/gates/currency.py` (`currency`)
- **Rule note:** `docs/method/rules/currency-both-directions.md`
- **Requirement:** `docs/knowledge-base` — "The documentation reflects the current state".

## Violations, one per property

1. `docs/superseded-no-replacement.md` is marked superseded and names no replacement.
2. `docs/planned-no-work.md` is marked planned and links no work that builds it.
3. `docs/planned-subject-exists.md` is marked planned and its named subject
   (`docs/method/`) is present in the tree — the marker should have been retired.
4. `docs/planned-task-done.md` is marked planned and names task 1.1, whose checkbox is
   ticked in the task list it links.

Properties 3 and 4 are the direction an adversarial review found missing: without them the
whole spine stays marked planned once its subjects arrive, with the gate green.

## Expected

Exit 1, four violations.
