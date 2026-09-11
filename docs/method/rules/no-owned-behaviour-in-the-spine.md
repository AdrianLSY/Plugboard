---
type: rule
status: current
authority: rationale
---

# A spine note never states behaviour a specification owns

**Gate:** `ci/gates/owned_behaviour.py`

Where a note must summarise owned behaviour for orientation, it marks the summary as non-normative
and links the owning specification. Reproducing a specification's requirement title without linking
its owner fails, and so does reproducing one without the deferral.

## Why

Without this, the vault becomes the place a plausible sentence about behaviour lives unchecked. That
is not hypothetical: the prior art carried 148 KB of prose containing two verifiably false documented
claims ([reference audit](../../history/reference-audit.md)), and neither was caught because nothing
distinguished a claim from a guess.

## What no gate decides

**Paraphrase.** A note restating a requirement in its own words, without using its title, is
invisible to this gate, to the normative-modal check in
[citations](citations.md), and to the verbatim-text check in
[one copy of requirement text](one-copy-of-requirement-text.md). That residue is owned by review, by
the deferral every note carrying behaviour states at its head, and by the concept-note ceiling that
makes a long paraphrase not fit.

Naming the residue is the point. A green run is not evidence that no note states owned behaviour, and
a check whose limits go undocumented gets read as a guarantee.
