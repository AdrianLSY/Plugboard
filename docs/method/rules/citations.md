---
type: rule
status: current
authority: rationale
---

# A cited artifact is obtainable

**Gate:** `ci/gates/citations.py`

Every path:line citation resolves to a tracked file or into an artifact declared obtainable with its
revision pinned, and the note stating how to obtain it exists. **The line resolves too**, not only the
path: a citation naming line 402 of a 200-line file is as wrong as one naming a file that is gone, and
until [rebuild-plugboard task 1.4a](../../../openspec/changes/rebuild-plugboard/tasks.md) only one of
those was detected.

A declared artifact that is actually present is checked against its pin rather than trusted at it, and
a mismatch fails. One that is **absent** makes its citations *unverifiable* — counted, printed, and
not reported as resolved. The run still exits zero, because absence is the normal state of gitignored
prior art and failing on it would make the one command this repository tells a reader to run
impossible to pass. The count is the debt:
[obtaining the reference](../../history/obtaining-the-reference.md) records why it stands.

Separately, a spine note carries no normative modal.

## Why

The reason for saying so here rather than in a commit message: the prior art carried 148 KB of prose containing two verifiably false documented claims, and the lesson recorded was that a check whose limits are undocumented gets read as a guarantee.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/citations.py`](../../../ci/gates/citations.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
