# Violating input: review-obligations

- **Gate:** `ci/gates/review_obligations.py` (`review_obligations`)
- **Rule note:** `docs/code/rules/review-obligations-single-sourced.md`
- **Requirement:** `docs/code-standards` — "The review obligations are stated in one location and
  enumerated".

## Violations, two of the gate's three cases

1. `CONTRIBUTING.md` does not name *The review checklist* item 2. The enumerator has fallen behind the
   canonical list — the propagation defect, and the only one of the three that a real repository
   produces by accident.
2. `CONTRIBUTING.md` does not name *The change-description questions* item 1. Same case, second
   enumeration, so the gate is shown to iterate the declared set rather than one list.
3. `docs/code/reviewing.md` carries no *Blocking objections* heading. `ci/vault.json` declares it a
   canonical enumeration, so either the note was reorganised and the check quietly stopped covering
   it, or the declaration is stale. Either way the answer is a failure, not silence.

## The third case, and why it is not here

The gate also fails a declared enumerator that does not exist. Demonstrating it needs the fixture to
omit `CONTRIBUTING.md`, and the tree would then have nothing for cases 1 and 2 to fire against —
one scenario cannot hold both. Stated rather than omitted.

## The negative control, in the same tree

*The review checklist* item 1 **is** named by the enumerator, and the gate stays silent about it. A
check that reported every item as missing would emit four violations here, and the declaration in
`expect.json` says three.

## Expected

Exit 1, three violations.
