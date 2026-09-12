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
   `6756a07`, so a reader cannot confirm they obtained what was cited. It emits one failure per
   pinned revision, and the declaration names both.
4. `docs/uncited.md` cites `docs/history/obtaining-the-reference.md:900` — a **tracked file in this
   tree** at a line far past its end. A path that resolves is not evidence the line does, and the
   line is the half a reader actually follows.

## Controls that must NOT fail

- A citation into `reference/` resolves, because that artifact IS declared obtainable — and with the
  artifact absent it is counted as *unverifiable* and printed, not as resolved and not as a failure.
- `SHALL` inside a fenced block, inside a code span, and on a blockquote line are all exempt —
  a note explaining this rule has to be able to show the word.

## Cases not exercised here, and why

Two of the gate's cases are about an artifact that is **present**: a checkout whose `HEAD` is not the
pinned revision, and a citation into a subtree that is checked out without that path. `reference/` is
gitignored and absent on every machine this has run on, and committing a clone into this repository to
serve as a fixture is not available. Both are demonstrated instead by building a throwaway checkout at
a different revision, which is what `rebuild-plugboard` task 1.4a asks for:

```
mkdir -p /tmp/ref/reference/Plugboard && git -C /tmp/ref/reference/Plugboard init -q .
# commit anything; its HEAD will not be 6756a07
python3 ci/gates/citations.py --root /tmp/ref    # reference/Plugboard=mismatch, exit 1
```

## Expected

Exit 1. **Five** violations, the first naming the undeclared artifact and the declared set.

Stated as three until `harden-vault-harness` task 2.2 remeasured it, then four. The fourth is the
normative-modal case at `docs/uncited.md:11`: this gate carries two subjects — obtainability and the
prohibition on a normative modal in the spine — and the count was written when the fixture exercised
only the first. The fifth is the cited-line case, added with the check by `rebuild-plugboard` task
1.4a. A stated count that nothing checks drifts the moment a case is added.
