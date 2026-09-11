---
type: essay
status: current
authority: rationale
---

# Documentation rules

Six rules, and one gated consequence. The failure each one answers is tabulated in
[the finding table](harness.md#the-finding-to-constraint-table).

---

## Documentation

The reference had 148 KB of prose against a history of `updated code`, and two documented claims are
verifiably false. The lesson is not "write less" — the prose is where intent was recorded and is the
most valuable thing in the repository. The lesson is **the docs must be falsifiable.**

**Rules:**

1. **Every behavioural claim carries a `file:line` citation or a test name.** A claim with neither is a
   claim nobody can check, and two such claims in the reference were false.
2. **Configuration documentation is generated**, not written. The reference's env-var tables were the
   *reliable* half of its docs precisely because they tracked something mechanical. Generate the
   Dockerfile `ENV` block, `.env.example`, and the config reference from one schema.
3. **Docs bump in the same PR as the behaviour.** Not "afterwards" — the reference's `AGENTS.md` said
   *"After completing any task, review and update README.md, AGENTS.md and CLAUDE.md"*, and it drifted
   anyway, because a rule with no gate is a wish.
4. **The gate:** a PR touching the wire contract, a public API, or a documented behaviour and *not*
   touching docs must say `docs: n/a` with a reason. CI checks for the marker's presence, not its
   correctness — the reviewer checks correctness.
5. **Record deliberate omissions next to the code.** `router.ex:47-49` is the standard: a security
   control dropped, with the reason. That comment is more valuable than the 60 KB README.
6. **`docs/` is for orientation and rationale; the contract is for behaviour.** When they disagree, the
   contract wins and `docs/` is wrong. Say so explicitly at the top of any doc that describes
   behaviour.

---

## One copy of requirement text

Rule 6 has a mechanical consequence: a note **links** to a requirement, it never copies it. A block of
requirement text carried by both a spine note and a specification fails `ci/gates/duplication.py`, and
the failure names both locations so the copy can be deleted in favour of the link.

The gate decides copy-paste and only copy-paste. A paraphrase is invisible to it — which is the
decision-log defect in the form no deterministic check can see — so rule 1's citation-or-test-name and
the `authority` field in every note's frontmatter carry the rest of that weight.

> Orientation, not behaviour. The specifications win.

## Where these rules came from

The rules above predate the vault; what made them checkable was
[the change that restructured the documentation into one](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/proposal.md),
which turned the falsifiability convention into a gate rather than a hope. Its normative half is
[`docs/knowledge-base`](../../openspec/specs/docs/knowledge-base/spec.md).
Where this note and that specification disagree, the specification wins.

What that change did not do was arrange for any of it to run.
[The change that wires the gates to a runner](../../openspec/changes/archive/2026-09-12-harden-vault-harness/proposal.md)
records the gap and the five requirements that close it: on a tree where twenty-one gates are declared
blocking, no tracked configuration executes them, so "a rule with no gate is a wish" had a second half
nobody had written down — a gate no runner invokes is a wish with a Python file attached.
