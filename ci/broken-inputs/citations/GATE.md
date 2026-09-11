# Violating input: citations

- **Gate:** `ci/gates/citations.py` (`citations`)
- **Rule note:** `docs/method/rules/citations.md`
- **Requirement:** `docs/knowledge-base` — "A cited artifact is obtainable", plus the
  enforceable half of "Authority precedence is stated and enforced".

## Violations

1. `docs/uncited.md` cites `elsewhere/thing.ex:42` — an artifact that is neither a tracked
   file nor declared obtainable in `ci/vault.json`. The failure must name the artifact.
2. `docs/uncited.md` uses the normative modal `SHALL` in the spine — a note may not state
   behaviour a specification owns.
3. `docs/history/obtaining-the-reference.md` exists here but omits the pinned revision
   `6756a07`, so a reader cannot confirm they obtained what was cited.

## Controls that must NOT fail

- A citation into `reference/` resolves, because that artifact IS declared obtainable.
- `SHALL` inside a fenced block, inside a code span, and on a blockquote line are all exempt —
  a note explaining this rule has to be able to show the word.

## Expected

Exit 1. **Four** violations, the first naming the undeclared artifact and the declared set.

Stated as three until `harden-vault-harness` task 2.2 remeasured it. The fourth is the
normative-modal case at `docs/uncited.md:11`: this gate carries two subjects — obtainability and the
prohibition on a normative modal in the spine — and the count was written when the fixture exercised
only the first. A stated count that nothing checks drifts the moment a case is added.
