---
type: rule
status: current
authority: rationale
---

# A failure message is a sentence naming the consequence, not a code

**Gate:** none — preference, not obligation

A gate's failure line reads as a sentence: the offending location, then what goes wrong because of
it. Not an identifier a reader has to look up, and not a bare verdict. Nothing checks this, and it
may not be raised as a blocking objection.

## Why

The evidence for it is in this repository's own gate modules rather than in the prior art, and that
is worth stating plainly: **no citation in [the reference audit](../../../history/reference-audit.md)
or [carry-forward](../../../history/carry-forward.md) records a defect caused by the wording of a
human-facing failure message.** What the audit does record is the adjacent defect — a message that
withholds the cause. The reference's documentation cited source paths that had been renamed, and a
checker reporting every one of them as "broken link" gave no way to tell a renamed file from a renamed
heading, so the whole list was re-verified by hand on every pass. That account is in
[`ci/gates/links.py:25`](../../../../ci/gates/links.py), which is why that gate reports a missing
anchor and a missing file as different findings.

Two shapes follow from it, and both are visible across the modules. A failure names the consequence,
not the rule number: a gate naming no rule note is refused because *a gate whose rule nobody can find
becomes folklore the next contributor deletes*
([`ci/gates/rule_gate_correspondence.py:88-90`](../../../../ci/gates/rule_gate_correspondence.py)). And
a failure hands over the command that fixes it — the index gates print the regeneration line rather
than the word `drift`.

## The deliberate inverse, so this is not read as a general rule

On the wire the preference is the opposite. A tunnel error is a typed code a client can branch on
(`types.go:63-76` carried forward as the vocabulary to keep), and rendering a term instead is a
blocking objection — the reference's refresh-token path shipped `inspect(reason)`
(`telephone_channel.ex:106`), which no client could match on. The distinction is the audience: a
sentence for the person reading a failing build, a code for the program handling a frame. Both
citations are in [carry-forward](../../../history/carry-forward.md).

## Why it stays unenforced

"Reads as a sentence" is not decidable, and the plausible proxies are worse than nothing — a minimum
length is satisfied by padding, and a check for a verb passes on a fluent message that names no
consequence at all. The property that *is* gated is the one that matters most: every failure output
names its rule note, so a message that teaches badly still hands over the note that teaches
([every rule names its gate](../rule-gate-correspondence.md)).
