---
type: decision
status: current
authority: decision
---

# D31 — A declared out-of-scope set may not name its own declarant's tree

**In force.** A path a change declares out of its own scope may not lie inside that change's own
directory. It rules out the arrangement `ci/vault.json` carried until `rebuild-plugboard` task 3.16,
where `rebuild-plugboard` declared its own sixteen specifications byte-unchanged and was therefore
refused every revision to the files it owns. That task emptied the declaration and recorded the
emptiness, with its reason and ending, as a declared vacuity.

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
- **What enforces it:** `ci/gates/out_of_scope.py`, since [rebuild-plugboard task 3.16](../../openspec/changes/rebuild-plugboard/tasks.md) — [a declared out-of-scope path lies outside its declarant's tree](../method/rules/out-of-scope-containment.md) is the rule, and this decision is its owner
- **Unblocked by the retirement:** [follow-ups](../method/follow-ups.md) — two open rows had named the declared out-of-scope set as what blocked them, and now name the specification revision itself

> The register wins where this note and it disagree.
