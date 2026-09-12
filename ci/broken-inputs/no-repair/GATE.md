# Violating input: no-repair

- **Gate:** `ci/gates/no_repair.py` (`no_repair`)
- **Rule note:** `docs/code/rules/no-helper-repairing-awaited-state.md`
- **Task:** `rebuild-plugboard` task 3.8.
## Violation

1. `conformance/harness/wait_test.go:14` calls `ReloadAll()` after its wait loop times out, then
   returns `true`. That is the prior attempt's defect written out: its wait helper called
   `MountStore.reload_all()` on timeout and reported success, so 947 lines of tests for a
   cache-invalidation mechanism passed while the mechanism had never run under test.

A helper waits, observes, and **fails**. Repairing the state it was written to observe turns a
failing assertion into a passing one, and nothing downstream can tell the difference.

## What it does not decide

A repair spelled some other way — `recompute()`, or a private helper that reloads without saying so.
The vocabulary is declared in `ci/vault.json` and widening it to every verb would fire on every test.
That residue is checklist item 5 and review's.

## Expected

Exit 1, one violation.
