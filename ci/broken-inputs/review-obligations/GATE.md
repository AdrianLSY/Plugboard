# Violating input: review-obligations

Exercises [`ci/gates/review_obligations.py`](../../gates/review_obligations.py), which enforces
[the review obligations are stated in one location and enumerated](../../../docs/code/rules/review-obligations-single-sourced.md).

## Violations

**Three** violations, exit 1 — one per canonical enumeration.

1. `CONTRIBUTING.md` cites `change-description question 1` where the canonical note states two.
2. It cites `checklist item 1` and `checklist item 2` where the canonical note states three.
3. It cites `blocking objection 1` and `blocking objection 2` where the canonical note states three.

One per enumeration rather than three against one, because a gate that resolved only the first
enumeration would pass a fixture whose omissions were all in that one. Each is the same mistake — an
item added to a canonical enumeration and never propagated — and the fixture proves the gate sees it
in every set it claims to cover.

The declared counts are *this fixture's* tree, not the repository's: the gate reads the item numbers
from whichever `docs/code/reviewing.md` it is pointed at, so a cardinal here would say nothing about
the real note.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/review_obligations.py --root ci/broken-inputs/review-obligations/tree` | exit 1, three violations |
| `python3 ci/gates/review_obligations.py` | exit 0 against the declared canonical note and `CONTRIBUTING.md` |

## Not violations here

**An absent canonical note**, and **an absent obliged artifact.** Both are checked and both would
stop the run before it reached the propagation cases this fixture is for — an absent canonical note
returns immediately, and an absent obliged artifact suppresses every per-item comparison against it.
They are separate trees' work if either is ever worth demonstrating.

**A label that misreads its item.** The tables in the real `CONTRIBUTING.md` put a short handle beside
each number, and nothing checks that handle against the canonical wording. That is deliberate and is
stated in the gate's own docstring: the rule is about location rather than wording, because one copy
and a link has no drift to detect. A fixture asserting otherwise would demonstrate a rule this
repository did not adopt.
