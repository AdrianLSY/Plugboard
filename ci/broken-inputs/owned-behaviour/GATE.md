# Violating input: owned-behaviour

- **Gate:** `ci/gates/owned_behaviour.py` (`owned_behaviour`)
- **Rule note:** `docs/method/rules/no-owned-behaviour-in-the-spine.md`
- **Requirement:** `docs/knowledge-base` — "Authority precedence is stated and enforced".

## Violations

1. `docs/why/unlinked.md` reproduces the requirement title "Every mutation is recorded in an audit
   trail" and links no owner — the failure names both the note and the owning capability.
2. `docs/why/undeferred.md` reproduces the same title and links the owner, but marks no summary as
   non-normative.

## Control that must NOT fail

`docs/why/fine.md` describes the same subject in its own words without using the requirement's title.
That is paraphrase, which this gate deliberately does not decide — stated in the rule note rather
than left as an implied guarantee.

## Expected

Exit 1, exactly two violations.
