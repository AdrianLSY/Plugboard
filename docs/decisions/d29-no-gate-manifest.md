---
type: decision
status: current
authority: decision
---

# D29 — No gate manifest. The roster is discovered; the INVOCATIONS are reconciled

**In force.** There is no `ci/gates.yml`. A gate is found because its module sits in `ci/gates/`, its
paired violating input because a directory under `ci/broken-inputs/` carries that gate's id, and the
obligation it enforces because the module names the rule note. The one thing a manifest would have
added that nothing else held is the set of CI jobs that invoke the gates, and that is reconciled
against `.github/workflows/` rather than restated. It rules out the enumerating file the plan asked
for.

The part worth carrying to the next manifest anyone proposes is the question each of its fields was
put to: does something already know this answer? Three of the four did, and a hand-maintained copy of
an answer three other things already hold is worse than no copy at all, because a stale entry in it
reads exactly like a correct one. The fourth field knew nothing, and that is where the defect turned
out to be: three of the five workflow files were declared nowhere, so the path filters, branch filters
and `continue-on-error` clauses that can defeat a refusal were read by nothing, and every gate
reported green the whole time.

Read as a refusal of declarations in general this inverts, so it is worth stating the line it is
actually drawn on. A declaration earns its place exactly when the thing declared is owned by a format
this repository does not author: a workflow file's shape belongs to the hosting service, so the
declaration cannot move into it and it cannot move into the declaration. Two encodings are forced,
and the answer for a forced pair is to reconcile it in both directions — a file nobody declared fails
by name, a declaration whose file is gone fails too. That is why `correspondences.declared` holds two
entries and not one per manifest somebody wanted.

- **Full entry, with rationale and alternatives:** [register D29](../../openspec/changes/rebuild-plugboard/design.md#d29--no-gate-manifest-the-roster-is-discovered-the-invocations-are-reconciled)
- **What enforces it:** [one set, one encoding](../method/rules/one-set-one-encoding.md) — `ci/gates/correspondences.py` holds `ci/vault.json`'s `runner.workflows` against `.github/workflows/`, in both directions
- **Settled:** [rebuild-plugboard task 3.1](../../openspec/changes/rebuild-plugboard/tasks.md)

> The register wins where this note and it disagree.
