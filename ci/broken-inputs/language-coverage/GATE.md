# Violating input: language-coverage

- **Gate:** `ci/gates/language_coverage.py` (`language_coverage`)
- **Rule note:** `docs/code/rules/language-conventions-keyed-on-source.md`
- **Requirement:** `docs/code-standards` — "Every language with tracked source has stated conventions".

## Violations, one per direction

1. Python source is present (`ci/gates/thing.py`) and `docs/code/languages/python.md` is absent.
2. `docs/code/languages/elixir.md` states conventions for a language with no source in the tree —
   describing a language the repository does not contain.

## Expected

Exit 1, two violations, one per direction.
