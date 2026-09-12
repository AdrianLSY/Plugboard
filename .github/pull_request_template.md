## What breaks if this is wrong?

## Wire contract impact
- [ ] None
- [ ] Additive (new optional field / reserved frame type now used)
- [ ] **BREAKING** -- requires version bump + capability flag

## Tests
Name the specific wrong implementation each new test would reject.

## Checklist
- [ ] Fast suite passes locally (no Postgres required)
- [ ] Conformance suite passes
- [ ] No new `async: false` without a comment saying why
- [ ] Read against every item of the review checklist (docs/code/reviewing.md#the-review-checklist)
- [ ] No blocking objection stands (docs/code/reviewing.md#blocking-objections)
- [ ] Docs updated, or "docs: n/a" with a reason
