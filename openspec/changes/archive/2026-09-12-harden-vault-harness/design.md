## Context

See [proposal.md](proposal.md) — *Why*. The short version: 21 gates are declared blocking, no tracked configuration executes any of them, and one `make check` run already prints two disagreeing counts of its own rule set.

Three properties of the existing harness shape every decision below.

**The manifest is the only declared location.** `ci/vault.json` holds every root, exemption, enumeration and policy any gate reads, and `ci/gates/_common.py` states the reason in its own docstring: *a gate never decides its own scope*. Any new check that infers its subject from the tree rather than from that file breaks the property the harness was built on.

**`meta.py` proves firing, and two other things prove non-firing.** `meta.py:187-211` requires each of the five per-file gates to exit **zero** against all twenty fixture trees that are not its own — 100 must-exit-0 assertions. `make check` requires all 21 blocking gates to pass the real 130-note vault. Between them these are a real negative control, and both false-positive gates in this repository's history would be caught by the second one today. This was not understood when the change was scoped, and correcting it removed a third of the intended work.

**The tracked tree and a fixture tree are different subjects.** 18 of 20 gates load the manifest from `repo_root()` regardless of `--root`; a fixture is deliberately broken and deliberately partial. A requirement that does not say which run it governs will be read against both, and the second reading is where this project has previously generated 165 failures containing no defect.

## Goals / Non-Goals

**Goals:**

- Every requirement here is checkable by a gate that can be written now, against the tree as it is.
- Every requirement was prototyped and run against the real vault before its text was fixed.
- No new gate decides its own scope; each reads a declaration this change adds to `ci/vault.json`.
- The harness gains no dependency. Standard library only, per `docs/code/languages/python.md`.

**Non-Goals (design level — the proposal's scope refusals are in its own Non-goals):**

- No change to what any existing gate *enforces*. Where an existing gate is touched it is to correct how it reports, what it reads its scope from, or a stated count — never to widen a rule.
- No CI provider is fixed by this design. See `HVH2`.
- No change to `openspec/` workflow schemas or templates.

## Decisions

### HVH1. The runner lands first, and the other four requirements are inert until it does

The proposal ranks CI first on severity × cheapness. The design makes it a hard ordering: requirements two through five are checks on checks, and a check on a check nobody runs is worth exactly nothing. Wiring a runner is one file; it converts 21 advisory scripts into 21 blocking ones and gives every other requirement here a consequence.

*Alternative considered — harden the checks first, wire CI when the harness is "ready".* Rejected on evidence produced during this change: a half-staged rename sat in the index for hours with one gate crashing on a path `git ls-files` reported as tracked, and it survived a completion report and a session boundary because the only thing that would have caught it was a command a person has to choose to type. The ordering is not a preference; the counter-example is in this change's own history.

### HVH2. The runner is addressed by a declared path, not by a provider

The requirement says a tracked runner configuration exists **at the path `ci/vault.json` declares**, is triggered on push and on a proposed change, and carries no filter and no clause letting a non-zero exit pass. It names no provider.

This is deliberate. The repository has no configured remote, so nothing in the tree determines a forge. Keying the requirement on a declared path means the provider is a task-level input rather than a spec-level commitment: switching forge later edits one manifest value and one file, and touches no requirement. It also stops the gate hardcoding a guessed path, which would violate the scope property above.

*Alternative considered — name the provider in the requirement.* Rejected: it would put a vendor in a behaviour contract, and the first migration would need a spec change to describe the same behaviour.

### HVH3. Declaration over discovery — the same move, three times

Three requirements need to know *which* things they govern: which tools generate artifacts, which sets are resolved twice, and where the runner is. In every case the first draft inferred it from the tree, and in every case the inference was the defect.

| requirement | inferred trigger, first draft | findings on the real vault | after declaring it |
|---|---|---|---|
| reconciliation | "published in a tracked artifact a reader is routed to" | 361 findings, 1 true positive | 1 |
| generator oracle | "a check that re-runs its own generator" | 15 of 15 correct artifacts flagged | 3 true positives |
| identifier register | "an identifier drawn from a sequence" | 483 findings, 0 true positives | requirement cut |

The reader-routed trigger is the clearest case: 156 of 159 tracked subjects are reachable from an entry point *because an in-force requirement says they must be*, so a trigger keyed on reachability narrows nothing at all. A pair of encodings is a fact about the repository's construction that a human knows and a regex cannot recover; so it is declared, named, and checked — and a correspondence whose two sides are later unified by one resolver is retired from the declaration with that resolver recorded as the reason, so the list cannot silently accumulate dead entries.

*Alternative considered — discover the pairs by static analysis of the gates and generators.* Rejected as the third encoding problem: a reconciliation that re-derives a side for itself is not checking the side the gate actually uses.

### HVH4. A generator is pinned to a tracked expectation, not forbidden from self-comparison

`index_drift` verifies a generated artifact by re-running its generator and byte-comparing. The first draft forbade exactly that: *"the check SHALL NOT derive its expectation solely by re-running that generator."*

That text is wrong twice. It constrains how a checker is implemented rather than what must hold, which is not what a spec is for; and it is satisfied by nothing available — it flags all 15 tracked generated artifacts with no remedy, because for 173 rendered values there is no second source to compare against. What is buildable is an oracle the generator cannot move: a small input tree plus the exact output that generator is expected to produce on it, both tracked. The generator's output on that input either matches the pinned file or the build fails, naming the first differing line.

Each generator additionally states, in its own module, **the class of wrongness its violating input does not reach** — because a pinned expectation over one small tree is a real oracle and a partial one, and a partial oracle that does not say so is the "documents wiring it never built" defect in a new costume.

### HVH5. Generator fixtures live outside `ci/broken-inputs/` — a reversal

The first draft put them inside it, and the proposal said so. That is unsatisfiable by construction and was caught by prototyping: `meta.py:62-70` maps `ci/gates/<module>.py` to `ci/broken-inputs/<gate-id>/`, so a generator directory there has no module to run, and the requirement that every violating input declare *the violations its gate emits* cannot be met by a fixture that has no gate and emits an artifact. The change's own Purpose paragraph had defined a violating input as one held "to demonstrate a gate", contradicting its own next requirement three paragraphs later.

Planting an orphan fixture directory to check the consequence turned up something worth keeping: `meta.py` does not fail on it, it **ignores** it. The gate↔fixture correspondence runs gate→fixture only. A fixture directory nothing runs is dead weight nobody notices — which is the one-direction class this change already exists to close, found in the mechanism built to prevent it. It is folded into the reconciliation requirement rather than given a requirement of its own.

### HVH6. The coverage line's subject source is three-valued

The first draft offered two values, version control or a directory scan. At least six gates take their subject set from a named manifest key and are neither; forced to pick, they must report something false, and the requirement would then fail them for it — a gate demanding a thing its subjects cannot supply, which is precisely the `currency`-v1 defect this repository already recorded.

So the vocabulary is version control, a directory scan, **or a named key in `ci/vault.json`**. Two further clauses come from the same measurement. The count is produced by the shared reporter from subjects a gate registers as it examines them, rather than handed over as a literal, because a literal is an assertion nothing checks — twelve gates hardcode one today. And the line names **the kind of item counted**: `_common.py:196` hardcodes `file(s)`, so `precedence` reports "5 file(s)" for five precedence layers and `component-boundaries` "0 file(s)" for components.

The comparison the build actually performs is the one decidable without an oracle: a run whose scan root is not a version-control work tree cannot have read its set from version control.

### HVH7. Vacuity is governed on the tracked-tree run only — a reversal

The first draft governed every run, and the prototype produced **138 false positives out of 148**: every gate whose subject set is legitimately empty against a small fixture tree, plus ten new `meta.py` isolation failures. This is the same trap this repository sprang once before and recorded in `ci/vault.json`'s `whole_tree_gates` comment — *"165 failures, none of them a defect"* — which is what satisfying a universally quantified property literally costs here.

So the obligation is scoped to the run the aggregating target makes with no tree argument. On that run a gate examining no subjects fails unless the manifest records the reason and the work that ends it — and fails again once that work is complete and the set is still empty, so a declaration cannot outlive its reason. `component-boundaries` is the case this is built for: legitimately empty until `rebuild-plugboard` task 1.1, and today carrying its reason in a docstring where nothing can read it.

*Alternative considered — require that emptying a declared enumeration fail the gate that reads it.* Rejected as unobservable: "emptied" is a claim about history, and an algorithm sees only the current value. Measured inert besides — for nine of ten keyed enumerations, emptying changes no gate's verdict. The purpose clause was deleted with it rather than kept as a promise the check does not keep.

### HVH8. The conforming-input fixture set is deferred to `rebuild-plugboard` task 1.1 — a reversal

This was recommended, in these words, as the single highest-value structural addition: a deliberately *valid* fixture per gate, on the argument that the harness checks rules bidirectionally and checks itself in one direction only. The argument was wrong and the reversal is recorded because the reasoning matters more than the conclusion.

`meta.py:187-211` already is a negative control — 100 must-exit-0 assertions against inputs built to trip a different rule — and `make check` over the real vault is a richer one. Both of the false-positive gates that motivated the idea are caught by the second one today; that was verified by rebuilding the working tree as a real work tree and reintroducing `precedence` v1, which fails `make check`.

What the existing controls do not cover is gate logic that only runs on a legitimate shape the vault does not yet contain — and that shape arrives with `contract/ proxy/ sidecar/ terminator/ conformance/` at task 1.1, when `component-boundaries` goes from 0 subjects to 5 and `language-coverage` from 1 language to 3. Building the fixtures now would be writing valid trees for shapes nobody has seen. This decision is the scheduled obligation the proposal promises, and it lives here so that it is findable rather than remembered.

### HVH9. The rule index is widened; the note is not moved

The live 42-versus-43 divergence has two possible closures. `ci/gen/rule_index.py:47` walks `code_standards.rule_dirs`; `docs/method/authority-precedence.md` is a gated rule note that lives outside them because the authority precedence is canonically stated in the spine.

Widening the generator to hold any note a gate names is one file and a regeneration, and it makes the generator agree with the gate by construction. Moving the note into `docs/code/rules/` would repoint eight files plus `precedence.canonical_note`, which `precedence.py:48` reads, and would relocate the canonical statement of the precedence order away from the spine to satisfy a generator — the tail wagging the dog.

*Alternative considered — have the correspondence gate assert the index's stated totals.* Rejected as the weaker fix: it detects the divergence without removing the cause, and it compares cardinals rather than members, which the reconciliation requirement forbids.

### HVH10. Prose claiming a build that does not exist stays with the currency rule — a reversal

Drafted as a clause of the first requirement, then cut. Three measurements killed it. It flagged 46 legitimate artifacts; 95 of its hits were `- **THEN** the build fails`, the THEN-clause of nearly every scenario in the repository, naming no check for its escape clause to resolve; and 33 sat inside `openspec/changes/rebuild-plugboard/specs`, which `ci/gates/out_of_scope.py` asserts byte-unchanged — so the clause demanded a failure whose only remedy is an edit another in-force requirement refuses. A deadlock with no nameable work that ends it, confirmed by editing one such line in a copied tree and watching `out-of-scope` report it.

The in-force *"The documentation reflects the current state"* already governs the class and keeps the decidability hook this clause dropped: a planned marker names its subject as a path a gate can test for existence. `docs/why/success-criteria.md:44-45` already applies it to exactly this claim about the Makefile.

## Risks / Trade-offs

- **The first CI run is red on the commit that introduces it.** `reachability` fails on a change's own planning artifacts until a note outside the planning directories links them, and it has no grace period — this change hit it live. → Ordered in the migration plan: the vault links land before the runner does. Encountered once already and fixed by linking from the capability note and the documentation-rules note, so the shape of the fix is known.
- **Two new gates fire on all 21 fixture trees.** No fixture contains a runner configuration or the new declarations, so through `meta.py`'s isolation check both new gates fail on every tree that is not their own. → They are declared in `gate_policy.whole_tree_gates` in the same commit that adds them, with the reason recorded there. This is not a workaround; it is the existing declared mechanism for a gate whose subject is the whole tree.
- **`ci/gates/_common.py` is unguarded and has the widest blast radius here.** 240 lines imported by all 21 gates, excluded from `meta.py` by name at `:52`. Narrowing one predicate in `tracked_markdown` collapses twelve gates' subject sets by roughly 80% while they all print `[ok]`, and fixture trees take the other branch so `meta.py` cannot see it. → No cheap check closes it and an expensive one built to look thorough is padding this repository's own rules forbid. It is added to the enumerated review obligations `docs/code/reviewing.md` single-sources. This is the weakest mitigation in the change and is recorded as such rather than dressed up.
- **A pinned generator expectation is a partial oracle.** It catches drift on one small tree and misses a wrongness that tree does not exercise. → Each generator states the class of wrongness its input does not reach, so the gap is written down where the next person reads it instead of being implied by a green run.
- **The harness grows again.** It is already 7,882 lines against 8,495 lines of vault. → Five requirements, no new capability, no new fixture tree per gate, and three of the five are edits to existing gates rather than new modules. The proposal's cheapest-subset estimate is 30–50 lines across three existing files for the two live defects; the runner and the generator fixtures are the only genuinely new surface.
- **Archive ordering is load-bearing and easy to get wrong.** → Stated in the proposal's Impact and repeated in the migration plan below; it is a prerequisite for this change, not a step inside it.

## Migration Plan

Ordered, because three of these steps turn the build red if taken out of sequence.

1. **Link this change's own artifacts into the vault** from a note outside the planning directories. Already done for `proposal.md` and the code-standards delta; must be repeated for `design.md` and `tasks.md` as they land, or `reachability` fails.
2. **Add the three declarations to `ci/vault.json`** — runner path, generator map keyed on the tool, named correspondences — before the gates that read them exist, so no gate is ever written that guesses its own scope.
3. **Close the two live defects**, which need no new gate: widen `ci/gen/rule_index.py` and regenerate; correct the four `GATE.md` stated counts; give `index_drift` its full fifteen subjects.
4. **Correct the reporting surface** in `_common.Report` and the twelve gates that hardcode a `from_index` value, then add the coverage assertions.
5. **Add the new gates**, each with its violating input, each declared in `whole_tree_gates` in the same commit.
6. **Wire the runner last**, when `make check` is already green on the tracked tree. A runner introduced against a red tree teaches everyone to ignore it.

**Rollback.** Every step is a tracked file and a manifest key. Reverting the runner configuration returns the gates to advisory without touching a gate; reverting a gate returns its rule to `**Gate:** planned`, which the correspondence check accepts provided the rule note links the work that builds it.

## Open Questions

- ~~**Which forge hosts the runner.**~~ **Resolved: GitHub Actions**, a tracked `.github/workflows/check.yml` invoking the aggregating target on `push` and `pull_request`. Those are the two triggers the requirement names, and a forge workflow observes both; a local hook was considered and rejected because it cannot observe a proposed change, so adopting it would have meant narrowing the requirement's trigger clause to fit the mechanism. `HVH2` still stands and is why this was answerable late: the requirement is keyed on the path `ci/vault.json` declares, so this answer sets one manifest value and names one file, and changes no requirement. The file is inert on a repository with no remote, which is the current state.
- **Whether two unarchived `ADDED` deltas carrying the same requirement title survive archiving in sequence.** Untested, and moot for this change: the five new titles were checked by hand against the nine existing ones and none collides. It becomes live only if a third change adds to `docs/code-standards` before either of these archives.
