## Purpose

Defines gate soundness as a checked property rather than an assumed one: that the gates are executed by something other than a person's initiative, that a generator is held to a pinned expectation instead of to its own re-run, that a violating input declares the failure it demonstrates, that a coverage line is an assertion about the run rather than narrative, and that two encodings of one set are reconciled rather than left to diverge. The organising property is that a check nobody runs and a check that examines nothing are indistinguishable from no check at all, so this capability makes the absence of enforcement visible the way `docs/code-standards` already makes the absence of a gate visible. Throughout, *the declared location* is `ci/vault.json`; a *gate* is a module under `ci/gates/` that the aggregating target invokes; a *generator* is a tool under `ci/gen/` that produces a tracked artifact; a *violating tree* is a deliberately broken tree held in the repository to demonstrate one gate; and a *subject* is one item a gate registers as it examines it.

## ADDED Requirements

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
