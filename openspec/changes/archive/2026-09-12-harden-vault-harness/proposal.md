## Why

**Nothing forces this change on a deadline, and this proposal will not manufacture a reason.**
`rebuild-plugboard` is 0 of 709 tasks done, no product code exists, and the vault's own ordering says
the schema is frozen before anything else starts. The harness is already **7,882 lines against 8,495
lines of vault it governs** — 0.93 lines of checker per line checked
(`git ls-files -z 'ci/*' | xargs -0 cat | wc -l`). A change that grows it owes a better argument than
tidiness.

The argument is a contradiction, not a deadline. `CLAUDE.md:18` calls `make check` *"every vault
gate; the one command CI runs."* **No CI configuration is tracked** —
`git ls-files | grep -cE '^\.github/|^\.gitlab-ci|^\.circleci/|Jenkinsfile|^\.travis'` returns `0`,
and there are no tracked git hooks. `docs/rule-index.md:13` defines a **gated** rule as one where *"a
check fails the build today."* There is no build. Twenty-one gates are declared blocking in
`ci/vault.json`'s `gate_policy` and nothing blocks: they run when a person chooses to type a command,
which is the condition every one of them was written to replace. Every claim in the change that built
them — that a mis-wired gate is *caught* rather than trusted, that a first draft violating a
convention *fails the build* rather than a review — is currently false by this one omission.

One consequence is already wrong on the page. A single `make check` run prints two counts of the same
enumeration and they disagree: `docs/rule-index.md:17` publishes *"**42 rules** — 20 gated, 19 gate
planned, 3 preference (7% unenforced)"* while `ci/gates/rule_gate_correspondence.py` prints
*"rule notes: 43 (21 gated, 19 gate planned, 3 unenforced = 6%)"*. The missing rule is
`docs/method/authority-precedence.md` — `type: rule`, `**Gate:** ci/gates/precedence.py`, gated and
live — and `grep -c authority-precedence docs/rule-index.md` returns `0`. It appears in no row of the
index whose own header claims *"Every rule this repository states"*, and which `CLAUDE.md:48` routes
every reader to. The cause is a one-directional correspondence: `ci/gates/rule_gate_correspondence.py:71-77`
deliberately holds any note a gate's `RULE_NOTE` names, `ci/gen/rule_index.py:47` walks
`code_standards.rule_dirs` only, and nothing compares the two. `ci/gates/index_drift.py` passes over
it because it verifies a generated file **by re-running its own generator and byte-comparing** —
a wrong generator is consistently wrong, so it verifies as current.

Now rather than after `rebuild-plugboard` task 1.1, because task 1.1 creates five component roots and
709 tasks then begin citing this vault. Each defect below is cheaper to close across 130 notes and 21
gates than across whatever follows. This is also not new scope: `rebuild-plugboard/tasks.md` §3
already schedules a CI skeleton across fifteen tasks, including 3.10's meta-gate and 3.11's
dual-invocation parity. This change moves that work in front of the 709 tasks that depend on it
instead of leaving it behind them.

## What Changes

Ranked by severity times cheapness. The first item is the precondition for every other one mattering.

- **The harness is wired to something that runs it.** A tracked CI configuration invokes `make check`
  on every push and pull request against the tracked tree, and `make check` fails the job on any
  blocking gate's non-zero exit. Until this exists, the other items harden checks that nothing
  executes.
- **BREAKING — "blocking" starts meaning blocking.** Twenty-one gates currently labelled blocking
  become able to refuse a merge. Any tree that would not pass `make check` today stops being
  mergeable, and the label in `ci/vault.json`'s `gate_policy` becomes a statement about the build
  rather than about intent. This is the intended effect and it is the only breaking one.
- **Generators stop being their own oracle.** `ci/gen/` is 515 lines across three generators
  (`indexes.py`, `rule_index.py`, `conventions.py`) producing fifteen tracked files carrying 129 index
  entries, with **zero fixtures** (`ls ci/broken-inputs | grep -cE '^gen'` returns `0`) and no entry in
  `gate_policy`. A generator that produces wrong output consistently passes `index_drift`. Generators
  get the fixture-plus-meta treatment the gates already have: a violating input each, and the
  meta-check's roster extended to cover them.
- **Two encodings of one enumeration must agree.** Where a gate and a generator each resolve the same
  subject set independently — the rule set, the gate roster, the generated-file set — the agreement is
  checked in both directions and a divergence fails. This closes the live 42-versus-43 defect and the
  latent one behind it: `gate_policy.blocking` is checked module-to-list but never list-to-module, so
  an entry naming no module is currently inert.
- **A fixture must demonstrate what it states.** Four `GATE.md` files state a violation count their
  gate does not emit: `citations` says three and emits four, `currency` says four and emits three,
  `index-drift` says four and emits six, `rule-gate-correspondence` says seven and emits eight. The
  meta-check reads the stated expectation and requires it to match. Relatedly, `ci/broken-inputs/out-of-scope/GATE.md:40`
  instructs that meta treat `--self-test` as that gate's second violating input;
  `grep -rn -- '--self-test' Makefile ci/run-gates.py ci/gates/meta.py` returns `0`. The harness
  documents wiring it never built.
- **The coverage line becomes an assertion instead of narrative.** Six gates hardcode
  `from_index=False` and therefore report *"from filesystem (fixture tree)"* while running against the
  tracked repository (`python3 ci/run-gates.py | grep -c 'from filesystem (fixture tree)'` returns
  `6`), while five others hardcode `from_index=True` and claim version control while walking a fixture
  tree; `ci/gates/index_drift.py` names 13 covered files while checking 15; and `_common.py:196`
  hardcodes the noun `file(s)`, so `precedence` prints "5 file(s)" for five layers and
  `component-boundaries` "0 file(s)" for components. A coverage line becomes an assertion about the
  run: the count produced by the reporter from subjects registered as examined, the kind of item
  named, and the source one of version control, a directory scan, or a named manifest key — three
  values, because at least six gates take their set from the manifest and the two-valued vocabulary
  forces them into a false report.
- **An empty subject set must be declared or fail.** `meta.py` proves each gate fails *somehow* on its
  fixture; nothing proves each sub-check inside a gate is still live. Emptying `precedence.layers` or
  `code_standards.components.candidates` in `ci/vault.json` permanently disables a sub-check while the
  fixture stays red and all 21 gates stay green. The obligation that survived prototyping is the
  decidable half: on the run against the tracked tree, a gate examining no subjects fails unless
  `ci/vault.json` records the reason and the work that ends it, and fails again once that work is
  complete and the set is still empty. The stronger form — that emptying an enumeration must fail the
  gate reading it — was cut: "emptied" is a history predicate no algorithm can observe, and for nine of
  ten keyed enumerations emptying changes no gate's verdict at all. `component-boundaries` is the case
  this is built for: legitimately empty until `rebuild-plugboard` task 1.1, and today carrying its
  reason in a docstring where nothing can read it.
- **The register gate reads its prefix from the declaration instead of hardcoding it.**
  `ci/gates/decision_register.py` hardcodes a literal `D` followed by digits, so appending `## R1`
  and `## C1` sections with contradictory meanings to two real notes leaves all 21 gates passing
  while `## D1` fails at the assigning line. This is a one-line change to where the gate reads its
  prefix, and it carries **no new requirement** — the in-force *"There is exactly one decision
  register"* already states the rule, and generalising its text to an arbitrary identifier family
  was drafted, prototyped and then cut (see the non-goals).

### Non-goals

- **No conforming-input fixture set.** A second fixture tree per gate — a deliberately *valid* input
  each gate must pass — is the obvious symmetric move and is refused here. Two controls already cover
  most of it, and neither was named when this was scoped: `ci/gates/meta.py:187-211` asserts each
  per-file gate exits **zero** on all twenty fixture trees that are not its own, and `make check`
  requires all 21 blocking gates to pass the real 130-note vault. Both of the false-positive gates
  that motivated the idea — `precedence` v1 and `currency` v1 — are caught by the second control
  today. What those controls do *not* cover is gate logic that only runs on a legitimate shape the
  vault does not yet contain, and that shape arrives with the component directories. The work is
  deferred to `rebuild-plugboard` task 1.1's doorstep rather than dropped, and this is recorded as a
  decision so it is a scheduled obligation and not a forgotten one. That decision, and any other this
  change records, carries the namespace `HVH` in this change's own `design.md` — the in-force
  one-register rule reserves the unnamespaced sequence for `rebuild-plugboard`'s register, and a
  change that recorded a decision with nowhere legal to put it would be repeating the collision this
  repository already declared breaking.
- **No new capability path.** `docs/gate-harness` was considered and refused: `docs/code-standards`
  already owns this class, a third home splits it further, and a new path immediately owes a concept
  note under `ci/gates/capability_notes.py` plus a permanent node in the dependency graph, for what is
  a handful of clauses.
- **The identifier rule is not generalised to an arbitrary family.** A requirement stating that any
  declared identifier family belongs to its declared register was written, then prototyped against
  the tracked tree, and cut. Measured: it produced **483 findings, zero of them a true positive**,
  because a tokenizer loose enough to see a new family also sees `SHA`, `IPv`, `PBKDF`, `Base` and
  sixteen more; the count swings between 0, 104 and 461 on the tokenizer choice alone, and no reading
  in between catches anything. Worse, it silently dropped five clauses the in-force register
  requirement carries — the five retired identifiers, the superseded register, the collision table,
  reassignment, and carry-forward — which is a measured regression: a revived `D13` is caught by
  today's gate and not by the generalised one. Its only demonstrated catch was an `R1`/`C1` collision
  this change planted itself in a family the repository does not use. The generalisation gets bought
  when a second family actually exists; until then the narrow change above is the whole of it.
- **The runner is not asked to prove the forge refuses a merge.** Whether a hosting service blocks a
  merge is a branch-protection setting held server-side; no tracked artifact states it and no check in
  this repository can read it. The requirement therefore stops at what is decidable from the tree —
  that the runner exists, is triggered on push and on a proposed change, and carries no filter and no
  clause letting a non-zero exit pass. Claiming more would be a scenario nothing can distinguish a
  pass from a fail on.
- **Prose claiming a build that does not exist is not separately forbidden.** A clause to that effect
  was drafted and cut: it flagged 46 legitimate artifacts, 95 of its hits were the `- **THEN** the
  build fails` scenario grammar that names no check at all, and 33 sat inside the byte-frozen
  `rebuild-plugboard/specs`, where the only remedy is an edit that the out-of-scope assertion refuses —
  a deadlock with no nameable work that ends it. The in-force *"The documentation reflects the current
  state"* already governs the class and keeps the decidability hook the drafted clause dropped.
- **`ci/gates/_common.py` gets no gate.** It is 240 lines imported by all 21 gates and excluded from
  the meta-check by name at `meta.py:52`. Narrowing one predicate in `tracked_markdown` collapses
  twelve gates' subject sets by roughly 80% while they print `[ok]`, and fixture trees take the other
  branch, so meta cannot see it. No cheap check closes this; inventing an expensive one to look
  thorough would be the padding this repository's own rules forbid. It is added to the enumerated
  review obligations that `docs/code/reviewing.md` single-sources, so that it is a named obligation a
  reviewer is handed rather than a sentence in a superseded proposal.
- **Stale prose counts are corrected, not gated.** `ci/vault.json` says *"the sixteen gate modules"*
  (there are 21) and *"139 citations point into `reference/`"* (the figure describes the pre-restructure
  tree). Both are fixed in passing. Recomputing arbitrary cardinals out of prose is not decidable, and
  a gate that tried would be the false-positive machine this change exists to avoid.
- **No product behaviour changes, and no `rebuild-plugboard` specification is edited.** Its sixteen
  spec files stay in the declared out-of-scope set that `ci/gates/out_of_scope.py` asserts
  byte-unchanged, for the same reason as last time: `/opsx:update` reconciles neighbouring artifacts
  in any direction over glob-expanded spec paths and forbids only creating them.
- **The three findings recorded as unfixable are not reopened here.** The `auth/sidecar-credentials`
  isolation gap, the absent CORS owner, and the 139 prior-art citations that stay uncheckable until
  the repository URLs are supplied all belong to `rebuild-plugboard` and cannot be touched from this
  change by construction.

## Capabilities

### New Capabilities

- `docs/code-standards`: gate soundness as a checked property — that the gates run on something other
  than a person's initiative, that a generator is verified by something that is not itself, that two
  encodings of one enumeration are reconciled in both directions, that a fixture demonstrates the
  failure it states, that a reported coverage is an assertion about the run rather than narrative,
  and that an empty subject set is declared or fails. Five requirements, twenty scenarios.

  **On the delta operation.** This capability already exists, but only as an unarchived delta inside
  `restructure-docs-as-vault`; `openspec/specs/` is empty
  (`find openspec/specs -mindepth 1 | wc -l` returns `0`). A `MODIFIED` or `RENAMED` delta against it
  is accepted by `openspec validate --strict` but carries a diagnostic saying archive would refuse it,
  so every requirement here is `ADDED`. Two unarchived changes may both carry `ADDED` deltas for one
  capability path and validate cleanly — including with identical requirement titles, which nothing
  detects — so the nine existing requirement titles are checked by hand against the new ones.

### Modified Capabilities

None. `MODIFIED` is unavailable while `restructure-docs-as-vault` is unarchived, and
`rebuild-plugboard`'s requirements are untouched by this change.

## Impact

- **New**: one tracked CI configuration at a path declared in `ci/vault.json`; a violating input plus
  a pinned expected output for each of the three generators, held **outside** `ci/broken-inputs/` so
  that the gate-to-fixture correspondence is not asked to resolve a fixture with no gate; three new
  declarations in `ci/vault.json` (the runner path, the generator map keyed on the tool, and the named
  correspondences) so that no new gate decides its own scope; two new `gate_policy.whole_tree_gates`
  entries, without which the runner and correspondence gates fire on all 21 fixture trees through
  `meta.py`'s isolation check; and five requirements in this change's `docs/code-standards` delta.
- **Modified**: `ci/gates/meta.py` (generator roster, stated-expectation check, `--self-test`
  invocation), `ci/gen/rule_index.py` and `ci/gates/rule_gate_correspondence.py` (the two-way
  reconciliation), `ci/gates/index_drift.py` (coverage names all fifteen subjects), `_common.Report`
  (subject registration, the item kind, and the three-valued source), the twelve gates that hardcode
  a `from_index` value, `ci/run-gates.py` (the blocking classification checked list-to-module),
  `ci/gates/decision_register.py` (its prefix read from `ci/vault.json` rather than hardcoded), the
  four `GATE.md` files whose stated counts disagree with what their gates emit, and `ci/vault.json`
  (two stale prose counts). `ci/gen/rule_index.py` is widened to hold any note a gate names — the
  cheaper side of the 42-versus-43 divergence, one file plus a regeneration, against eight files plus
  `precedence.canonical_note` if the note were moved instead.
- **Sequencing — this change MUST archive after `restructure-docs-as-vault`.** If it archives first,
  the `docs/code-standards` main spec is created with a `TBD` Purpose placeholder naming this change,
  and `restructure-docs-as-vault`'s own Purpose is discarded with only a warning when it archives
  second. The placeholder survives. Archiving `restructure-docs-as-vault` first is clean for OpenSpec
  but breaks the vault until `ci/vault.json`'s capability `spec_glob` and 44 path citations across 38
  tracked files are repointed in the same commit, so that ordering is a prerequisite for this change,
  not a step inside it.
- **No runtime dependency changes.** Every gate and generator stays standard-library-only, per
  `docs/code/languages/python.md`.

### Every number above, and the command that reproduces it

| claim | command | value |
|---|---|---|
| no CI runs the harness | `git ls-files \| grep -cE '^\.github/\|^\.gitlab-ci\|^\.circleci/\|Jenkinsfile\|^\.travis'` | `0` |
| two counts of one rule set disagree | `sed -n 17p docs/rule-index.md; python3 ci/gates/rule_gate_correspondence.py \| grep 'rule notes:'` | `42`/`20` vs `43`/`21` |
| the missing rule is absent from the index | `grep -c authority-precedence docs/rule-index.md` | `0` |
| generators are unverified | `cat ci/gen/*.py \| wc -l; ls ci/broken-inputs \| grep -cE '^gen'` | `515` lines, `0` fixtures |
| entries at risk in generated indexes | `git ls-files 'docs/**index.md' \| xargs grep -hE '^- \[\|^\| \[' \| wc -l` | `129` across `14` files, plus `docs/method/conventions.md` |
| gates mislabel their subject source | `python3 ci/run-gates.py \| grep -c 'from filesystem (fixture tree)'` | `6` |
| gates hardcoding their subject source | `grep -lE 'from_index=(True\|False)' ci/gates/*.py \| grep -vc _common` | `12` |
| index_drift under-reports its coverage | `python3 ci/gates/index_drift.py \| grep -oE 'coverage: [0-9]+ file'` vs its two declared `generated_files` | `13` reported, `15` checked |
| `--self-test` is never invoked | `grep -rn -- '--self-test' Makefile ci/run-gates.py ci/gates/meta.py \| wc -l` | `0` |
| gates that pass on an empty directory | `mkdir -p /tmp/e; for g in ci/gates/*.py; do n=$(basename $g .py); case $n in _common\|meta) continue;; esac; python3 $g --root /tmp/e >/dev/null 2>&1 \|\| echo $n; done \| wc -l` | `7` of `20` fail, so `13` pass |
| harness-to-vault ratio | `git ls-files -z 'ci/*' \| xargs -0 cat \| wc -l; git ls-files -z 'docs/*' \| xargs -0 cat \| wc -l` | `7882` / `8495` = 0.93:1 |
| no capability has a main spec | `find openspec/specs -mindepth 1 \| wc -l` | `0` |
| the product is not started | `grep -cE '^\s*- \[[ x]\] [0-9]' openspec/changes/rebuild-plugboard/tasks.md` | `709`, `0` done |
