## Purpose

Defines the code guide as a cited artifact rather than a set of opinions: each component's boundary stated once and only once, a correspondence between every rule and its enforcing gate that holds in both directions, a quarantine that keeps unenforced preference from being mistaken for an obligation, task-shaped entry points that tell a contributor where a feature or a fix belongs before they choose a file, and the project's testing obligations held in the same rule shape as everything else rather than as prose in a methodology note. The organising property is that a rule with no gate is a wish, so this capability makes the absence of a gate visible rather than letting an unenforced rule sit beside an enforced one looking identical. Throughout this capability a *rule* is a single named obligation on how code is written or placed, a *gate* is an automated check that fails the build, a *rule note* is the tracked note stating one rule, and a *component* is a top-level directory holding the source of one deployable or one shared artifact.

## ADDED Requirements

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
