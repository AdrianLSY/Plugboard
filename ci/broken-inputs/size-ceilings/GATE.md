# Violating input: size-ceilings

- **Gate:** `ci/gates/size_ceilings.py` (`size_ceilings`)
- **Rule note:** `docs/code/rules/module-size-ceiling.md`
- **Task:** `rebuild-plugboard` task 3.5.
- **Also serves:** `docs/code/rules/function-size-ceiling.md`.

## Violations

1. `sidecar/oversized.go` is 327 non-comment lines against a ceiling of 300. Every one of its
   eighty-four helper functions differs from every other, so what is reported is the LENGTH and not a
   repetition — the duplication gate has nothing to find here, deliberately.
2. `TooLong` is 72 non-comment lines against a ceiling of 60, measured per clause.

## The controls

Eighty-four functions in that same file are under the clause ceiling and are not reported, and the
file's comments are not counted toward either number. That second one is the half that matters: a
file counted by raw lines gets padded with comments to move the count, and what the rule asks for is
the file split along whatever made it long.

## What it does not decide

Whether a long function should have been long. A decision table is one expression per row and is
legitimately long. The ceiling is a forcing function on structure, and the remedy is always to split
along a responsibility rather than to raise the number.

## Expected

Exit 1, two violations.
