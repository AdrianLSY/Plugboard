# Violating input: coverage

Exercises [`ci/gates/coverage.py`](../../gates/coverage.py), which enforces
[a gate's reported coverage is an assertion about the run](../../../docs/method/rules/coverage-is-an-assertion.md).

Four gate-shaped modules, one per case the rule states.

## Violations

**Four** violations, exit 1 — one per module:

1. `ci/gates/silent.py` prints no coverage line at all.
2. `ci/gates/borrowed_source.py` claims the tracked index on a tree that is not a work tree.
3. `ci/gates/understated.py` reports one subject while its failures name three.
4. `ci/gates/undeclared_empty.py` reports zero subjects with no declaration recording why.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/coverage.py --root ci/broken-inputs/coverage/tree` | exit 1, four violations |
| `python3 ci/gates/coverage.py` | exit 0 over the real gate roster |

## Not violations here

A gate reporting zero subjects *with* a declaration naming its reason and the work that ends it —
`component-boundaries` is exactly that today, and it passes. The case this fixture holds is the
undeclared one, because an exemption nobody recorded is indistinguishable from a check that quietly
stopped checking.
