## Context

See `proposal.md` — Why. The constraints that shape the approach, not the motivation:

**Two readers, one set of files.** A person navigates by link, backlink and graph; an agent retrieves by path and pays for every token it reads. Anything that serves only one of them creates a second artifact for the other, and two artifacts drift. Every mechanism chosen below is chosen because one file satisfies both.

**The prose is the most valuable thing in the repository, and it is also the largest liability.** The reference carried 148 KB of prose against a history of `updated code`, and two of its documented claims are verifiably false (`docs/method/documentation-rules.md#documentation`). This change roughly doubles the note count. It is therefore only defensible if the falsifiability gate scales with the surface, which is why the majority of the requirements in `docs/knowledge-base` are gates rather than conventions.

**The work lands ahead of a 709-task plan at 0 done.** `rebuild-plugboard` tasks 1.1, 1.3, 1.4 and 1.10 already own the directory shape, the entry files, the link checker and the docs gate. Doing this after they run means rewriting them twice; doing it before means they are written once, against paths that exist.

**Nothing is enforced at authoring time today, and the obvious hook does not reach a note author.** `openspec/config.yaml` has its `context:`, `rules:` and `operations:` blocks entirely commented out, so an agent writing a spec or a task receives no project conventions at all. But that file is also not sufficient: its `rules:` block is keyed per openspec artifact, so it cannot carry an obligation on a note. Every convention in this change is currently a review-time hope, and closing that needs two channels rather than one — see `RDV10`.

**Two changes are in flight at once, and one is the authority for the other's decisions.** `rebuild-plugboard` holds the decision register this change consolidates into, and this change edits four of its tasks and its design while it sits at 0 of 709. The instrument for those edits performs a coherence pass across neighbouring artifacts, so the boundary between "the artifacts this change may edit" and "the sixteen specifications it must not" has to be a checked property rather than an instruction.

## Goals / Non-Goals

**Goals:**

- One vault, one spine, one decision register, one statement of each component boundary — with a gate behind each "one" so that a second copy fails rather than being noticed.
- A middle layer between orientation and normative behaviour, sized so it can be read whole before a spec is opened.
- Traceability that a person and an agent both get from the same syntax, with no plugin and no build step required to follow a link.
- The absence of enforcement made visible, so an ungated rule cannot be mistaken for an obligation.
- Doc currency as a gate rather than a promise, **in both directions**: a note whose subject was deleted fails the build, and so does a note still marked planned once its subject exists.
- Every obligation's scope declared, so that which files a gate governs is a decision in this specification rather than a property of a scanner's configuration.

**Non-Goals (design-level, beyond the proposal's scope):**

- Not a documentation generator. Prose stays hand-written; only indexes are generated.
- Not a knowledge graph in the graphify sense. That tool maps code once code exists; this vault maps intent. The precedence order below keeps them from competing.
- Not a migration of the specs into the vault's conventions. Specs keep their own format and their own authority, and that boundary is asserted byte-unchanged by a gate rather than promised in prose.
- No note is written for a component that does not yet exist. The structure is created; stubs are not.

## Decisions

### RDV1. Vault root is the repository root, and `docs/` is the spine

The alternative shapes were a `vault/` directory beside `docs/`, and a `docs/` tree with the essays left numbered. Both were rejected for the same reason: the sixteen specs are the behaviour authority, and under any shape where the vault is a subdirectory, the specs are either outside the graph or copied into it. With the repository as the vault, `openspec/changes/**/spec.md` are *already notes* — they appear in the graph, accept backlinks, and are linked to rather than summarised.

The cost is that the vault also indexes `reference/` while it is present on disk, and will index `graphify-out/` once it exists. Both are handled by the reader's exclusion list rather than by moving the vault, because excluding a directory from a view is reversible and relocating the vault is not.

### RDV2. Relations are relative markdown links; wikilinks are prohibited

This is the decision most likely to be re-litigated, so the reasoning is recorded rather than the conclusion.

| | `[[Version Skew]]` | `[Version skew](../why/version-skew.md)` |
|---|---|---|
| renders on GitHub | no — literal text | yes |
| an agent resolves it | must search | directly, by path |
| off-the-shelf link gate | no | yes |
| Obsidian backlinks and graph | yes | **yes** |
| rename safety | automatic | reader rewrites on rename |

The decisive row is the fourth: Obsidian's backlink pane and graph view work on relative markdown links, so wikilinks buy authoring ergonomics and cost the three rows above them. Transclusion (`![[…]]`) is prohibited on the same grounds and one more — a transcluded fact reads as present to a person and as absent to an agent reading the raw file, which is the exact failure mode this change exists to remove.

*Alternative considered:* wikilinks plus a wikilink-aware checker and a GitHub rendering shim. Rejected: it makes the repository's most basic affordance depend on bespoke tooling, and `docs/method/documentation-rules.md` already treats bespoke tooling around a checker as a defect source.

### RDV3. Frontmatter classifies; the body relates

Frontmatter carries exactly three fields — `type`, `status`, `authority` — each from a closed enumeration. Relations are body links.

The split is not aesthetic. A relation in frontmatter is invisible in the rendered file, absent from the backlink pane, and unfollowable by a person, so it must be duplicated as a link anyway; two encodings of one relation is the drift this change is removing. A classification, by contrast, is not a relation and has nowhere better to live.

Three fields, not eight, because the query mechanism is grep plus a small generator — not Dataview, which is a plugin an agent cannot execute and GitHub cannot render. `docs/knowledge-base` therefore requires that a field no gate and no generator reads is refused, which is what stops the frontmatter growing into decoration.

**Which files this reaches is now stated, because it was the plan's largest hole.** An adversarial review found that "note" was defined as any tracked markdown file inside the vault, the vault root was the repository root, and `RDV1` says the specs "are *already notes*" — so an unqualified "every note carries frontmatter" reached all sixteen specs and `rebuild-plugboard`'s three planning artifacts, contradicting a headline non-goal. Worse, no requirement authorised an exemption of any kind, so the first gate written filled that hole with an undeclared exclusion list in its own manifest, silently exempting twelve tracked files under `.claude/` — a gate mechanism with no rule behind it, which is the precise inverse of `RDV6`.

The scope is therefore declared rather than inherited from a scanner's configuration. Every root is either **governed** or **exempt**, both named in the one retrievable location, and an exempt root carries a recorded reason stating what owns its files instead. Each gate reports the roots it excluded, so a passing run states its own coverage instead of implying total coverage; a directory omitted from a traversal without being declared exempt fails. And the obligations do not share one scope — classification covers the spine and the per-component roots, links and reachability additionally cover the planning directories, and tool-owned directories are exempt outright. An obligation whose scope is unstated is now a specification defect rather than a licence for the gate author to decide.

### RDV4. `design.md`'s numbering wins; the orphans become D21–D27; D11–D15 stay vacant

The collision is asymmetric. `design.md` is the stated authority (`CLAUDE.md`), it is what the specs cite (`D16`, five times), and it is what four of the five decision citations in `tasks.md` resolve against. `docs/05-decision-log.md` is cited by no artifact outside itself, and `CLAUDE.md` already records its "Open questions" table as stale.

But it is not a deletion. Seven decisions are recorded **only** in `docs/05` — rebuild-from-scratch, one-repository, contract-first-with-conformance, version-skew-as-governing, the positioning, WebTransport-deferred, and observability-before-the-hot-path. These are folded into `design.md` as `D21`–`D27` *before* the file is removed, which is why `docs/knowledge-base` requires that a register cannot be removed while it holds a unique decision, verified by enumeration.

`D11`–`D15` are left permanently unassigned. `design.md` jumps `D10` → `D16`, and `docs/05` fills `D11`–`D15` with five decisions of its own. Reusing those numbers would make a citation written today ambiguous against any archived citation, so the numbers are retired and a collision table records what the superseded register called each one.

*Alternative considered:* renumber both registers into one clean sequence. Rejected — it breaks the five `D16` citations in the specs and every `D`-citation in `tasks.md` for a cosmetic gain, and it is exactly the kind of churn a 709-task plan at 0 done cannot absorb.

The immediate proof that this matters: `tasks.md:3` justifies the single-repository directory shape with "D2 and D4". Under `design.md` alone, `D2` is the frame-shaped tunnel and `D4` is the runtime choice, neither of which requires a single repository. The sentence is only coherent if `D2` is read from `docs/05` and `D4` from `design.md` — a citation that silently mixes registers, in the first task of the plan.

**A change's own decisions are namespaced, and this change's were not.** An adversarial review of this plan found that the decisions in this very file were numbered `D1`–`D10`, colliding one-for-one with `rebuild-plugboard`'s `D1`–`D10` — reproducing the exact defect this change calls BREAKING, in the act of fixing it. `D1` here was "vault root is the repository root"; `D1` there is "three primitives, not twelve protocols". They are now `RDV1`–`RDV10`.

The rule that follows, and that `docs/knowledge-base` states so future changes inherit it: **the unnamespaced `D<n>` sequence belongs to the declared register alone.** A change's design rationale may record decisions of its own, and they carry a prefix naming the change. A namespaced set is not a register; an unnamespaced identifier introduced anywhere but the declared register is a gate failure, whatever file it appears in.

This also fixes what the review found to be an undefined gate subject. Scoped to a literal path, the single-register gate would fail this tree the moment these artifacts are tracked; scoped to "any file named `design.md`", it would license every future change to open its own `D1`–`D10`. Scoped to *an unnamespaced identifier outside the declared register*, it catches both, and citing an existing identifier — the collision table, the decision notes, a task — is explicitly not introducing one.

### RDV5. The capability graph is built in the vault, not in the specs

Sixteen concept notes each link to their spec and to the capabilities their spec names as dependencies. The eighty backticked cross-references inside the specs are left as they are.

The obvious move is to turn those eighty strings into links directly, which would put the graph in the authoritative files. It is deferred because the specs are the one artifact whose format is validated by an external tool. Building the graph one layer out gets the whole navigational payoff — "what depends on `tunnel/listener`" is answered by that note's backlinks — at no risk to sixteen files that 709 tasks depend on. Linking the specs directly becomes a follow-up.

**The evidence this decision originally lacked now exists, and it is narrower than the deferral assumed.** Prepending `type`/`status`/`authority` frontmatter to two `spec.md` files plus `proposal.md`, `design.md` and `tasks.md` in a scratch copy leaves `openspec validate rebuild-plugboard --strict` reporting the change valid, `openspec list` reporting 0/709 tasks, and every requirement still parsing, on openspec 1.12.0. One caveat: `openspec show` echoes the YAML block raw into its output, so frontmatter becomes part of what an agent reading through that command sees.

So the tool tolerates *frontmatter*. That is what unblocks the scope question in `RDV3` — the classification requirement could have covered the planning artifacts safely. It is deliberately still scoped to exclude them, on ownership grounds rather than fear: an external tool owns those files' format, and a convention this repository imposes on a file that tool authors is a convention that breaks on the tool's next release. What remains untested is *links inside a `## Purpose` paragraph*, which is the actual subject of this decision, so the deferral stands on its original terms with the frontmatter question removed from it.

The correspondence is gated in the direction that can drift: a dependency named in a spec with no matching link in the concept note fails.

### RDV6. Every rule states its gate, and the gate's failure message states the rule

The guide's structure follows from one line in the existing methodology — *"a rule with no gate is a wish"* (`docs/method/documentation-rules.md#documentation`). So the guide is organised by enforcement rather than by topic, and the correspondence is checked both ways: a gate naming no rule note fails, a rule note claiming a gate that is not run fails.

The bidirectional check is the part that earns its cost. A one-directional check (every rule has a gate) still permits a gate nobody can find the rule for, which is how a lint rule becomes folklore. Making the failure output name the rule note also converts each gate into the teaching surface — the contributor who trips it is handed the defect it prevents and its citation, which is the cheapest moment to learn it.

Ungated rules are not banned, because some genuinely are taste. They are quarantined, marked as preference, barred from being cited as blocking objections, and their proportion is retrievable — so a guide sliding toward unenforced opinion is a visible number rather than a feeling.

### RDV7. Banned patterns are atomic; carry-forward is not

Both are enumerable lists, and they get opposite treatment, which needs a stated reason.

A banned pattern is a *citation target*: a gate cites it, a review comment cites it, a spec may cite it. Roughly a dozen of them, each mapping to one lint rule and one reference defect. Atomic notes with stable anchors are what make `docs/code/banned-patterns/headers-as-a-map.md` addressable from a CI failure message.

A carry-forward item is a *work item*, and there are about sixty. Nothing cites one individually yet, because the tasks that port them have not run. Sixty notes with no inbound links would each fail the reachability gate or force sixty index entries that exist only to satisfy it. So `docs/06-carry-forward.md` stays one note with stable per-item anchors, and an item is split out the first time a task cites it — the split becomes cheap exactly when it becomes useful.

### RDV8. Precedence is stated once, and ranks five layers

```
  1  contract/            machine-checked                  ABSOLUTE
  2  openspec specs/      normative SHALL statements        BEHAVIOUR
  3  design.md D1-D27     decisions in force                DECISIONS
  4  docs/ notes          orientation, rationale, glossary  NEVER states behaviour
  5  graphify-out/        generated from the AST            WHERE the code is
```

This extends the chain `CLAUDE.md` already states (contract beats `design.md` beats `docs/`) rather than replacing it, and it adds the layer that does not exist yet: once code exists, graphify produces a third navigation surface. Naming its rank now is cheaper than discovering the competition later. The division is *why* (layer 4), *what* (layer 2), *where* (layer 5).

The load-bearing consequence is the rule that a layer-4 note may not state behaviour a layer-2 spec owns. Without it, the vault becomes the place where a plausible sentence about behaviour lives unchecked — which is precisely how the reference acquired two false documented claims.

### RDV9. Currency is a gate, not a review habit

"The documentation reflects the current state" is stated as four checkable properties rather than as an intention: a note whose subject is removed fails, a superseded note must name its replacement, a note describing something unbuilt must be marked planned and link to the work that builds it, and **a planned marker must be retired once its subject exists.**

The third is the one that applies today, because almost nothing in this repository exists yet. `CLAUDE.md` currently instructs an agent to prefer `graphify query` over grep against a graph that has never been generated, and its hook fires on a file that does not exist — a live instance of a doc describing an absent artifact as present. The gate that refuses that is the same gate that keeps the vault honest once there is code.

**The fourth property was missing, and it is the one that will actually fire.** An adversarial review found that the currency requirement ran in one direction only. Because this change lands *before* `rebuild-plugboard` 1.1 — the task that creates `contract/`, `proxy/`, `sidecar/`, `terminator/` and `conformance/` — nearly the whole spine gets stamped planned against directories that appear almost immediately afterwards, and nothing would ever un-stamp them. `status: planned` would become the default value across the vault at the exact moment CI started passing, which is the value an agent reads to decide whether a note can be trusted. A currency guarantee enforced only in the direction that is empty today would have reported green over a vault that had gone stale everywhere.

So a marker must name its subject as a path the gate can test for existence, and a note still marked planned whose subject is present — or whose linked task is complete — fails. That makes the marker's own correctness decidable instead of a matter of reading, which is the same substitution the rest of this change rests on.

### RDV10. Conventions are supplied at authoring time, keyed to the gates

This is the same substitution the whole rebuild rests on — structure instead of discipline. A convention enforced only at review is a convention an agent violates on every first draft, and every first draft costs a review cycle. `docs/method/harness.md#structural-gates-not-instructions` states the principle ("structural gates, not instructions") and then leaves the project's single authoring-time hook switched off.

**One channel is not enough, and the original version of this decision named only one.** An adversarial review established that `openspec/config.yaml`'s `rules:` block is keyed *per openspec artifact* — `proposal:`, `design:`, `specs:`, `tasks:` — so it cannot express an obligation on a note at all, and `context:` is by the file's own documentation shown only "to AI when creating artifacts". The single substitution this decision rests on could not reach the author it most needed to reach. The file's third block, `operations:`, which governs the apply and archive loops, was named nowhere in the plan — and that loop is what will touch this vault hundreds of times across 709 tasks.

So there are two channels, keyed on one convention source so they cannot diverge:

- The **planning-artifact channel** — `context:`, `rules:` *and* `operations:`, covering both artifact authoring and the apply/archive loop.
- The **note-authoring channel** — a location a note author reads before writing, which the planning tool's configuration explicitly is not. A hook, or a conventions note that the entry files link as their first hop, generated from the same source.

`docs/knowledge-base` requires both, and requires that a convention reaching the gates but not both channels fails. Relying on `config.yaml` alone would have left every per-note obligation — frontmatter, the planned marker, the precedence header — exactly where this decision says a convention must not be: at review.

## Risks / Trade-offs

**[The gate count is the real cost: roughly thirty distinct checks across about a dozen gate families, before a line of product code exists]** → This bullet previously said "seven new gates", and an adversarial review recounted it: `tasks.md` introduces on the order of twenty-six gate-introducing tasks, unpacking to roughly thirty checks, against about forty gate-failure scenarios across the two specifications. The figure mattered because it is the number this risk was accepted at — a reviewer who accepted seven cheap markdown checks had not accepted thirty, each of which also carries a violating input, a rule note, a failure message naming that note (`RDV6`), and an entry in both authoring channels (`RDV10`).

The gates are not cut to make the sentence true. The density is load-bearing: `RDV6`'s correspondence and the falsifiability argument in Context both scale with the note surface, and a plan that doubles the prose while holding enforcement flat is the reference's failure mode with better intentions. What changes is the honesty of the number. *Mitigation:* every one of them is a check on markdown, so they are cheap to run and cheap to fix; each is demonstrated against a deliberately violating input (`docs/code-standards`) so a mis-wired gate is caught rather than trusted — the precedent being the plural-versus-singular `--warnings-as-errors` flag in the reference, where nobody checked whether the checker checked; the violating inputs are part of this change, not a follow-up; and the aggregating target enumerates every gate it ran, so the inventory is a build output rather than a prose claim that can drift again.

**[Reachability gating makes adding a note more work than writing one]** → A note nobody links to is a note nobody finds, so the friction is the point. But it does mean the index notes must be generated rather than hand-maintained, or every new note becomes two edits. *Mitigation:* RDV3's generator plus the drift check; a stale index fails, so the generated path is the path of least resistance.

**[Doubling the note count doubles the surface for unfalsifiable prose]** → The reason the falsifiability requirements are gates in `docs/knowledge-base` rather than rules in `method/`. *Mitigation:* the citation gate covers behavioural claims, and the obtainability requirement closes the hole that makes 139 existing citations uncheckable.

**[A rename storm across ten files that reference the numbered essays]** → Bounded and enumerable, but larger than this bullet first claimed: **thirty-nine occurrences across ten pre-existing files**, not fifteen across four. An adversarial review found the original inventory counted only the `docs/NN-*.md` form and missed twenty-four bare relative links of the form `](02-architecture.md)` inside `docs/` itself — eleven of them in `docs/README.md`, a file the plan did not account for at all. The two classes need different detectors: the fifteen prefixed occurrences are backticked prose no link gate can see, so the `docs/0` search is their only detector; the twenty-four relative ones are real markdown links squarely inside the link gate's scope. *Mitigation:* both detectors are named in the move task, and the link gate lands before the move, so the move is verified rather than reviewed.

**[Editing `rebuild-plugboard`'s artifacts from a second change in flight]** → Its `design.md` gains D21–D27 and four of its tasks are rewritten, while it sits at 0 of 709. *Mitigation:* those edits go through `/opsx:update`, never by hand, and they are the last tasks in this change so that the paths they point at already exist.

**"Nothing in its sixteen specs is touched" is now a gate, not a sentence.** An adversarial review pointed out that `/opsx:update` — the instrument named as the mitigation — is itself the most likely way to break the guarantee: its procedure applies the requested edit and then reconciles *every other existing artifact* against it "in ANY direction", over paths glob-expanded to the concrete `spec.md` files. Only *creating* an artifact is forbidden; revising one is not. So adding D21–D27 to `design.md` is exactly the kind of edit whose coherence pass reaches sixteen files that cite `D16` five times and that 709 tasks depend on — and a single reconciling edit there would silently invalidate `RDV5`'s entire justification. This change is invoked seven times against that change.

An intention recorded in prose is not a control. `docs/knowledge-base` therefore requires a declared out-of-scope set asserted byte-unchanged as part of the aggregating target, each `/opsx:update` task refuses any proposed spec revision and records it as follow-up work, and the closure tasks assert the specs' diff is empty.

**[Obsidian becomes a soft dependency that quietly hardens]** → A convention that only Obsidian can satisfy would make the reader mandatory. *Mitigation:* RDV2 and RDV3 exist precisely to keep every affordance available to `cat`, `grep`, GitHub and a link checker; the reader adds the graph view and the backlink pane and nothing the repository depends on. A gate requiring Obsidian to run would be a defect.

**[The style guide is written before the code it governs]** → Its content is derived from cited failures in 27k lines of prior art rather than from taste, which is the same derivation the methodology already used. But some rules will be wrong, and a wrong gated rule is more expensive than a wrong ungated one. *Mitigation:* the quarantine cuts both ways — a rule whose gate cannot be written yet is marked ungated rather than asserted, and the size ceilings and duplication thresholds are set to values the reference demonstrably violated rather than to values that feel right.

## Migration Plan

No data migration. Sequencing, and the reason for the order:

1. **Gates before content, but blocking only where the tree can pass.** The link, frontmatter, wikilink and reachability gates are written and demonstrated against violating inputs first, so that every later step in this list is verified as it lands rather than reviewed after it. Each becomes *blocking* only after the step that makes the tree satisfy it — the frontmatter gate after the enumerations are fixed and applied, the reachability gate after the concept notes create the specifications' first inbound links in step 5. An adversarial review found both flips scheduled ahead of the work that satisfies them, which would have put every subsequent step on a red tree and left the gate to be quietly narrowed during application rather than by decision. A gate that cannot pass on the tree it governs is not a gate.
2. **The register merge.** D21–D27 into `design.md`, the collision table recorded, D11–D15 retired, `docs/05-decision-log.md` removed — with the enumeration check proving no unique decision was lost.
3. **The structural move.** The seven essays split across `why/ how/ code/ history/ method/`, the fifteen citing paths repointed, `docs/agents/` deleted, `start-here.md` and the generated indexes created.
4. **The new notes.** Glossary, alternatives, threat model, failure taxonomy, operator view, tenant view, success criteria, research provenance, obtaining-the-reference. The last of these unblocks the citation-obtainability gate for the other 139.
5. **The capability layer.** Sixteen concept notes plus the dependency correspondence check.
6. **The code guide.** Component boundaries, the rule-to-gate correspondence, atomic banned patterns, the two procedures, the language notes, review single-sourcing.
7. **The entry files and the authoring hook.** `CLAUDE.md` rewritten as a router under its ceiling, `AGENTS.md` created, `openspec/config.yaml` populated.
8. **`rebuild-plugboard` reconciled last.** Tasks 1.1, 1.3, 1.4 and 1.10 rewritten via `/opsx:update` against paths that now exist.

**Rollback.** Steps 1 and 2 are the only irreversible ones — a retired decision number stays retired, and the collision table is the artifact that makes that safe. Steps 3 through 8 are file moves and additions under version control, revertible in a single commit.

## Open Questions

- Whether the eighty cross-capability references inside the sixteen specs are eventually linked directly (RDV5). Deferrable because the concept-note layer carries the graph either way, and resolving it changes no requirement here — only whether a later change adds links to files this change does not touch.
- Which size ceiling the concept notes carry. `docs/knowledge-base` requires a declared ceiling, not a particular number; the value is set when the first four notes exist and their natural length is known.
