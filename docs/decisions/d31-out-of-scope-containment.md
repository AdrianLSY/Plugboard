---
type: decision
status: current
authority: decision
---

# D31 — A declared out-of-scope set may not name its own declarant's tree

**In force.** A path a change declares out of its own scope may not lie inside that change's own
directory. It rules out the arrangement `ci/vault.json` carries today, where `rebuild-plugboard`
declares its own sixteen specifications byte-unchanged and is therefore refused every revision to the
files it owns.

The part worth reading twice is the mechanism, because it is a shape a manifest invites rather than a
lapse anyone would repeat knowingly. Two fields sit side by side and read as one control.
`declared_by` scopes whose declaration this is: the gate reads it for the failure text, and for the
expiry that ends the declaration once every declarant is archived. The byte-unchanged assertion reads
neither — it is unconditional and cannot observe which change is editing. So re-pointing `declared_by`
changes whose name is printed and when the declaration lapses, and changes nothing at all about what
is frozen. A freeze days from expiring became one that ends when the plan does, the manifest recorded
the move as the assertion continuing to mean what it had meant, and every gate stayed green through
it. A field read for a message is not a field read for a decision, and nothing in the file
distinguishes them.

What replaces it is weaker, and saying so is half the decision. Containment swaps *who may not edit*
for *who may not declare*: decidable, which the old property was not, and less than the declaration
was believed to deliver. Retiring the declaration removes the only mechanical control against a
coherence pass quietly revising a specification no task named — the hazard the gate's own docstring
records, and one `/opsx:update` makes real rather than hypothetical, since it reconciles neighbouring
artifacts over glob-expanded spec paths. The gate does not go with the declaration:
[`openspec/specs/docs/knowledge-base/spec.md`](../../openspec/specs/docs/knowledge-base/spec.md)
holds the byte-unchanged requirement and requires the assertion be among those the aggregating target
reports. Whether anything should replace the immutability half — given that the owner of these
specifications has to be able to revise them — is left open here rather than answered by implication.

- **Full entry, with rationale and alternatives:** [register D31](../../openspec/changes/rebuild-plugboard/design.md#d31--a-declared-out-of-scope-set-may-not-name-its-own-declarants-tree)
- **What enforces it:** nothing yet — [an artifact declared out of scope stays byte-unchanged](../method/rules/out-of-scope-byte-unchanged.md) names the gate this invariant joins, and [rebuild-plugboard task 3.16](../../openspec/changes/rebuild-plugboard/tasks.md) installs it
- **Waiting on the declaration it retires:** [follow-ups](../method/follow-ups.md) — three open rows name the declared out-of-scope set as what blocks them

> The register wins where this note and it disagree.
