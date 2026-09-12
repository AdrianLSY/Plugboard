---
type: rule
status: current
authority: rationale
---

# Authority precedence

**Gate:** `ci/gates/precedence.py`

Five layers, ranked. This is the only place the order is stated; every other note links here.

```
AUTHORITY PRECEDENCE -- stated here and nowhere else

  1  contract/              machine-checked encoding and vectors      ABSOLUTE
  2  specifications         normative SHALL statements                BEHAVIOUR
  3  decisions in force     the decisions in force, in the register   DECISIONS
  4  spine notes            orientation, rationale, glossary          NEVER states behaviour
  5  generated              indexes, and the code map once it exists  WHERE the code is
```

The division is **why** (layer 4), **what** (layer 2), **where** (layer 5). A layer never overrules
one above it, and where two disagree the higher is right and the lower is a defect to fix.

## What this makes true of every note

A spine note may not state behaviour a specification owns. Where a note must summarise owned
behaviour for orientation, it marks the summary as non-normative and links the owning specification —
and every note describing behaviour says at its head that the owning artifact wins where the two
disagree.

That sentence is a *deferral*, and it is required. It is not a restatement of this order, and the
gate distinguishes the two: restating means reproducing the marker above, not mentioning a layer.

## Why

Without a ranking, the vault becomes the place a plausible sentence about behaviour lives unchecked —
which is precisely how the prior art acquired two false documented claims against 148 KB of prose
([reference audit](../history/reference-audit.md)). Layer 5 is named now rather than later because
once code exists a generated code map becomes a third navigation surface, and deciding its rank in
advance is cheaper than discovering the competition.
