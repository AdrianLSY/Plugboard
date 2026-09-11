---
type: rule
status: current
authority: rationale
---

# A gate's docstring opens with the requirement it enforces and the defect behind it

**Gate:** none — preference, not obligation

A gate module's docstring names, in its first lines, the capability and requirement it enforces and
the concrete defect that motivated the check. Nothing verifies this, and it may not be raised as a
blocking objection: a review comment asking for it is a suggestion the author is free to decline.

## Why

Every gate in the tree happens to do it, which is the only evidence that the habit is real rather
than aspirational. The meta-check opens with its requirement and then with the flag defect that
produced it — `mix precommit` running `compile --warning-as-errors` while CI ran the plural spelling,
so the guardrail never guarded anything ([`ci/gates/meta.py:11`](../../../../ci/gates/meta.py), and
`unit_test.yml:69` in [the reference audit](../../../history/reference-audit.md)). Reading that
docstring tells you why the check exists before you argue with it.

What the habit buys is small and real: the contributor who trips a check reads the module, and a
docstring that starts with the defect turns a verdict into an explanation. What it cannot buy is
enforcement. "Names the requirement it enforces" is not decidable over English — a docstring can name
a requirement that does not exist, or paraphrase one into something else — and the nearest decidable
proxy, *a gate declares a rule note*, is already a gated obligation elsewhere
([every rule names its gate](../rule-gate-correspondence.md)). Writing a second check that
approximated the prose part would produce a gate whose green run means less than its own message
claims.

So it lives here, unenforced, counted in [the rule index](../../../rule-index.md) as one of the
preferences — visible as taste rather than dressed as a requirement.
