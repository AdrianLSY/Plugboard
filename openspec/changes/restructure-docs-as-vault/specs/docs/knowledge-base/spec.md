## Purpose

Defines the repository's documentation surface as a single checked artifact: one vault with one spine, a classification every note carries, a link discipline whose resolution is verifiable, an authority precedence that stops a note from stating behaviour a specification owns, and a reachability property that makes "the documentation reflects the current state of the project" a gate rather than a promise. The vault serves two readers with one set of files — a person navigating by link and graph, and an agent retrieving by path — so every obligation here is stated so that both are served by the same artifact rather than by two that drift.

Throughout this capability the *spine* is the directory holding the hand-written notes; a *governed root* is a declared directory whose tracked markdown this capability's obligations apply to; an *exempt root* is a declared directory whose tracked markdown is outside them, with its reason recorded; a *note* is a tracked markdown file under a governed root; an *entry point* is a file an agent or a person is expected to read before any other; and a *gate* is an automated check that fails the build.

Every obligation below states which roots it governs, because the obligations do not share one scope: the spine is hand-written and fully governed, planning artifacts are owned by an external tool and are governed only for reachability and linking, and tool-owned directories are exempt outright. An obligation whose scope is unstated is a defect in this specification, not a licence for the gate to choose.

## ADDED Requirements

### Requirement: The repository is one vault with one spine

The repository SHALL be a single vault whose root is the repository root, and SHALL NOT contain a second vault. The hand-written notes SHALL live under one declared spine directory. Normative specifications, planning artifacts and generated indexes MAY live outside the spine and SHALL be linked to rather than copied into it.

The declared set SHALL name, in one retrievable location, every governed root and every exempt root, and SHALL be closed: a tracked markdown file under neither SHALL fail the gate, which SHALL name the offending path and the declared set.

The governed roots SHALL comprise the spine, the declared planning directories, and the declared per-component directories. An exempt root SHALL carry a recorded reason for its exemption, and the reason SHALL state what owns the files instead. Exemption SHALL be a declaration in the same location as the roots, never a property of a scanning tool's configuration — a directory omitted from a gate's traversal without being declared exempt SHALL fail the gate. Each gate SHALL report which roots it excluded from its run, so that a passing result states its own coverage rather than implying total coverage.

Vault reader configuration SHALL be tracked for the settings that change how links resolve and how notes are classified, and SHALL NOT be tracked for per-person workspace state or caches.

#### Scenario: A note outside every declared root is refused

- **WHEN** a tracked markdown note is added at a path covered by no declared root
- **THEN** the gate fails
- **AND** the failure names the offending path and the declared set

#### Scenario: A tracked file under an exempt root is not a note

- **WHEN** a tracked markdown file exists under a declared exempt root
- **THEN** no obligation of this capability applies to it
- **AND** the gate reports that root among the roots it excluded

#### Scenario: An undeclared exclusion is refused

- **WHEN** a gate omits a directory from its traversal and that directory is declared neither governed nor exempt
- **THEN** the gate fails
- **AND** the failure names the directory and requires it be declared

#### Scenario: A passing gate states its coverage

- **WHEN** a gate passes
- **THEN** its output names the roots it covered and the roots it excluded

#### Scenario: Content is not duplicated between the spine and the specifications

- **WHEN** a note in the spine and a specification both contain the same requirement text
- **THEN** the gate fails
- **AND** the failure names both locations

#### Scenario: Per-person reader state is not tracked

- **WHEN** the vault reader writes per-person workspace state or a cache
- **THEN** the change does not appear as a tracked modification

### Requirement: Every note carries a classification

Every note under the spine and under a declared per-component root SHALL carry frontmatter declaring its `type`, its `status`, and its `authority`. Each field SHALL take a value from a closed enumeration, and each enumeration SHALL be retrievable from a single location, and each enumeration SHALL name the note classes it covers so that a note class with no assigned value is a failure rather than a judgement call.

The declared planning directories are outside this requirement. Their files are authored and validated by an external tool that owns their format, so this capability governs their links and their reachability but not their frontmatter. That exclusion SHALL be stated in the declared set alongside the roots, with this as its recorded reason — it is a scope decision, not a concession to the tool's current behaviour.

`authority` SHALL distinguish a note that carries no authority from one carrying rationale, one carrying a decision in force, and one carrying normative behaviour. A note in the spine SHALL NOT declare normative authority.

The classification SHALL be limited to fields that a gate or a generated index reads. A field that no gate and no index reads SHALL NOT be introduced.

#### Scenario: Missing frontmatter is refused

- **WHEN** a note is added with no frontmatter, or with frontmatter missing any required field
- **THEN** the gate fails
- **AND** the failure names the note and every missing field at once

#### Scenario: A value outside the enumeration is refused

- **WHEN** a note declares a `type`, `status` or `authority` value absent from the enumeration
- **THEN** the gate fails
- **AND** the failure names the offending value and the permitted set

#### Scenario: A spine note claiming normative authority is refused

- **WHEN** a note in the spine declares normative authority
- **THEN** the gate fails

#### Scenario: A planning artifact is not required to carry a classification

- **WHEN** a file under a declared planning directory carries no frontmatter
- **THEN** the classification gate does not fail
- **AND** the link and reachability gates still cover that file

#### Scenario: A note class with no assigned value is refused

- **WHEN** a note class exists for which the enumeration assigns no `type`, `status` or `authority` value
- **THEN** the gate fails
- **AND** the failure names the note class and the field with no value

#### Scenario: An unread field is refused

- **WHEN** a frontmatter field is introduced that no gate and no index generator reads
- **THEN** the gate fails

### Requirement: Relations are relative markdown links

A relation between notes SHALL be expressed as a relative markdown link to a file path. Wiki-style link syntax and transclusion syntax SHALL NOT appear in a tracked note.

A relation SHALL NOT be expressed only as a frontmatter identifier list. Where a relation exists, it SHALL be expressed as a link in the note body, so that the same relation is followed by a person reading the rendered file, an agent resolving a path, and the vault reader's backlink view.

#### Scenario: Wiki-style link syntax is refused

- **WHEN** a tracked note contains wiki-style link or transclusion syntax
- **THEN** the gate fails
- **AND** the failure names the note, the line, and the equivalent markdown form

#### Scenario: An absolute or reader-specific link is refused

- **WHEN** a tracked note links to another note by absolute filesystem path, or by a form that resolves only inside the vault reader
- **THEN** the gate fails

### Requirement: Every link resolves

Every link from a tracked note to a path inside the repository SHALL resolve to an existing file, and every link carrying a fragment SHALL resolve to an anchor present in the target file. A link to a line-numbered location in a tracked file SHALL resolve to a file that exists.

The gate SHALL cover every tracked note, every component README, and the contributor entry files, and SHALL report every unresolved link in one run rather than stopping at the first.

#### Scenario: A link to a nonexistent file fails the gate

- **WHEN** a note links to a repository path that does not exist
- **THEN** the gate fails
- **AND** the failure names the source note, the line, and the unresolved target

#### Scenario: A link to a missing anchor fails the gate

- **WHEN** a note links to a fragment that no heading in the target file provides
- **THEN** the gate fails
- **AND** the failure distinguishes a missing anchor from a missing file

#### Scenario: Every unresolved link is reported at once

- **WHEN** a change introduces more than one unresolved link
- **THEN** the gate names all of them in a single run

### Requirement: Authority precedence is stated and enforced

A single ordered precedence SHALL be stated in one location, ranking the machine-checked contract above the normative specifications, the specifications above the decisions in force, the decisions above the spine's rationale notes, and the rationale notes above any generated index.

A note SHALL NOT state behaviour that a specification owns. Where a note must summarise owned behaviour for orientation, it SHALL mark the summary as non-normative and SHALL link to the owning specification.

Every note in the spine that describes behaviour SHALL declare, at its head, that the owning artifact wins where the two disagree. This obligation is scoped to the spine because a planning artifact is itself an owning artifact and has nothing to defer to.

#### Scenario: An unmarked behavioural summary is refused

- **WHEN** a spine note states behaviour owned by a specification without marking the statement non-normative and linking to that specification
- **THEN** the gate fails
- **AND** the failure names the note and the owning specification

#### Scenario: Precedence is stated once

- **WHEN** the precedence order appears in more than one location with differing content
- **THEN** the gate fails

### Requirement: Every note is reachable from an entry point

Every note, and every *planning artifact* under a declared planning directory, SHALL be reachable by following links from a declared entry point. A file reachable from nothing SHALL fail the gate, whether it is newly added or newly orphaned by a deletion. The entry-point set SHALL be declared in the same retrievable location as the roots.

A planning artifact is a file an author writes: a proposal, a specification, a design, a task list. Metadata a planning tool manages for itself is not a reachability subject, and the distinction SHALL be declared alongside the roots rather than inferred by the gate — a gate that decides for itself which files it will not look at is the defect the declared root set exists to remove.

A planning artifact's inbound link SHALL come from a note rather than from another planning artifact, so that reachability of the normative surface is a property of the vault and not of the planning tool's internal cross-references.

Reachability SHALL be reported as a path from the entry point, so that a contributor is told where the note is missing from rather than only that it is unreachable.

Because a specification's first inbound link is created by its concept note, this gate SHALL NOT be blocking before the obligation that creates those links is in force. A gate that cannot pass on the tree it governs is not a gate; the ordering is stated here so that it is a decision rather than a discovery during application.

#### Scenario: A newly added note that nothing links to is refused

- **WHEN** a note is added and no other note links to it
- **THEN** the gate fails
- **AND** the failure names the note

#### Scenario: A note orphaned by a deletion is refused

- **WHEN** the only note linking to a second note is deleted
- **THEN** the gate fails
- **AND** the failure names the note left unreachable

#### Scenario: Reachability is reported as a path

- **WHEN** the gate passes for a note
- **THEN** the report can state a link path from an entry point to that note

### Requirement: Entry points route rather than carry content

The agent entry files SHALL be routers: each SHALL link into the vault, SHALL name at least one invariant and at least one banned pattern, and SHALL NOT restate framework or language conventions.

Each entry file SHALL be below a declared size ceiling. The ceiling SHALL be enforced by a gate, and the gate SHALL fail on the current content of any entry file that exceeds it.

An entry file SHALL NOT describe a tool, index or artifact that does not exist in the repository.

#### Scenario: An entry file over the ceiling is refused

- **WHEN** an entry file exceeds the declared size ceiling
- **THEN** the gate fails
- **AND** the failure names the file, its size, and the ceiling

#### Scenario: An entry file restating framework conventions is refused

- **WHEN** a framework-conventions section is added to an entry file
- **THEN** the gate fails

#### Scenario: An entry file describing an absent artifact is refused

- **WHEN** an entry file instructs a reader to use a generated index, tool or directory that the repository does not contain
- **THEN** the gate fails
- **AND** the failure names the absent artifact

### Requirement: There is exactly one decision register

A *register* is a location that assigns decision identifiers in the installation's unnamespaced sequence and holds those decisions as being in force. The installation SHALL hold exactly one register, and its location SHALL be named in the same retrievable location as the roots, so that the gate has a declared subject rather than a path convention.

A decision identifier SHALL denote exactly one decision, and an identifier SHALL NOT be reassigned once used, including an identifier whose decision was superseded and an identifier used by a register that has been removed.

A change's own design rationale MAY record decisions of its own, and those SHALL carry an identifier namespaced to that change. A namespaced per-change decision set is not a register. An identifier in the installation's unnamespaced sequence introduced anywhere other than the declared register SHALL fail the gate, whatever file it appears in — including a change's own design artifact, which is the case that would otherwise reproduce the collision this requirement exists to prevent.

Citing an existing identifier is not introducing one. A collision table, a decision note, a task and a specification may all name an identifier the declared register holds.

Where a register is superseded, a collision table SHALL be retained recording every identifier the superseded register used and what it now denotes, so that a citation written against the old register can be resolved rather than guessed at.

A decision recorded in a removed register and nowhere else SHALL be carried into the surviving register before the removal, and the carry SHALL be verifiable by enumeration rather than by inspection.

#### Scenario: A second register is refused

- **WHEN** a second location introduces unnamespaced decision identifiers of its own
- **THEN** the gate fails
- **AND** the failure names both locations

#### Scenario: A change's own unnamespaced decisions are refused

- **WHEN** a change's design artifact numbers its decisions in the installation's unnamespaced sequence
- **THEN** the gate fails
- **AND** the failure names the change and the identifiers it collides with

#### Scenario: A change's namespaced decisions are permitted

- **WHEN** a change's design artifact records decisions under an identifier namespaced to that change
- **THEN** the gate passes
- **AND** those identifiers are not treated as a register

#### Scenario: Citing an identifier is not introducing one

- **WHEN** a note, task or specification names an identifier the declared register holds
- **THEN** the gate passes

#### Scenario: Reusing a retired identifier is refused

- **WHEN** a new decision is assigned an identifier that a superseded register used
- **THEN** the gate fails
- **AND** the failure names the identifier and its former meaning

#### Scenario: An old citation resolves through the collision table

- **WHEN** a reader holds a citation written against the superseded register
- **THEN** the collision table states what that identifier denoted and what it denotes now

#### Scenario: A register cannot be removed while it holds a unique decision

- **WHEN** a register is removed while it records a decision recorded nowhere else
- **THEN** the gate fails
- **AND** the failure names every decision that would be lost

### Requirement: An artifact declared out of scope stays byte-unchanged

Where a change declares a set of artifacts out of its scope, that declaration SHALL be a checked property rather than an intention. A gate SHALL assert that every path in the declared out-of-scope set is byte-unchanged across the change, and the assertion SHALL run as part of the aggregating target so that it is not a closing review step.

This applies with particular force where the instrument used to edit a neighbouring artifact performs a coherence pass across its siblings. A tool that revises a planning artifact and then reconciles the artifacts around it can reach a specification that no task named, so an intention recorded in prose is not a control. The set SHALL be declared in the same retrievable location as the roots.

#### Scenario: An out-of-scope artifact modified by a coherence pass is refused

- **WHEN** a tool revising one planning artifact also modifies a path in the declared out-of-scope set
- **THEN** the gate fails
- **AND** the failure names the path and the change that declared it out of scope

#### Scenario: The assertion runs with the other gates

- **WHEN** the aggregating target runs
- **THEN** the out-of-scope assertion is among the gates it reports

#### Scenario: A needed revision becomes a follow-up rather than an edit

- **WHEN** a coherence pass proposes a revision to an out-of-scope artifact
- **THEN** the revision is refused
- **AND** it is recorded as follow-up work naming the artifact and the proposed revision

### Requirement: A cited artifact is obtainable

Every behavioural claim in a note SHALL carry a citation to a location in a tracked file, a named test, or an artifact for which the vault states how to obtain the exact revision cited.

Where notes cite an artifact that is not tracked in this repository, one note SHALL state how to obtain it and SHALL pin the exact revision the citations were taken against. A citation into an artifact with no such statement SHALL fail the gate.

#### Scenario: A claim with no citation is refused

- **WHEN** a note states a behavioural claim carrying neither a location in a tracked file, nor a test name, nor a citation into an obtainable artifact
- **THEN** the gate fails

#### Scenario: A citation into an unobtainable artifact is refused

- **WHEN** a note cites a location in an artifact for which no note states how to obtain the pinned revision
- **THEN** the gate fails
- **AND** the failure names the artifact

#### Scenario: The pinned revision is stated

- **WHEN** a reader follows the obtaining instructions
- **THEN** the revision they obtain is the revision the citations name

### Requirement: The documentation reflects the current state

A note whose subject has been removed from the repository SHALL be deleted or marked superseded in the same change that removes the subject. A note marked superseded SHALL name what replaced it.

A note SHALL NOT describe a planned artifact as existing. Where a note describes something not yet built, it SHALL be marked as planned and SHALL link to the task or change that builds it. The marker SHALL name its subject as a path the gate can test for existence, so that the marker's own correctness is decidable rather than a matter of reading.

A planned marker SHALL be retired once its subject exists. A note still marked planned whose named subject is present in the tree, or whose linked task is complete, SHALL fail the gate. This direction is stated because it is the one that will be exercised: the spine is marked planned while almost nothing is built, and every marker becomes wrong as the work lands. A currency property enforced only in the direction that is empty today would report green over a vault that had gone stale everywhere.

#### Scenario: A note describing a removed subject is refused

- **WHEN** a change removes a directory, tool or gate and leaves a note describing it as current
- **THEN** the gate fails
- **AND** the failure names the note and the removed subject

#### Scenario: A superseded note names its replacement

- **WHEN** a note's status is superseded
- **THEN** it links to the note that replaced it

#### Scenario: A planned artifact is marked as planned

- **WHEN** a note describes an artifact the repository does not yet contain
- **THEN** it is marked as planned and links to the work that builds it
- **AND** the marker names its subject as a path the gate can test

#### Scenario: A stale planned marker is refused

- **WHEN** a note is marked planned and the subject its marker names now exists in the tree
- **THEN** the gate fails
- **AND** the failure names the note and the subject that now exists

#### Scenario: A planned marker whose work is complete is refused

- **WHEN** a note is marked planned and the task or change its marker links to is complete
- **THEN** the gate fails

#### Scenario: A planned marker naming an untestable subject is refused

- **WHEN** a planned marker names no path the gate can test for existence
- **THEN** the gate fails

### Requirement: Each capability has a concept note

Every capability with a specification SHALL have exactly one concept note in the spine. The note SHALL link to its specification, SHALL link to each capability its specification names as a dependency, and SHALL link to the decisions in force that shaped it.

A concept note SHALL NOT restate its specification's requirements. It SHALL be short enough to be read whole before the specification is opened, under a declared ceiling.

Adding a capability without its concept note, or naming a dependency in a specification without a corresponding link in the concept note, SHALL fail the gate.

#### Scenario: A capability without a concept note is refused

- **WHEN** a specification is added for a capability with no concept note
- **THEN** the gate fails
- **AND** the failure names the capability

#### Scenario: An unlinked dependency is refused

- **WHEN** a specification names a dependency on another capability and the concept note does not link to it
- **THEN** the gate fails
- **AND** the failure names the dependency

#### Scenario: Dependents of a capability are retrievable

- **WHEN** a reader asks which capabilities depend on a given capability
- **THEN** the answer is obtained from links into that capability's concept note without reading any specification

### Requirement: Generated indexes are checked in and cannot drift

An index derived from other notes SHALL be generated by a tool, SHALL be tracked, and SHALL be byte-identical to a fresh regeneration. A generated index SHALL declare that it is generated and name the tool that produces it.

A generated index SHALL NOT be hand-edited, and a hand edit SHALL be detected as drift rather than silently overwritten.

#### Scenario: A stale generated index is refused

- **WHEN** a note changes such that a generated index would differ from its tracked content
- **THEN** the gate fails
- **AND** the failure names the index and the tool that regenerates it

#### Scenario: A hand-edited index is detected

- **WHEN** a generated index is edited by hand
- **THEN** the gate fails as drift

### Requirement: Authoring guidance is applied at authoring time

The conventions this capability imposes SHALL be supplied at authoring time rather than left to review, through **two channels**, because no single channel reaches both authors:

- A **planning-artifact channel**: the location the planning tool reads when it authors a proposal, a specification, a design or a task list, including the guidance that governs its apply and archive operations, since those operations touch the vault far more often than authoring does.
- A **note-authoring channel**: a location an agent or a person authoring a note reads before writing one. The planning tool's configuration SHALL NOT be relied on for this, because its per-artifact guidance is keyed to that tool's own artifact types and cannot express an obligation on a note.

Both channels and the gates SHALL be keyed on one enumeration derived from a single convention source, so that a convention added to the gates without reaching both channels fails, and so that the two channels cannot state different conventions.

#### Scenario: A gate without authoring guidance is refused

- **WHEN** a convention is added to the gates and not to both authoring channels
- **THEN** the gate fails
- **AND** the failure names the convention and the channel missing it

#### Scenario: Guidance reaches the planning workflow

- **WHEN** the planning tool authors a planning artifact
- **THEN** the conventions are present in the context it reads

#### Scenario: Guidance reaches a note author

- **WHEN** an agent or a person begins authoring a note
- **THEN** the conventions are present in a location it reads before writing
- **AND** that location is not the planning tool's configuration

#### Scenario: Guidance reaches the apply and archive operations

- **WHEN** the planning tool runs its apply or archive operation
- **THEN** the conventions governing the vault are present in the guidance it reads

#### Scenario: The two channels cannot diverge

- **WHEN** the two channels state conventions that differ
- **THEN** the gate fails
- **AND** the failure names the convention and both channels
