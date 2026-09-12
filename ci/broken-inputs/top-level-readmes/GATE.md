# Violating input: top-level-readmes

- **Gate:** `ci/gates/top_level_readmes.py` (`top_level_readmes`)
- **Rule note:** `docs/code/rules/top-level-directory-carries-a-readme.md`
- **Requirement:** `docs/code-standards` — "A component's boundary is stated once".

## Violations

1. `proxy/` holds a tracked file and no `README.md`, so nothing at the root of the tree says what the
   directory is or routes a reader to the note that owns its boundary.

## The negative control, in the same tree

`sidecar/` holds a file *and* a README. It is here so the tree proves the gate discriminates: a gate
that failed on every top-level directory would emit two violations against this fixture, and the
declaration in `expect.json` says one.

## The second case, and why it is not here

The gate also fails an exemption in `ci/vault.json` whose directory holds no tracked file — a
declaration outliving its subject. That case reads the real manifest and is scoped to the repository
by `on_tracked_tree`, exactly as `component_boundaries`, `index_drift` and `out_of_scope` each scope
their own repository-wide checks. Against a deliberately partial tree it would fire once per exempt
directory absent from the fixture and demonstrate nothing, so it is not exercised here. Stated rather
than omitted: a fixture that does not say which case it leaves uncovered converts an unexamined case
into an apparently examined one.

## Expected

Exit 1, one violation.
