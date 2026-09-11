# Violating input: runner

Exercises [`ci/gates/runner.py`](../../gates/runner.py), which enforces
[every blocking gate runs without a person's initiative](../../../docs/method/rules/the-gates-actually-run.md).

## Violations

**Five** violations, exit 1:

1. The workflow carries `branches:` — a branch filter.
2. The workflow carries `continue-on-error:` — a non-zero exit that does not fail the job.
3. The workflow triggers on `push` only, missing `pull_request`.
4. The `check` recipe begins with `-`, so make ignores its exit status.
5. The same recipe ends with `|| true`.

Cases 4 and 5 are separate because they are separate mistakes with one effect, and a fixture that
merged them would let either fix alone appear to work.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/runner.py --root ci/broken-inputs/runner/tree` | exit 1, five violations |
| `python3 ci/gates/runner.py` | exit 0 against the declared runner |

## Not violations here

An absent configuration. It is checked, and planting it would stop the run before reaching the four
clause cases, which are this fixture's subject.
