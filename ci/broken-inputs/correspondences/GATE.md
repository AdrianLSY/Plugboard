# Violating input: correspondences

Exercises [`ci/gates/correspondences.py`](../../gates/correspondences.py), which enforces
[a published enumeration and the computed one are reconciled](../../../docs/method/rules/one-set-one-encoding.md).

The tree carries its own `ci/vault.json`, because this gate's subject *is* the declaration.

## Violations

**Eight** violations, exit 1, across five cases:

1. `diverging` — a member on each side the other lacks, so both directions fire (two violations).
2. `empty-side` — one side resolves to nothing, and its emptiness then makes every published member
   read as missing (three violations; the emptiness is named separately from its consequences).
3. `broken-resolver` — a resolver that raises. Reported as a failure, so one broken side does not
   take the run with it.
4. `collapsed` — both sides declare one resolver kind, which is no longer a pair.
5. `undocumented` — a retired correspondence recording no cause.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/correspondences.py --root ci/broken-inputs/correspondences/tree` | exit 1, eight violations |
| `python3 ci/gates/correspondences.py` | exit 0: one live correspondence, one retired |

## Not violations here

A side naming no members. It is checked, and planting it would produce a finding about the
declaration rather than about a divergence, which is the next gate's concern and not this case's.
