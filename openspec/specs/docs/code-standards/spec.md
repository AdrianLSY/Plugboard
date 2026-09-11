## Purpose

Defines the code guide as a cited artifact rather than a set of opinions: each component's boundary stated once and only once, a correspondence between every rule and its enforcing gate that holds in both directions, a quarantine that keeps unenforced preference from being mistaken for an obligation, task-shaped entry points that tell a contributor where a feature or a fix belongs before they choose a file, and the project's testing obligations held in the same rule shape as everything else rather than as prose in a methodology note. The organising property is that a rule with no gate is a wish, so this capability makes the absence of a gate visible rather than letting an unenforced rule sit beside an enforced one looking identical. Throughout this capability a *rule* is a single named obligation on how code is written or placed, a *gate* is an automated check that fails the build, a *rule note* is the tracked note stating one rule, and a *component* is a top-level directory holding the source of one deployable or one shared artifact.

## Requirements

### Requirement: A component's boundary is stated once

For every component, one note SHALL state what that component owns and what it must not own. That statement SHALL exist in exactly one location; every other location naming the boundary SHALL link to it rather than restate it.

The set of components the guide covers SHALL be keyed on the set of components that exist, so that adding a component without its boundary statement fails, and so that a boundary statement for a component that no longer exists fails.

#### Scenario: A component without a boundary statement is refused

- **WHEN** a component directory is added and no note states its boundary
- **THEN** the gate fails
- **AND** the failure names the component

#### Scenario: A restated boundary is refused

- **WHEN** a second location states a component's boundary rather than linking to the canonical note
- **THEN** the gate fails
- **AND** the failure names both locations

#### Scenario: A boundary statement for a removed component is refused

- **WHEN** a component is removed and its boundary statement remains
- **THEN** the gate fails

#### Scenario: Placement is answerable before a file is chosen

- **WHEN** a contributor asks which component a piece of work belongs in
- **THEN** the boundary notes answer it without reading source

### Requirement: Every rule names its gate, and every gate names its rule

Each rule SHALL be stated in exactly one rule note, and that note SHALL name the gate that enforces it or SHALL be explicitly marked as carrying no gate.

Each gate SHALL name the rule note it enforces, and its failure output SHALL identify that note so that the failure teaches the rule rather than only reporting a violation.

The correspondence SHALL be checked in both directions and keyed on one enumeration: a gate naming no rule note fails, a gate naming a rule note that does not exist fails, and a rule note claiming a gate that does not exist fails.

#### Scenario: A gate with no rule note is refused

- **WHEN** a gate is added that names no rule note
- **THEN** the correspondence check fails
- **AND** the failure names the gate

#### Scenario: A rule note claiming an absent gate is refused

- **WHEN** a rule note names a gate that the repository does not run
- **THEN** the correspondence check fails
- **AND** the failure names the rule note and the claimed gate

#### Scenario: A gate failure identifies its rule note

- **WHEN** a gate fails on a violating input
- **THEN** its output names the rule note stating the rule it enforces

#### Scenario: Adding a rule without a gate or a marker is refused

- **WHEN** a rule note is added that neither names a gate nor carries the no-gate marker
- **THEN** the correspondence check fails

### Requirement: Unenforced rules are quarantined

A rule carrying no gate SHALL be held in a separately identified section or directory, and SHALL be marked as preference rather than obligation.

An unenforced rule SHALL NOT be cited as a blocking objection in review. A gated rule and an unenforced rule SHALL be distinguishable without reading either note in full.

The proportion of rules carrying no gate SHALL be retrievable, so that a guide drifting toward unenforced preference is visible rather than discovered.

#### Scenario: An unenforced rule outside the quarantine is refused

- **WHEN** a rule marked as carrying no gate is placed among the gated rules
- **THEN** the gate fails

#### Scenario: Enforcement status is visible without reading the note

- **WHEN** a reader views the rule index
- **THEN** each rule's enforcement status is stated there

#### Scenario: The unenforced proportion is retrievable

- **WHEN** a contributor asks how many rules carry no gate
- **THEN** the answer is retrievable from the rule index

### Requirement: Each banned pattern is individually addressable

Every banned pattern SHALL have its own rule note with a stable anchor, so that a gate, a review comment, or a specification can cite one pattern rather than a list.

Each banned pattern note SHALL name the defect it prevents and SHALL carry a citation to a location in a tracked file, a named test, or an obtainable artifact demonstrating that defect.

Renaming or moving a banned pattern note SHALL be detected as a broken citation rather than silently breaking every gate and review comment that cited it.

#### Scenario: A banned pattern without an addressable anchor is refused

- **WHEN** a banned pattern is stated without its own stable anchor
- **THEN** the gate fails

#### Scenario: A banned pattern without a demonstrated defect is refused

- **WHEN** a banned pattern note names no defect, or names one with no citation
- **THEN** the gate fails
- **AND** the failure names the pattern

#### Scenario: Moving a pattern note breaks visibly

- **WHEN** a banned pattern note is renamed or moved and a citing gate is not updated
- **THEN** the correspondence check fails
- **AND** the failure names the citing gate

### Requirement: Adding a feature and fixing a bug have stated procedures

The guide SHALL state, as two distinct procedures, the ordered artifacts a contributor touches to add a feature and to fix a bug. Each procedure SHALL name where the change is specified, where it is proven failing before it is fixed, where the code goes, and what must be updated alongside it.

Each procedure SHALL name its own verification, so that a contributor can tell whether they followed it. A procedure SHALL NOT name an artifact, directory or command that does not exist.

The bug procedure SHALL require the failing case be demonstrated before the fix, and SHALL prohibit a test that accommodates the defect or a helper that repairs the state it waits on.

#### Scenario: A procedure naming an absent command is refused

- **WHEN** a procedure names a command, target or directory the repository does not provide
- **THEN** the gate fails
- **AND** the failure names the absent artifact

#### Scenario: A fix without a prior failing case is refused

- **WHEN** a change fixes a defect and adds no case that fails before the fix and passes after it
- **THEN** review refuses the change
- **AND** the refusal names the bug procedure

#### Scenario: A test accommodating a defect is refused

- **WHEN** a test asserts the defective behaviour rather than the intended behaviour
- **THEN** review refuses the change

#### Scenario: A helper repairing awaited state is refused

- **WHEN** a test helper performs the state transition it is written to wait for
- **THEN** review refuses the change

### Requirement: Testing discipline is stated as rules, not as prose

The guide SHALL state the project's testing obligations as rule notes under the same shape as every other rule, so that each names its gate or carries the no-gate marker, appears in the rule index with its enforcement status, and is citable as a blocking objection when gated.

The obligations SHALL cover the test tiers and what each is for, the latency budget that makes the fast tier a correctness control rather than a convenience, the authority of the conformance suite over any implementation's own tests, and what a test may not do.

The prohibitions on test shape SHALL each be their own rule note with its own stable anchor and its own cited defect: a helper that performs the state transition it is written to wait for; a test that asserts defective behaviour rather than the intended behaviour; a security or correctness property weakened or disabled in test configuration; and an uncertainty marker or an unconditional skip standing in for a failing assertion.

These SHALL NOT be held as prose in a methodology note. A prohibition recorded as prose carries no gate, does not appear in the rule index, is not covered by the correspondence check, and therefore cannot be raised as a blocking objection under this capability's own quarantine rule — which would retire four review blockers by relocating them.

#### Scenario: A test-shape prohibition held only as prose is refused

- **WHEN** a prohibition on test shape exists in a note that is not a rule note
- **THEN** the gate fails
- **AND** the failure names the prohibition and the note holding it

#### Scenario: A test-shape prohibition without a cited defect is refused

- **WHEN** a test-shape rule note names no defect, or names one with no citation
- **THEN** the gate fails

#### Scenario: A test-shape prohibition is citable in review

- **WHEN** a reviewer raises one of the test-shape prohibitions as a blocking objection
- **THEN** it cites a rule note that names a gate

#### Scenario: The tiers and their budgets are stated once

- **WHEN** a second location states the test tiers or the fast-tier latency budget
- **THEN** the gate fails
- **AND** the failure names both locations

### Requirement: Every language with tracked source has stated conventions

For every language in which the repository holds tracked source, the guide SHALL state that language's conventions, including its formatter, its linters, its size ceilings, and the constructs banned in it.

The set of languages the guide covers SHALL be keyed on the set of languages present, so that introducing a language without its conventions fails, and conventions for a language no longer present fail.

Language conventions SHALL NOT restate what the language's own formatter or documentation already enforces; the guide's content SHALL be this project's obligations.

#### Scenario: A new language without conventions is refused

- **WHEN** tracked source appears in a language the guide does not cover
- **THEN** the gate fails
- **AND** the failure names the language

#### Scenario: Conventions for an absent language are refused

- **WHEN** the guide covers a language for which no tracked source exists
- **THEN** the gate fails

#### Scenario: Restating formatter-enforced conventions is refused

- **WHEN** a language note states a convention the project's formatter already enforces
- **THEN** the gate fails

### Requirement: Review obligations are single-sourced and enumerated

The review checklist, the questions a change description must answer, and the set of blocking objections SHALL each be stated in exactly one location. Every other location referring to them SHALL link rather than restate.

Each SHALL be keyed on its enumeration, so that adding an item in the canonical location fails every artifact required to name it until that artifact names it.

#### Scenario: Adding a checklist item propagates or fails

- **WHEN** an item is added to the canonical review checklist
- **THEN** the gate fails until every artifact required to enumerate the checklist names it
- **AND** the failure names each artifact still missing it

#### Scenario: A restated checklist is refused

- **WHEN** a second location states the checklist rather than linking to it
- **THEN** the gate fails

#### Scenario: A blocking objection cites a gated rule

- **WHEN** a reviewer raises a blocking objection
- **THEN** it cites a rule note that names a gate

### Requirement: The gates are themselves demonstrated to fail

Every gate this capability requires SHALL have a deliberately violating input held in the repository, and the gate SHALL be demonstrated to fail on it.

A gate that passes on its own violating input SHALL fail the build, so that a gate wired to the wrong flag, path or enumeration is caught rather than trusted.

Each violating input SHALL name the gate it exercises and the rule note that gate enforces.

#### Scenario: A gate that does not fail on its violating input is refused

- **WHEN** a gate is run against its deliberately violating input and does not fail
- **THEN** the build fails
- **AND** the failure names the gate

#### Scenario: A gate without a violating input is refused

- **WHEN** a gate is added with no violating input held in the repository
- **THEN** the build fails
- **AND** the failure names the gate

#### Scenario: A violating input names what it exercises

- **WHEN** a violating input is added
- **THEN** it names its gate and that gate's rule note

### Requirement: Every blocking gate runs without a person's initiative

A tracked runner configuration SHALL exist at the path declared in `ci/vault.json`, and SHALL invoke the aggregating target on every push and every proposed change to the tracked tree, with no path filter, no branch filter, and no clause that lets a non-zero exit pass. The aggregating target SHALL exit non-zero when any gate declared blocking exits non-zero.

The scope is the declared runner configuration and the gates declared blocking in `ci/vault.json`'s `gate_policy`. A gate declared report-only SHALL be invoked by the same target on the same trigger and SHALL report without refusing, so that the difference between blocking and report-only is the consequence and never whether the check ran.

Whether the hosting service refuses a merge is a server-side setting that no tracked artifact states and no check can read. It is out of scope, and this requirement SHALL NOT be read as constraining it. What is checked is that the runner exists, is triggered on both events, and is unfiltered.

#### Scenario: No runner is configured

- **WHEN** no tracked runner configuration exists at the path `ci/vault.json` declares
- **THEN** the build fails
- **AND** the failure names the declared path

#### Scenario: A runner that cannot refuse

- **WHEN** the declared runner configuration carries a path filter, a branch filter, or a clause allowing a non-zero exit to pass
- **THEN** the build fails
- **AND** the failure names the clause

#### Scenario: The aggregating target passes a blocking failure through

- **WHEN** a gate declared blocking exits non-zero
- **THEN** the aggregating target exits non-zero
- **AND** its output names that gate

### Requirement: A generated artifact is verified against something other than its generator

Each generator SHALL be runnable against a tree root other than the repository root, and SHALL have a violating input held in the repository: such a tree, together with the exact output the generator is expected to produce on it, tracked as its own file. A run whose output differs from that tracked expectation SHALL fail the build, naming the generator, the expectation and the first differing line. Each generator SHALL state, in its own module, the class of wrongness its violating input does not reach.

The scope is every tool tracked under `ci/gen/`. The declaration in `ci/vault.json` SHALL be keyed on the tool rather than on the artifact, and SHALL be complete in both directions: a tool under `ci/gen/` the declaration does not name fails, and a named tool that does not exist fails. A tracked artifact carrying a generated-by declaration that neither the generator declaration nor the declared per-directory index scheme names also fails, so that the artifact side cannot stay undeclared while the tool side is satisfied.

Artifacts under a declared scan exclusion are outside this requirement in both directions; they are held deliberately stale.

A generator's violating input is not a gate's violating input. The obligations in "A violating input states the failure it produces" that speak of a gate, a rule note, or a violation count do not apply to it, and generator fixtures SHALL be held outside `ci/broken-inputs/` so that the gate-to-fixture correspondence is not asked to resolve them.

#### Scenario: A generator whose output drifts from its pinned expectation is caught

- **WHEN** a generator's output on its violating input differs from the tracked expectation
- **THEN** the build fails
- **AND** the failure names the generator, the expectation file and the first differing line

#### Scenario: An undeclared generator is refused

- **WHEN** a tool is tracked under `ci/gen/` and the declaration does not name it
- **THEN** the build fails
- **AND** the failure names the tool and the declaration

#### Scenario: A generated artifact no declaration accounts for is refused

- **WHEN** a tracked artifact declares that it was generated and neither the generator declaration nor the declared per-directory index scheme names it
- **THEN** the build fails
- **AND** the failure names the artifact

### Requirement: A violating input states the failure it produces

Each violating tree SHALL carry a machine-readable declaration of what its gate emits against it: the violation count, and one expectation per case the accompanying note claims, each required to match at least one failure line the gate emits. Prose in the accompanying note SHALL NOT be read as that declaration.

A declared count that disagrees with the emitted count, or a declared case expectation that matches no emitted failure, SHALL fail the build naming both numbers or the unmatched expectation, so that a fixture drifting away from the gate it demonstrates is caught rather than read as still current.

Where the count a gate emits against a tree is a function of a declaration that tree does not carry, the tree's declaration SHALL name that declaration, and a disagreement SHALL name it alongside both counts.

A violating input MAY declare further invocations of its own gate, each with the exit status it expects. The check SHALL perform every declared invocation and assert that status. An invocation declares an exit status and SHALL NOT declare a violation count. A flag the gate's own argument handling accepts, shown in the accompanying note and absent from the declaration, SHALL fail, naming the flag and the input.

The scope is every violating tree under `ci/broken-inputs/`, notwithstanding that root's presence in the declared scan exclusions. The unit is the tree, not the directory, because one gate may need more than one scenario. A generator's violating input is outside this requirement.

#### Scenario: A declared violation count that does not match is refused

- **WHEN** a violating tree declares a violation count and its gate emits a different count
- **THEN** the build fails
- **AND** the failure names the declared count and the emitted count

#### Scenario: A declared case that matches no failure is refused

- **WHEN** a violating tree declares an expectation for a case and no failure line the gate emits matches it
- **THEN** the build fails
- **AND** the failure names the unmatched expectation

#### Scenario: A declared invocation is performed

- **WHEN** a violating input declares an invocation of its gate and the expected exit status
- **THEN** the check performs that invocation and asserts that status

#### Scenario: A demonstrated flag that is never declared is refused

- **WHEN** the note accompanying a violating tree shows a flag its gate accepts and the tree's declaration does not declare an invocation using it
- **THEN** the build fails
- **AND** the failure names the flag and the input

### Requirement: A gate's reported coverage is an assertion about the run

Every gate SHALL report, on every run including a passing one, how many subjects it examined, what kind of item it counted, and where that set came from: version control, a directory scan, or a named key in `ci/vault.json`.

The count SHALL be produced by the shared reporter from the subjects a gate registers as it examines them, rather than handed to the reporter as a literal.

A run whose scan root is not a version-control work tree SHALL NOT report version control as its source, and a coverage line claiming it on such a run SHALL fail, naming the gate, the label and the tree.

On each of a gate's violating inputs, the reported count SHALL be at least the number of distinct subjects that run's own failure messages name. A gate that fails about an item its count excludes has examined a subject it did not report, and SHALL fail, naming the gate, the count and the unreported subject.

Where a gate's subject set is empty on the tracked tree because its subjects do not exist yet, the emptiness SHALL be declared in `ci/vault.json` with a reason and the work that ends it; the coverage line SHALL state both; an undeclared empty subject set SHALL fail; and once the named work is complete and the set is still empty, the build SHALL fail so that a declaration cannot outlive its reason. This paragraph governs the run against the tracked tree only — the run the aggregating target makes with no tree argument. A run against a violating input is outside it, and so is an enumeration declared inside one.

The scope is the gates declared blocking in `ci/vault.json`'s `gate_policy`. A gate-shaped module under a declared scan exclusion is a fixture, not a gate. The separate obligation to name the roots covered and excluded is stated in `docs/knowledge-base` and is not restated here.

#### Scenario: A run outside version control claiming version control is refused

- **WHEN** a gate reports version control as its subject source on a run whose scan root is not a version-control work tree
- **THEN** the build fails
- **AND** the failure names the gate, the reported source and the tree

#### Scenario: A gate failing about an unreported subject is refused

- **WHEN** a gate's failure messages name more distinct subjects than its reported count
- **THEN** the build fails
- **AND** the failure names the gate, the count and the unreported subject

#### Scenario: A declared empty subject set passes and is reported

- **WHEN** a gate examines no subjects on the tracked tree and `ci/vault.json` records the reason and the work that ends it
- **THEN** the gate passes
- **AND** its coverage line states that its subject set is empty, the reason, and the work that ends it

#### Scenario: An undeclared empty subject set is refused

- **WHEN** a gate examines no subjects on the tracked tree and no declaration records why
- **THEN** the build fails
- **AND** the failure names the gate

#### Scenario: A declaration that has outlived its reason is refused

- **WHEN** a gate's declared emptiness names work that is complete and the gate's subject set is still empty
- **THEN** the build fails
- **AND** the failure names the gate and the completed work

#### Scenario: A coverage line names the kind of item counted

- **WHEN** a gate reports its coverage
- **THEN** the line names the kind of item counted rather than assuming files

### Requirement: A published enumeration and the computed one are reconciled

Where one set is resolved twice by encodings that do not read each other, the pair SHALL be declared in `ci/vault.json` as a named correspondence, naming each side and how its members are resolved. A side whose members a gate computes SHALL expose those members under the name the declaration gives; a reconciliation that re-derives a side for itself is a third encoding of the set and SHALL NOT stand in for the one the gate uses.

Each declared correspondence SHALL be checked in both directions, and a divergence SHALL fail naming the members that differ and both sides, not only the counts.

The declared set SHALL include the rule set — the rule notes the rule-to-gate correspondence holds, against the rows the rule index publishes — and the blocking-gate classification against the gate modules the repository runs. The generated-artifact set is stated under "A generated artifact is verified against something other than its generator" and is not restated here.

This requirement governs the whole tracked tree. The declared exempt roots and scan exclusions are outside every correspondence, and the run SHALL name them among the roots it excluded. A side that resolves to nothing, and a resolver that cannot run, SHALL be reported as a failure and never raised as a crash. An artifact stating a cardinal without naming its members is not a side. A correspondence closed by collapsing both sides onto one resolver SHALL be retired from the declaration, recording that resolver as the reason.

#### Scenario: A published set omitting a computed member is refused

- **WHEN** one side of a declared correspondence holds a member the other omits
- **THEN** the build fails
- **AND** the failure names the omitted member and both sides

#### Scenario: A declared blocking entry corresponding to no module is refused

- **WHEN** the blocking classification names an entry that corresponds to no gate module the repository runs
- **THEN** the build fails
- **AND** the failure names the entry

#### Scenario: A resolver that cannot run is reported rather than crashing

- **WHEN** a declared side's resolver raises or resolves to nothing
- **THEN** the build fails with a failure naming the side and its resolver
- **AND** the run does not terminate with an unhandled error

#### Scenario: A correspondence whose sides have been unified is retired

- **WHEN** both sides of a declared correspondence are resolved by one resolver
- **THEN** the declaration is required to record that resolver as the reason and retire the correspondence
