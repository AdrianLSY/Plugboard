# Violating input: entry-points

- **Gate:** `ci/gates/entry_points.py` (`entry_points`)
- **Rule note:** `docs/method/rules/entry-files-route.md`
- **Requirement:** `docs/knowledge-base` — "Entry points route rather than carry content".

## Violations

1. `CLAUDE.md` names `docs/graphify-out/wiki/index.md`-style absent artifacts — here,
   `docs/nowhere/index.md` — which is the real defect this check was written for: the actual
   `CLAUDE.md` instructed every agent to query a knowledge graph that has never been generated.
2. `CLAUDE.md` carries a framework-conventions heading; a framework tutorial is not context.
3. `CLAUDE.md` names no banned pattern.
4. `AGENTS.md` is declared and absent.

## Expected

Exit 1, four violations. The real tree passes at 2,865 and 2,284 bytes against a 4,096 ceiling.
