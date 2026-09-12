# Violating input: linter-config

- **Gate:** `ci/gates/linter_config.py` (`linter_config`)
- **Rule note:** `docs/code/rules/one-linter-config.md`
- **Task:** `rebuild-plugboard` task 2.4 — the terminator shares exactly one linter configuration
  with the sidecar, and a second copy anywhere in the tree fails.

## `tree` — two copies, and a module that points at neither

1. `sidecar/.golangci.yaml` is a second configuration. It is spelled with the other extension on
   purpose: a check that looked only for the exact filename this repository uses would be blind to
   the most likely way a second copy actually arrives.
2. `sidecar/Makefile` names neither `ci/make/go.mk` nor `.golangci.yml`, so the module does not share
   the one configuration even though one exists at the root. One file on disk that a module never
   points at is a copy with extra steps.

## `tree2` — a module with no configuration at all

3. A Go module is present and `.golangci.yml` is absent. Its Makefile *does* reach the shared
   include, so case 2 fires alone and the two cases are shown to be independent. An unconfigured
   module is not lightly configured; it is unlinted, and it reports the same green as a module with
   thirty-nine checks.

The two cases cannot share a tree: one needs two configurations present and the other needs none.

## Expected

`tree`: exit 1, two violations. `tree2`: exit 1, one violation.
