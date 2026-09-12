# Violating input: test-tiers

- **Gate:** `ci/gates/test_tiers.py` (`test_tiers`)
- **Rule note:** `docs/code/rules/test-tiers.md`
- **Also serves:** `docs/code/rules/fast-tier-latency-budget.md`, in the half that is decidable over
  the tree — the wiring, not the elapsed time.
- **Tasks:** `rebuild-plugboard` 2.7 and 2.8.

## Violations, all four cases

1. `ci/make/go.mk` declares `test-fast` and neither `test-integration` nor `test-conformance`. Two
   failures, one per missing target: a tier dropped from one include and not the other is a tier that
   silently does not run in half the components.
2. `Makefile` has a `test-fast` target that routes through no budget tool, so the declared ceiling is
   a number in `ci/vault.json` that nothing passes through.
3. `ci/make/elixir.mk` is declared in `ci/vault.json` and absent, so every component it serves has no
   tiers — or has its own copy of them.
4. `proxy/Makefile` includes none of the declared shared includes, so it carries its own copy of the
   tier targets. Its `test-fast` is a bare `mix test`: no exclusions, so the "fast" tier there runs
   the integration tests too. That is the drift the includes exist to prevent, written out.

## What the gate does not do, and what does it instead

It times nothing. The ten seconds are enforced by `ci/fast-tier.py`, which wraps the real run, prints
elapsed time on every run including a passing one, and exits non-zero above the declared budget.
Demonstrated by planting a fifteen-second sleep in a fast-tier test:

```
python3 ci/fast-tier.py -- make -C sidecar test-fast    # OVER BUDGET by 6.5s, exit 1
```

A gate that ran the suite would put the whole suite inside `make check`, and `make check` is the one
command a contributor runs on every commit.

## Expected

Exit 1, five violations.
