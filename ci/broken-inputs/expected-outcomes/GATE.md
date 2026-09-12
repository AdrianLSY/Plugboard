# Violating input: expected-outcomes

- **Gate:** `ci/gates/expected_outcomes.py` (`expected_outcomes`)
- **Rule note:** `docs/code/rules/a-red-gate-is-a-recorded-debt.md`
- **Task:** `rebuild-plugboard` task 4.5 — *"add the check that every red entry names one and that the
  named task exists, demonstrated by adding a red entry with no closing task and observing the check
  fail."*

## Violations, one per case

1. `pkg/thing:TestNoCloser` is recorded red and names no closing task. A red gate is a **debt**, and a
   debt with no named creditor is a permanent exemption wearing a temporary one's clothes.
2. `pkg/thing:TestBadCloser` names task `9.9` of a list that holds no such task. The id is resolved
   against **that** list rather than against every task list in the repository: two changes in flight
   carry overlapping identifiers, and an unscoped read clears a marker against the wrong one.
3. `pkg/thing:TestBadOutcome` records `amber`. A run is red or green; anything else is a note somebody
   left in a field a check reads.
4. `pkg/thing:TestNobodyWrote` names a test no source declares. The runner would report nothing about
   it and exit zero — which reads exactly like a clean run, and is the same shape as a suite green
   over an empty subject set.

## The control, in the same registry

`pkg/thing:TestPresent` is red, names a closing task that exists in the list it names, and names a
test that `thing_test.go` declares. It is not reported. A check that failed every row would emit five
violations here, and `expect.json` says four.

## What this gate does not do

Run anything. `ci/expected-outcomes.py` runs the gating tests and compares each outcome to the record;
this gate checks the record itself, and it runs inside `make check` precisely because it starts no
process. A gate that ran a chain of processes would put that chain in the command a contributor runs
on every commit.

## Expected

Exit 1, four violations.
