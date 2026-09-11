# Violating input: fixture-declarations

Exercises [`ci/gates/fixture_declarations.py`](../../gates/fixture_declarations.py), which enforces
[a violating input states the failure it produces](../../../docs/method/rules/fixtures-declare-their-failure.md).

Four nested fixtures, each with its own gate emitting two known violations.

## Violations

**Four** violations, exit 1:

1. `nodecl/` has a violating tree and no `expect.json`.
2. `wrongcount/` declares five violations where its gate emits two.
3. `deadcase/` declares a case its gate no longer emits.
4. `badflag/GATE.md` demonstrates a flag its gate accepts that the declaration never exercises.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/fixture_declarations.py --root ci/broken-inputs/fixture-declarations/tree` | exit 1, four violations |
| `python3 ci/gates/fixture_declarations.py` | exit 0 over the real fixture set |

## Not violations here

An invocation declaring a violation count instead of an exit status, and an invocation whose exit
differs from the one declared. Both are checked; neither is planted, because the four above already
cover one case per clause and a fifth would only lengthen the run.
