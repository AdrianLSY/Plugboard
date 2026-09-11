# Violating input: decision-register

- **Gate:** `ci/gates/decision_register.py` (`decision_register`)
- **Rule note:** `docs/method/rules/decision-register.md`
- **Requirement:** `docs/knowledge-base` — "There is exactly one decision register".

## Violations

1. `docs/second-register.md` assigns `D1` and `D2` — unnamespaced identifiers outside the
   declared register, i.e. a second register. This is the defect the requirement exists to
   prevent, and the one the consolidating change committed in the act of repairing it.
2. `openspec/changes/rebuild-plugboard/design.md` assigns `D13`, a retired identifier.

## Controls that must NOT fail

- `docs/namespaced.md` assigns `RDV1`/`RDV2` — a change's own namespaced decisions are not a register.
- The same file cites `D16`, `D20`, `D24` and `D9` in prose, backticks and a table cell. Assignment
  is a heading; a citation is not an assignment. Without this distinction the collision table, which
  must name all fifteen superseded identifiers, would itself be unwritable.
- `docs/decisions/superseded-register.md` exists, so the collision-table check passes.

## Expected

Exit 1 with exactly three violations — two assignments outside the register, one retired reuse —
the retired one naming what `D13` used to denote.
