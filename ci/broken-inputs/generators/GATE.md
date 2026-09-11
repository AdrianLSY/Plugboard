# Violating input: generators

Exercises [`ci/gates/generators.py`](../../gates/generators.py), which enforces
[a generated artifact is verified against something other than its generator](../../../docs/method/rules/generators-have-an-oracle.md).

## Violations

**Three** violations, exit 1:

1. `ci/gen/indexes.py` writes output that differs from its pinned expectation.
2. `ci/gen/stowaway.py` is a tool under `ci/gen/` that the declaration does not name.
3. `ci/gen/rule_index.py` states nothing about the class of wrongness its input does not reach.

`ci/gen/conventions.py` conforms, so the fixture is not uniformly broken and the gate is shown
distinguishing a passing generator from a failing one in the same run.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/generators.py --root ci/broken-inputs/generators/tree` | exit 1, three violations |
| `python3 ci/gates/generators.py` | exit 0 over the three real generators |

## Not violations here

A generator whose *declared expectation* is absent, and a declared tool that does not exist. Both are
checked and neither is planted, because the fixture would then fail before reaching the comparison
that is this gate's subject.
