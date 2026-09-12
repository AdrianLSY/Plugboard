# Violating input: review-obligations

Exercises [`ci/gates/review_obligations.py`](../../gates/review_obligations.py), which enforces
[the review obligations are stated in one location and enumerated](../../../docs/code/rules/review-obligations-single-sourced.md).

## Two trees

`tree/` holds the **propagation** failures — an item stated canonically and never carried across.
`tree-structure/` holds the **structural** ones, where nothing is missing from the enumeration but the
relationship between the two artifacts is broken. They are separate because a tree carrying both
would let a fix to either appear to work.

## `tree/` — three violations, exit 1, one per canonical enumeration

1. `CONTRIBUTING.md` cites `change-description question 1` where the canonical note states two.
2. It cites checklist items 2 through 10 and omits **item 1**, where the canonical note states ten.
3. It cites `blocking objection 1` and `blocking objection 2` where the canonical note states three.

One per enumeration rather than three against one, because a gate that resolved only the first
enumeration would pass a fixture whose omissions were all in that one. Each is the same mistake — an
item added to a canonical enumeration and never propagated — and the fixture proves the gate sees it
in every set it claims to cover.

The declared counts are *this fixture's* tree, not the repository's: the gate reads the item numbers
from whichever `docs/code/reviewing.md` it is pointed at, so a cardinal here would say nothing about
the real note.

## Two regressions this tree also locks

The shape of case 2 is deliberate, and so is the fenced sample in the canonical note. Each traps a
soundness defect the gate actually had, and each moves the violation count in a **different**
direction — so `ci/gates/fixture_declarations.py` refuses either regression against the declared
three, without this fixture needing a case that asserts a pass.

| regression | what it was | count becomes |
|---|---|---|
| the citation test reverts to a raw substring | `checklist item 1` is a prefix of `checklist item 10`, so an artifact citing only item 10 read as having cited item 1 | **2** — item 1 falsely satisfied |
| fenced regions stop being masked | a numbered line in a code sample became a phantom item, and the gate demanded a citation for an item no enumeration states | **4** — phantom item 11 |

The second is why a fenced sample sits inside the review-checklist section here. It is not decoration:
without masking, that block alone fails the gate, and the failure arrives through `Report.fail()` — so
the meta gate's neuter test passes and proves nothing about it.

## `tree-structure/` — three violations, exit 1

Its `CONTRIBUTING.md` cites **every** item of every enumeration, so no propagation case fires. What
is wrong is structural — the three ways an artifact can carry the numbers and still break the rule:

1. The canonical note states `### The review checklist` **twice** — a two-item stub under Pull
   requests, then the real three-item list. A first-match search reads the stub as the enumeration and
   passes an artifact citing two items; the gate refuses the repeat instead of choosing between them.
2. Its `CONTRIBUTING.md` names the blocking objections with **no link** to the note that owns them.
   Every other mention links rather than copies, so the link is part of the obligation and not
   decoration.
3. It carries the **text** of blocking objection 1 verbatim rather than citing the number. That is the
   second copy the whole rule exists to prevent, and citing the number correctly does not excuse it.

Case 1 is one of two that were silently wrong: before the gate counted heading occurrences, this exact
tree exited 0. Case 3 is the other — it was attributed to `ci/gates/duplication.py`, whose subjects are
the spine against the specifications, so no root-level artifact was ever among them.

The item copied in case 3 is deliberately long. A short item is a label, and `MIN_COPY_CHARS` lets it
collide by coincidence rather than by copying — `ci/gates/duplication.py` takes the same position for
the same reason.

## Runs

| command | expected |
|---|---|
| `python3 ci/gates/review_obligations.py --root ci/broken-inputs/review-obligations/tree` | exit 1, three violations |
| `python3 ci/gates/review_obligations.py --root ci/broken-inputs/review-obligations/tree-structure` | exit 1, two violations |
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

## `tree-template` — the published template and the block that states it

A third case, merged in from `claude/project-review-openspec-d4c0b1`: the pull-request template is
**stated** in a fenced block in the canonical note and **published** where the forge reads it, and the
two are held byte-identical in both directions. Here somebody added a box to the published copy alone.

The other two trees each carry that block and a matching published copy, so their declared counts are
unchanged and they go on demonstrating exactly what this note says they demonstrate.

The block is read from the **unmasked** note. `mask_fences` blanks every fenced line — which is right
for every other case here and would blank exactly the block this one is about.
