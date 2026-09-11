---
type: moc
status: current
authority: none
---

# Follow-ups

The destination for work this repository has deliberately deferred. Two changes have required a
record like this and neither provided one: `restructure-docs-as-vault` task 9.0 obliges every refused
specification revision to be "recorded as follow-up work naming the artifact and the proposed
revision", and `harden-vault-harness` defers a fixture set on a named trigger
([its design](../../openspec/changes/harden-vault-harness/design.md), `HVH8`). Before this note, both
obligations pointed nowhere — `git ls-files` matched no file for either.

An entry names four things: what was deferred, where the obligation came from, why it was not done,
and the work or event that ends it. An entry with no ending condition is a wish, and this page is not
for wishes.

## Open

| deferred | origin | why not now | what ends it |
|---|---|---|---|
| A conforming-input fixture tree per prose-shape gate — a deliberately *valid* input each gate is proven to pass | `harden-vault-harness` design, `HVH8` | The two existing negative controls cover the shapes the vault contains today; what they miss is gate logic that only runs on a shape the vault does not yet have | `rebuild-plugboard` [task 1.1](../../openspec/changes/rebuild-plugboard/tasks.md) creates the five component directories, at which point `component-boundaries` goes from 0 subjects to 5 and `language-coverage` from one language to three |
| `ci/gates/_common.py` has no gate of its own, and narrowing one predicate in it collapses twelve gates' subject sets while they all report `[ok]` | `harden-vault-harness` design, Risks | No cheap check closes it, and an expensive one built to look thorough is padding | **Partly closed:** it is now [checklist item 9](../code/reviewing.md), so a reviewer is handed the obligation. What is still open is a *check*: it becomes possible if `ci/gates/meta.py` gains a way to observe the shared library rather than the modules, since a fixture tree takes the other branch of `tracked_markdown` and a break confined to the work-tree branch is invisible to it |
| `auth/sidecar-credentials` names no cross-capability reference in 877 lines, though it is plainly coupled to key custody | [threat model](../how/threat-model.md) | The sixteen specifications are a declared out-of-scope set and cannot be edited from either change that found this | A `rebuild-plugboard` change that revises that specification; until then the gap is recorded, not owned |
| No specification names CORS or `Access-Control-Expose-Headers`, though RFC 9725 §4.2 makes honouring CORS the difference between a browser WHIP client that can read `Location` and one that cannot | [scope refusals](../why/scope-refusals.md) | Same declared out-of-scope set | A `rebuild-plugboard` change that assigns the owner, or an explicit refusal recorded there |
| Generalising the one-register rule from the decision sequence to an arbitrary declared identifier family | `harden-vault-harness` proposal, Non-goals | Drafted, prototyped against the tracked tree, and cut: 483 findings and zero true positives, because a tokenizer loose enough to see a new family also sees `SHA`, `IPv` and `PBKDF`, and the count swings between 0, 104 and 461 on the tokenizer choice alone. It also dropped five clauses the in-force rule carries, a measured regression | A second identifier family actually existing. The narrow half landed: `ci/gates/decision_register.py` reads its prefix from `ci/vault.json` rather than hardcoding it, so the generalisation is a declaration away rather than a rewrite |
| Merging `spec/expectations-terminator-dispatch` — 14 requirements and 53 scenarios revising three of the sixteen specifications | Found as uncommitted work in the main checkout, existing on no branch and in no stash | The declared out-of-scope set asserts those files byte-unchanged against a pinned baseline, so the revision and the vault work cannot both land without a deliberate step | Re-baselining or retiring `ci/vault.json`'s `out_of_scope` declaration when the two documentation changes archive. The gate now fails once every declaring change is archived, so the step cannot be forgotten — but it cannot be skipped either, which is the point |
| Every `file:line` citation resolving into `reference/` is checkable by nobody but their author, because no repository URL or pinned revision is recorded anywhere — 227 of them today, printed by `python3 ci/gates/citations.py` | [obtaining the reference](../history/obtaining-the-reference.md) | The URLs are not in the repository and cannot be derived from it | The repository owner supplying the URLs and revisions, which that page states precisely |

## Refused specification revisions

None to date. `/opsx:update` was invoked seven times by `restructure-docs-as-vault` and proposed no
revision to a file in the declared out-of-scope set; `ci/gates/out_of_scope.py` reports all sixteen
byte-unchanged on every run. The heading stays because the obligation is standing, not because the
list is expected to be empty — an empty list that is checked is a different thing from an absent one.

> Orientation, not behaviour. Where this page and a specification disagree, the specification wins.
