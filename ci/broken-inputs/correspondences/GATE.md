# Violating input: correspondences

Exercises [`ci/gates/correspondences.py`](../../gates/correspondences.py), which enforces
[a published enumeration and the computed one are reconciled](../../../docs/method/rules/one-set-one-encoding.md).

The tree carries its own `ci/vault.json`, because this gate's subject *is* the declaration.

## Violations, in `tree`

**Eight** violations, exit 1, across five cases:

1. `diverging` — a member on each side the other lacks, so both directions fire (two violations).
2. `empty-side` — one side resolves to nothing, and its emptiness then makes every published member
   read as missing (three violations; the emptiness is named separately from its consequences).
3. `broken-resolver` — a resolver that raises. Reported as a failure, so one broken side does not
   take the run with it.
4. `collapsed` — both sides declare one resolver kind, which is no longer a pair.
5. `undocumented` — a retired correspondence recording no cause.

## The person-reviewed paths, in `tree-person-reviewed`

**Five** violations, exit 1. `rebuild-plugboard` task 1.9 holds `.github/CODEOWNERS` against the
paths `.github/workflows/dependabot-auto-merge.yml` refuses to advance unattended, and asks for one
planted omission of each kind:

1. `person-reviewed-paths` — `CODEOWNERS` names `/codecs/` and the tree holds no such directory. The
   workflow names it too, so the two lists agree about it and only the tree check can fire: that is
   the case where agreement proves nothing.
2. `person-reviewed-paths` — `CODEOWNERS` names `/conformance/` and the exclusion omits it, so an
   unattended patch bump could advance the suite that is the contract's authority.

And the three ways the new resolvers refuse to guess:

3. `twice-assigned` — the exclusion is assigned in two steps with different members.
4. `unanchored-owner` — a glob owner pattern, which names a set of paths rather than one prefix.
5. `unread-exclusion` — the exclusion is assigned and no executed line expands it, so the workflow
   publishes a list and acts on none of it.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/correspondences.py --root ci/broken-inputs/correspondences/tree` | exit 1, eight violations |
| `python3 ci/gates/correspondences.py --root ci/broken-inputs/correspondences/tree-person-reviewed` | exit 1, five violations |
| `python3 ci/gates/correspondences.py` | exit 0: three live correspondences, one retired |

## Not violations here

A side naming no members. It is checked, and planting it would produce a finding about the
declaration rather than about a divergence, which is the next gate's concern and not this case's.
