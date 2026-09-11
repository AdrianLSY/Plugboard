---
type: rule
status: current
authority: rationale
---

# Every blocking gate runs without a person's initiative

**Gate:** `ci/gates/runner.py`

A tracked runner configuration exists at the path `ci/vault.json` declares, invokes the aggregating
target on every declared trigger, and carries no path filter, no branch filter, and no clause letting
a non-zero exit pass. The aggregating target itself exits non-zero when any blocking gate does — a
`-` prefix or a `|| true` on its recipe makes every gate advisory again in one character. Whether the
hosting service refuses a merge is a server-side setting nothing here can read, and is out of scope.

## Why

Twenty-five gates were declared blocking and nothing blocked. They ran when somebody chose to type a
command, while [`CLAUDE.md`](../../../CLAUDE.md) described `make check` as *"the one command CI
runs"* and [the rule index](../../rule-index.md) defined a gated rule as one where a check fails the
build today. There was no build.

The cost was paid before the rule existed. A rename sat half-staged in the index for hours — the old
path recorded as added, the replacement untracked, one gate crashing on a path `git ls-files`
reported as tracked — and it survived a completion report and a session boundary. Nothing was wrong
with the gate that would have caught it. Nothing ran it.

The provider is not part of this rule. The requirement is keyed on a declared path, so changing forge
edits one manifest value and the file it names, and no requirement — which is also why the choice
could be made after the specification was fixed rather than before.

The clause names are matched as keys, not as text. The first version of the check grepped for them and
failed on the workflow file that documents them in a comment: the very file it was written to approve.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
