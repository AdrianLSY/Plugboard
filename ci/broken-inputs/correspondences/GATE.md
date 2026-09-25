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

**Eleven** violations, exit 1. `rebuild-plugboard` task 1.9 holds `.github/CODEOWNERS` against the
paths `.github/workflows/dependabot-auto-merge.yml` refuses to advance unattended, and asks for one
planted omission of each kind:

1. `person-reviewed-paths` — `CODEOWNERS` names `/codecs/` and the tree holds no such directory. The
   workflow names it too, so the two lists agree about it and only the tree check can fire: that is
   the case where agreement proves nothing.
2. `person-reviewed-paths` — `CODEOWNERS` names `/conformance/` and the exclusion omits it, so an
   unattended patch bump could advance the suite that is the contract's authority. The exclusion
   carries a trailing comment naming `conformance/`: a resolver that read the comment as members
   would heal this omission and publish `#`, `left` and `out` besides.

Then the ways the new resolvers refuse to guess. Each workflow below is its own declared pair against
a manifest list, so the two sides never share a resolver kind and each refusal is the only failure
its pair can produce:

3. `twice-assigned` — the exclusion is assigned in two steps with different members.
4. `unanchored-owner` — a glob owner pattern, which names a set of paths rather than one prefix.
5. `anchored-exclusion` — the exclusion is `"/contract/ /conformance/"`, the CODEOWNERS spelling
   copied across. The workflow tests each word as a prefix of a repo-relative changed path, which
   never begins with `/`, so the list refuses nothing; the slash is refused, not stripped. The refusal
   names exactly the two words, which also shows the quotes were stripped first.
6. `folded-exclusion` — the exclusion is a folded block scalar (`>-`). Only a single-line plain or
   quoted scalar is read; split as raw text, this one read as the single member `>-`.

And five workflows that publish a list without acting on it. The only read recognised is a
`for NAME in ...` word list, in the step that holds the list, with the expansion an unquoted word:

7. `unread-exclusion` — the exclusion is assigned and never expanded.
8. `commented-read` — the only loop over it is in a shell comment; the loop that runs has an empty
   list. The commented-out line puts its loop after `&&`, so only dropping comment lines refuses it.
9. `echoed-read` — it is expanded only by an `echo`, which prints the list and refuses nothing.
10. `other-step-read` — it is on one step's `env:` and the loop is in the next step, where the
    variable is empty: a step's `env:` is visible to that step alone.
11. `reassigned-exclusion` — the step's shell reassigns it before the loop, so the loop acts on that
    value and not on the list reconciled here.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/correspondences.py --root ci/broken-inputs/correspondences/tree` | exit 1, eight violations |
| `python3 ci/gates/correspondences.py --root ci/broken-inputs/correspondences/tree-person-reviewed` | exit 1, eleven violations |
| `python3 ci/gates/correspondences.py` | exit 0: three live correspondences, one retired |

## Not violations here

A side naming no members. It is checked, and planting it would produce a finding about the
declaration rather than about a divergence, which is the next gate's concern and not this case's.
