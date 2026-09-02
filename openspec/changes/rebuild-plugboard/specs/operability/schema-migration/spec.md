## Purpose

Defines how the shape of the durable state is versioned, changed, and validated, so that the guarantees the wire contract makes across version skew have an equivalent for durable state. The wire contract exists because sidecars run in tenants' infrastructure and are never force-upgraded: it carries an explicit version, negotiates a compatible one, refuses rather than guesses, and changes additively. Durable state has the same exposure in a different direction — the operator's own fleet is upgraded instance by instance, so more than one code version operates against one durable state during every deployment, and a projection rebuilt from that state must remain correct throughout. This capability is the counterpart: a version recorded in the state itself, a declared compatibility range, ordered and recorded migrations, and a decomposition rule that keeps the system correct at every intermediate point of an upgrade rather than only at its endpoints.

## ADDED Requirements

### Requirement: The durable schema carries its own version

The durable state SHALL carry a record of the schema version it is at. That version SHALL be read from the durable state itself and SHALL NOT be inferred from the version of the running code, from which migrations are present in the running build, from the presence or absence of any particular stored attribute or collection, or from a value supplied in configuration. This is the durable-state counterpart of the wire contract's obligation that the negotiated version be carried explicitly in the establishment declaration rather than derived from the transport's own handshake.

There SHALL be exactly one authoritative version record for an installation's durable state. Where none is found, and where more than one is found, the state SHALL be treated as unreadable rather than reconciled to a default or to the highest value present, and each of those two conditions SHALL be distinguishable from the other, from an empty state that has never been initialised, and from a state at a version outside the supported range.

The current schema version SHALL be readable by an operator from the component's operational surface alongside its build provenance, without reading the durable state directly.

#### Scenario: The version is read from the state, not from the build

- **WHEN** two builds declaring different code versions are started against one durable state
- **THEN** both report the same schema version
- **AND** neither derives it from its own version or from the migrations present in it

#### Scenario: Configuration cannot assert the version

- **WHEN** a component is started with a configured value naming a schema version different from the one recorded in the durable state
- **THEN** the recorded version is the one used for every compatibility decision
- **AND** the component does not operate as though the configured value were true

#### Scenario: An absent version record is distinguishable from an empty state

- **WHEN** a component is started against a durable state that holds data but no version record
- **THEN** it refuses to start with a cause naming an unversioned durable state
- **AND** that cause is distinct from the one produced for a state that has never been initialised
- **AND** no migration is applied to the unversioned state

#### Scenario: More than one version record makes the state unreadable

- **WHEN** the durable state is found to carry two version records
- **THEN** the component refuses to start with a cause naming an ambiguous schema version
- **AND** it does not select the higher, the lower, or the most recently written of them
- **AND** the state is left unmodified

#### Scenario: The version is on the operational surface

- **WHEN** an operator inspects a running component
- **THEN** the current schema version, the set of migrations applied, and any migration not yet applied are reported
- **AND** they are reported together with the component's build identity

#### Scenario: An unparseable version record is refused distinctly

- **WHEN** the version record is present but not in a form the running code can interpret
- **THEN** the component refuses to start with a cause distinct from an absent record and from an out-of-range version
- **AND** it does not treat the uninterpretable value as the lowest or highest version it knows

### Requirement: An empty durable state is initialised only when it is provably empty

A durable state that has never been initialised SHALL be initialised by applying the full ordered set of migrations, and the version record SHALL be written as part of that initialisation so that a subsequent start reads it rather than inferring it. Initialisation SHALL be reported distinguishably from a migration of an existing state.

Emptiness SHALL be established positively, not inferred from a failure. A durable state that cannot be reached, cannot be read, is readable only in part, or returns an error where the version record would be SHALL NOT be treated as never initialised, and SHALL NOT be initialised. A state holding any data whatsoever, with or without a version record, SHALL NOT be initialised; that condition is the unversioned state this capability refuses. Where several instances start simultaneously against a never-initialised state, initialisation SHALL occur once, under the same exclusion that governs a migration.

Whether a component initialises a never-initialised state on start SHALL be a declared property of how it was invoked rather than an implicit consequence of the state being empty, and a component that does not initialise SHALL refuse to start naming an uninitialised durable state rather than serving against it.

#### Scenario: A never-initialised state is initialised and records its version

- **WHEN** a component invoked to initialise starts against a durable state that has never been initialised
- **THEN** the full ordered set of migrations is applied
- **AND** the version record is written as part of that initialisation
- **AND** a subsequent start reads that recorded version rather than inferring it

#### Scenario: An unreachable store is not mistaken for an empty one

- **WHEN** a component invoked to initialise starts while the durable state cannot be reached or the version record cannot be read
- **THEN** nothing is initialised
- **AND** it refuses with the unreachable-durable-state cause rather than the never-initialised one
- **AND** no migration is applied

#### Scenario: A state holding data is never initialised

- **WHEN** a durable state holds data but carries no version record
- **THEN** it is not initialised
- **AND** the refusal names an unversioned durable state
- **AND** the data it holds is unchanged

#### Scenario: Simultaneous initialisation happens once

- **WHEN** several instances invoked to initialise start at once against a never-initialised durable state
- **THEN** the set of migrations is applied once
- **AND** exactly one completion entry exists for each

#### Scenario: A component that does not initialise refuses rather than serves

- **WHEN** a component not invoked to initialise starts against a never-initialised durable state
- **THEN** it refuses to start naming an uninitialised durable state
- **AND** it accepts no connection on any listener, tunnel endpoint, or probe surface
- **AND** it writes nothing to the durable state

### Requirement: Every durable store the installation holds is versioned and they are checked together

Where the installation keeps durable state in more than one store — at minimum the store holding routing and tenancy state, the store holding credential state, and any store holding shared cryptographic material — each SHALL carry its own version record, its own recorded set of applied migrations, and its own declared supported range, by every obligation of this capability. A version record in one store SHALL NOT be taken as describing another.

Compatibility SHALL be established for every such store before the component serves, and a component SHALL NOT begin serving on the strength of some stores validating while another did not. Where the installation declares a combination of store versions it supports and the versions found are not such a combination, the component SHALL refuse with a cause naming which stores disagree, and SHALL NOT reconcile them by migrating one to match another, by choosing the lowest or highest, or by proceeding against the subset that agrees.

Each store SHALL be separately identified wherever a version, an applied set, or a refusal cause is reported, so that an operator can tell which store is at which version without inferring it.

#### Scenario: Each store reports its own version

- **WHEN** an operator inspects a running component
- **THEN** the version and applied set of every durable store the installation holds are reported
- **AND** each is attributed to the store it belongs to

#### Scenario: One incompatible store refuses the whole component

- **WHEN** every store but one is at a supported version and one is outside the declared range
- **THEN** the component refuses to start
- **AND** the refusal names that store
- **AND** it does not serve the operations that depend only on the stores that validated

#### Scenario: Disagreeing stores are not reconciled

- **WHEN** the versions found across the stores are not a combination the installation declares it supports
- **THEN** the component refuses with a cause naming which stores disagree
- **AND** no store is migrated to match another
- **AND** neither the lowest nor the highest version present is adopted

#### Scenario: A version record does not describe another store

- **WHEN** one store carries a version record and another carries none
- **THEN** the store carrying none is treated as unversioned or never initialised on its own terms
- **AND** the other store's version record is not taken as describing it

#### Scenario: Migrations of one store do not appear in another's history

- **WHEN** a migration is applied to one store
- **THEN** it appears in that store's recorded applied set
- **AND** it appears in no other store's applied set

### Requirement: The recorded version is validated against the state it describes

The recorded schema version SHALL be validated against the actual shape of the durable state before the component operates on it. A state whose recorded version claims a version whose obligations the state does not satisfy SHALL be refused with a cause naming a version-to-shape mismatch, distinguishable from a version outside the supported range and from an absent version record.

The component SHALL NOT repair such a mismatch by inference: it SHALL NOT apply migrations to bring the shape into line with the claim, SHALL NOT lower the recorded version to match the shape, and SHALL NOT proceed on the parts of the state that do validate. Validation SHALL cover the store-level enforcement obligations of the version, not only the presence of stored attributes and collections.

#### Scenario: A version claim contradicted by the shape is refused

- **WHEN** the recorded version names a version whose stored attributes are not all present in the state
- **THEN** the component refuses to start naming a version-to-shape mismatch
- **AND** the cause is distinct from an out-of-range version

#### Scenario: A mismatch is not repaired silently

- **WHEN** a version-to-shape mismatch is detected
- **THEN** no migration is applied
- **AND** the recorded version is not rewritten
- **AND** the durable state is unchanged after the refusal

#### Scenario: Missing enforcement counts as a mismatch

- **WHEN** the state carries every stored attribute the recorded version defines but is missing a store-level enforcement obligation that version requires
- **THEN** validation fails
- **AND** the refusal names the missing enforcement

#### Scenario: Validation is not partial

- **WHEN** the shape of one part of the durable state contradicts the recorded version and the rest agrees with it
- **THEN** the component refuses to start
- **AND** it does not begin serving the parts that validated

#### Scenario: Validation happens before use, not on first access

- **WHEN** a component is started against a state whose shape contradicts its recorded version
- **THEN** the refusal occurs before any listener, tunnel endpoint, or probe surface accepts a connection
- **AND** it does not occur first as the failure of a lookup or a mutation

### Requirement: The running code declares a supported schema version range

The running code SHALL declare the inclusive lowest and highest schema versions it can operate against, and SHALL be able to operate against every version between them. This is the direct analogue of tunnel contract version negotiation, with one asymmetry stated explicitly: a tunnel with no overlapping version is refused per connection and the rest of the system continues, whereas there is one durable state and no per-connection alternative, so a version outside the range refuses the component's startup entirely.

A recorded version above the declared highest SHALL be refused with a cause naming durable state newer than the running code. A recorded version below the declared lowest SHALL be refused with a cause naming durable state older than the supported window. The two causes SHALL be distinguishable from each other, from a version-to-shape mismatch, and from any configuration or credential failure. A version the code does not know SHALL NOT be treated as compatible with any version it does know, and an unknown higher version SHALL NOT be operated against as though it were the highest known one.

The declared range SHALL be a property of the build, readable by an operator from the running component, and SHALL NOT be widenable at runtime: no configured value SHALL permit operating against a version outside it, and no setting SHALL accept any version whatsoever. A declaration whose highest is below its lowest SHALL be refused with a cause distinct from every other cause in this requirement.

That the same range is also readable from the component's artifact while it is stopped, that the artifact's declaration and the running component's must be identical, and that a release is gated on both, are `operability/packaging`'s obligations and are not restated here. This requirement owns what the running code does with the range and with a recorded version outside it.

#### Scenario: A version inside the range is operated against

- **WHEN** the recorded schema version lies between the declared lowest and highest inclusive
- **THEN** the component starts
- **AND** it records the recorded version and its declared range

#### Scenario: State newer than the code is refused

- **WHEN** the recorded version is above the declared highest
- **THEN** the component refuses to start naming durable state newer than the running code
- **AND** it performs no write to the durable state
- **AND** the cause is distinct from state older than the window

#### Scenario: State older than the window is refused

- **WHEN** the recorded version is below the declared lowest
- **THEN** the component refuses to start naming durable state older than the supported window
- **AND** it does not attempt to migrate the state forward from outside the window

#### Scenario: An unknown higher version is not assumed compatible

- **WHEN** the recorded version is above every version the running code knows
- **THEN** the component refuses to start
- **AND** it does not operate against the state as though it were at the highest version the code knows

#### Scenario: No setting widens the range

- **WHEN** a component is started with configuration attempting to permit a schema version outside its declared range
- **THEN** the configuration is rejected as invalid
- **AND** the component still refuses to operate against the out-of-range version

#### Scenario: An inverted declared range is a defect

- **WHEN** a build declares a highest supported schema version below its lowest
- **THEN** it refuses to start with a cause naming a malformed version declaration
- **AND** that cause is distinct from every out-of-range cause

#### Scenario: Every version in the range is genuinely supported

- **WHEN** each schema version between a build's declared lowest and highest inclusive is presented to it in turn
- **THEN** the build starts and serves correctly against each
- **AND** a version inside the declared range that it cannot serve against is reported as a defect rather than as an incompatible state

### Requirement: Schema compatibility is established before anything is served

The schema version check, the shape validation, and the determination of whether any migration is outstanding SHALL be performed before any listener, tunnel endpoint, or probe surface accepts a connection, and SHALL NOT be deferred to the first lookup, the first mutation, or the first tunnel establishment. These checks SHALL be reported within the single startup validation pass the observability capability owns, in the same refusal that names every other failing startup item; this capability SHALL NOT introduce a second validation pass, a second refusal, or a second ordering relative to it.

Where the durable state cannot be reached or read at all, the component SHALL refuse to start with a cause naming an unreachable durable state, distinguishable from every incompatibility cause this capability defines. It SHALL NOT start on the assumption that a state it could not read is compatible, is empty, or is at any particular version.

A component that started successfully SHALL NOT assume the schema version is fixed for its lifetime. Where the recorded version changes underneath a running component to one outside its declared range, or where the version it validated against no longer matches the state, the component SHALL withdraw readiness and cease accepting new work rather than continuing to read and write state it may misread, and SHALL surface the condition with the version it validated against and the version now recorded. That withdrawal SHALL proceed through the single withdrawal lifecycle the sidecar-registry capability owns, with no second ordering of phases and no second deadline introduced here.

#### Scenario: Refusal precedes accepting anything

- **WHEN** a component refuses to start because the schema version is outside its declared range
- **THEN** no listener, tunnel endpoint, or probe surface accepted a connection at any point
- **AND** no exchange was served

#### Scenario: The schema failure is named alongside other failing items

- **WHEN** a component is started with an out-of-range schema version and several unrelated configuration items missing
- **THEN** one refusal names the schema incompatibility and every failing configuration item together
- **AND** a subsequent start with the configuration corrected still names the schema incompatibility

#### Scenario: The check is not deferred to first use

- **WHEN** a component is started against an incompatible schema version and receives no traffic
- **THEN** the incompatibility is already reported
- **AND** it is not discovered later by a failing lookup

#### Scenario: A version change under a running component withdraws readiness

- **WHEN** the recorded schema version is advanced beyond a running component's declared highest while it is serving
- **THEN** that component reports itself not ready and stops accepting new exchanges
- **AND** it surfaces both the version it validated against and the version now recorded
- **AND** it does not continue to write to the durable state

#### Scenario: In-flight work follows the ordinary withdrawal lifecycle

- **WHEN** readiness is withdrawn because the schema version changed underneath a running component
- **THEN** exchanges and streams already dispatched are treated under the phases and the single deadline of the ordinary planned-withdrawal lifecycle
- **AND** none is left with no outcome recorded
- **AND** no deadline other than that lifecycle's is applied to them

#### Scenario: An unreachable durable state is not reported as an incompatibility

- **WHEN** a component is started while the durable state cannot be reached
- **THEN** it refuses to start with a cause naming an unreachable durable state
- **AND** that cause is distinct from an out-of-range version, a version-to-shape mismatch, and an absent version record
- **AND** it does not start on the assumption that the state is empty or at any particular version

#### Scenario: A partially readable state is not treated as compatible

- **WHEN** the version record is readable but the parts of the durable state the shape validation must inspect are not
- **THEN** the component refuses to start naming what it could not read
- **AND** it does not report the version as validated

### Requirement: Readiness and degraded state reflect migration progress

An instance with an outstanding migration, or one on which a migration is in progress, SHALL report itself not ready to receive new traffic while that holds, and its liveness signal SHALL continue to report success. The condition SHALL be contributed as an entry to the single enumerable inventory of degraded conditions the observability capability owns, rather than surfaced through a mechanism of this capability's own, and SHALL name migration state as the cause distinguishably from stale routing state, an unreachable durable store, and an unreachable credential store.

Readiness SHALL be restored without a restart once the migration has completed and the projections it obliges to be rebuilt have been rebuilt. An incomplete data-shaping step that the system is designed to serve traffic alongside SHALL nevertheless be enumerable as an in-progress condition for as long as it is incomplete, so that "the backfill never finished" is visible rather than inferred from behaviour.

#### Scenario: An outstanding migration withdraws readiness

- **WHEN** an instance starts against a durable state with a migration not yet applied
- **THEN** its readiness signal reports failure
- **AND** its liveness signal reports success
- **AND** the cause reported names migration state

#### Scenario: The condition is enumerable while it holds

- **WHEN** a migration has been running for some time
- **THEN** an operator inspecting the instance finds the condition listed with the time it began
- **AND** finding it does not require locating the record emitted when it began

#### Scenario: The cause is distinguishable from stale routing state

- **WHEN** an instance is not ready because a migration is outstanding
- **THEN** the reported cause is distinct from the cause reported for routing state beyond its staleness bound
- **AND** an operator can tell the two apart without correlating other signals

#### Scenario: Readiness returns without a restart

- **WHEN** the migration completes and the projections it obliges to be rebuilt are rebuilt
- **THEN** the instance reports itself ready again
- **AND** no restart was required

#### Scenario: An unfinished data-shaping step stays visible

- **WHEN** a data-shaping step that traffic is served alongside stops making progress before completing
- **THEN** it remains enumerable as an in-progress condition
- **AND** the condition states when it began and that it has not completed

### Requirement: Schema changes are additive by default

Introducing a stored attribute, a stored collection, an enforcement constraint that no existing state violates, or an enumerated value SHALL NOT require any code version inside the current support window to change. This mirrors the wire contract's rule that introducing a field, frame kind, error code, or capability name requires no existing implementation to change.

Code encountering a stored attribute or collection it does not recognise SHALL NOT act on it, SHALL record it, and — the obligation the wire contract's relay rule corresponds to — SHALL preserve it unchanged across any write it makes to the same subject, so that a write by an older instance does not erase a value a newer instance depends on. Tolerance of the unknown SHALL NOT extend to the known: a stored attribute the recorded version defines, carrying a value outside the range that version defines for it, SHALL be rejected with an enumerated cause and SHALL NOT be ignored, defaulted, or clamped.

A change that cannot be made additively SHALL require a new schema version, a declared sequence of intermediate steps, and a documented period during which both the prior and the new shape are readable and writable. Each schema version SHALL record which code versions remain compatible with it, and each code version SHALL record which schema versions it supports.

#### Scenario: An older instance preserves an attribute it does not know

- **WHEN** an instance of a code version that predates a stored attribute writes to a subject that carries a value in it
- **THEN** the value is unchanged after that write
- **AND** an instance of the newer code version reads the same value it wrote

#### Scenario: An unknown attribute is recorded, not acted on

- **WHEN** an instance encounters a stored attribute its version does not define
- **THEN** it serves the operation normally
- **AND** it records that it encountered an unrecognised attribute
- **AND** it takes no behaviour from its value

#### Scenario: An invalid known value is rejected, not clamped

- **WHEN** a stored attribute the recorded version defines carries a value outside the range that version defines
- **THEN** the read or the mutation depending on it is refused with an enumerated cause
- **AND** the value is not defaulted, clamped, or treated as absent

#### Scenario: A non-additive change requires a version and a sequence

- **WHEN** a change cannot be expressed additively
- **THEN** it is expressed as a new schema version with a declared sequence of intermediate steps
- **AND** a period is documented during which both shapes are readable and writable
- **AND** it is not applied as a single step

#### Scenario: Compatibility is recorded in both directions

- **WHEN** a schema version is released
- **THEN** the code versions that remain compatible with it are recorded
- **AND** each code version's supported schema range is recorded
- **AND** an operator can determine, for a given pair, whether they are compatible without running them together

### Requirement: Applying a migration is an operator action and is never reachable from tenant traffic

Applying, undoing, confirming, ordering, or ending a migration SHALL be an operator action performed against an operational surface, authorised against an operator principal, and recorded to that principal. No such action SHALL be reachable through any mount, through any tunnel, or through any surface that serves tenant traffic, and where a migration surface is exposed on a hostname that also serves tenant traffic its path SHALL be contributed to the single reserved-path enumeration the mount-point capability owns rather than protected by a check of this capability's own.

No value originating in tenant-supplied input SHALL select which migration is applied, order the migrations, satisfy a confirmation this capability requires, or cause a migration to begin, resume, or end. A request bearing such a value SHALL be served as ordinary traffic with no migration effect whatsoever.

An unauthorised attempt at a migration action SHALL be refused, SHALL be recorded, and SHALL disclose nothing about which migrations exist, which are outstanding, or what the durable state contains.

#### Scenario: A mount cannot reach the migration surface

- **WHEN** a request whose path would address the migration surface arrives for a mount
- **THEN** no migration is applied, resumed, or ended
- **AND** the request is served as ordinary traffic or refused as ordinary traffic
- **AND** no frame for it causes a migration effect

#### Scenario: Tenant input cannot name a migration

- **WHEN** a tenant-supplied value naming a migration identifier is carried in a request, a header field, or a body
- **THEN** no migration is selected, begun, resumed, or ended on the strength of it
- **AND** it does not satisfy any confirmation this capability requires

#### Scenario: A migration action requires an operator principal

- **WHEN** a migration action is attempted without an authorised operator principal
- **THEN** it is refused
- **AND** the durable state is unchanged
- **AND** the attempt is recorded

#### Scenario: An unauthorised attempt discloses nothing

- **WHEN** an unauthorised principal requests the set of outstanding migrations
- **THEN** the refusal names no migration, no tenancy, and no attribute of the durable state
- **AND** the refusal for an installation with outstanding migrations is indistinguishable from one with none

#### Scenario: The acting operator is recorded

- **WHEN** an operator applies a migration
- **THEN** the record of that application names that operator principal
- **AND** the action is attributable to them rather than to the component

### Requirement: Every migration has a stable identity and one total order

Each migration SHALL carry an identifier that is stable, unique within an installation's history, and never reused. The migrations SHALL have one total order that is identical on every installation and independent of the order in which they were authored, discovered, or received by a build.

A migration whose position in that order precedes one already applied SHALL NOT be applied silently: the condition SHALL be refused or reported with a cause naming out-of-order arrival, so that two migrations authored independently cannot come to be applied in different relative orders on different installations. Renumbering or reordering a migration after it has been released SHALL be refused.

#### Scenario: The order is identical across installations

- **WHEN** the same set of migrations is applied to two independently initialised durable states
- **THEN** they are applied in the same order in both
- **AND** both reach the same recorded schema version

#### Scenario: Authoring order does not set application order

- **WHEN** two migrations are authored in one order and delivered to a build in the other
- **THEN** they are applied in the declared total order
- **AND** the result does not depend on delivery order

#### Scenario: An out-of-order arrival is reported, not absorbed

- **WHEN** a build contains a migration whose position precedes one already recorded as applied
- **THEN** the condition is reported with a cause naming out-of-order arrival
- **AND** the migration is not applied silently ahead of or behind the recorded set

#### Scenario: Identifiers are never reused

- **WHEN** a migration is authored with an identifier that already appears in the recorded history
- **THEN** it is refused with a cause naming a duplicate identifier
- **AND** neither the existing record nor the state is modified

#### Scenario: Reordering after release is refused

- **WHEN** a released migration's position in the total order is changed
- **THEN** the change is refused
- **AND** the refusal names the released migration whose order would move

### Requirement: A released migration is immutable

Once a migration has been released, its content SHALL be fixed. The recorded set of applied migrations SHALL record an identity of each migration's content as well as its identifier, and a migration whose content differs from what was recorded as applied SHALL be reported with a cause naming an altered migration, distinguishable from a migration that is recorded as applied but absent from the running build, and from one present in the build but not yet applied.

Correcting a released migration SHALL be done by authoring a further migration, never by editing the released one. This is what makes the recorded history evidence of what a given installation actually did, rather than a description of the current design that happens to be expressed as a sequence.

#### Scenario: An altered migration is detected

- **WHEN** a component starts against a state whose recorded history names a migration whose content in the running build has since changed
- **THEN** the condition is reported with a cause naming an altered migration
- **AND** the component refuses to serve until the condition is resolved

#### Scenario: A missing applied migration is distinguishable

- **WHEN** the recorded history names a migration that the running build does not contain
- **THEN** the cause reported is distinct from an altered migration and from an unapplied one
- **AND** the state is unmodified

#### Scenario: Correction is a new migration

- **WHEN** a released migration is found to be wrong
- **THEN** the correction is expressed as a further migration with its own identifier
- **AND** the released migration's content and recorded identity are unchanged

#### Scenario: Two installations reporting the same history hold the same schema

- **WHEN** two installations report the same identifiers with the same content identities in the same order
- **THEN** the schema each holds is identical in stored attributes, collections, enforcement, and defaults
- **AND** an installation whose recorded history was altered to match another's is reported as carrying an altered migration rather than as agreeing with it

### Requirement: Each migration is applied at most once and the applied set is recorded durably

The set of migrations that have been applied SHALL be recorded in the durable state it describes, not in the running code, in configuration, or in an external record. For each, the record SHALL state at minimum its identifier, its content identity, when application began, when it completed, its duration, the build that applied it, and its outcome.

Each migration SHALL be applied at most once. An attempt to apply a migration already recorded as applied SHALL make no change to the durable state and SHALL be reported as applying nothing rather than as a failure. The record and the effect SHALL not be able to disagree in a way that hides either: a completed effect SHALL NOT be left recorded as unapplied, and a recorded completion SHALL NOT exist for an effect that did not complete.

The record SHALL be append-only. Removing or amending an entry in order to cause a migration to be applied again SHALL be refused, and re-application where genuinely required SHALL be expressed as a new migration.

#### Scenario: Re-running applies nothing

- **WHEN** the migration process is run against a durable state already at the newest version the build knows
- **THEN** no migration is applied
- **AND** the outcome reports that nothing was outstanding
- **AND** it is not reported as a failure

#### Scenario: The applied set lives with the state it describes

- **WHEN** a durable state is examined from a build other than the one that migrated it
- **THEN** the full applied set with its identifiers, content identities, timings, applying builds, and outcomes is readable from that state
- **AND** it does not depend on any record held outside it

#### Scenario: The record and the effect do not disagree

- **WHEN** a migration completes
- **THEN** its effect and its record of completion are both observable to any subsequent reader
- **AND** no reader observes the effect without the record or the record without the effect

#### Scenario: An entry cannot be removed to force re-application

- **WHEN** an attempt is made to remove or amend an entry in the applied set
- **THEN** the attempt is refused
- **AND** the entry is unchanged
- **AND** the attempt is recorded

#### Scenario: A duplicate application is not merely harmless but prevented

- **WHEN** two processes each attempt to apply the same outstanding migration
- **THEN** its effect is applied once
- **AND** exactly one completion entry exists for it

### Requirement: An interrupted migration leaves readable state and is safe to re-run

A migration interrupted at any point SHALL leave the durable state in a condition that at least one code version inside the support window can read and serve from — the version that preceded the migration, the version that introduces it, or both — and never a condition neither can read. Re-running an interrupted migration SHALL complete it without duplicating any effect already applied and without requiring the state to be restored from a copy.

An interrupted migration SHALL be recorded as begun and not completed, with enough detail to identify where it stopped, and the recorded schema version SHALL NOT advance for it. A migration whose steps cannot be applied as one indivisible change SHALL declare that, and SHALL declare the point from which a re-run resumes.

#### Scenario: Interruption leaves the state readable

- **WHEN** a migration is interrupted part-way through
- **THEN** a component of the code version that preceded it starts and serves against the resulting state, or a component of the version introducing it does
- **AND** neither is left unable to read the state

#### Scenario: Re-running completes without duplicating

- **WHEN** an interrupted migration is run again
- **THEN** it completes
- **AND** no effect it had already applied is applied a second time
- **AND** the state after completion is identical to the state produced by an uninterrupted application

#### Scenario: An incomplete migration does not advance the version

- **WHEN** a migration is interrupted
- **THEN** the recorded schema version is the version that preceded it
- **AND** the migration is recorded as begun and not completed

#### Scenario: The resumption point is recorded

- **WHEN** a migration that cannot be applied as one indivisible change is interrupted
- **THEN** the record states which of its steps completed
- **AND** a re-run resumes from the declared resumption point

#### Scenario: Repeated interruption converges

- **WHEN** a migration is interrupted and re-run repeatedly, each time interrupted at a different point, and then run to completion once uninterrupted
- **THEN** it completes on that run
- **AND** the resulting state is identical to the state produced by a single uninterrupted application
- **AND** the recorded history shows one completion entry and one begun-and-not-completed entry per interruption

### Requirement: At most one migration runs against a durable state at a time

Where several instances start against one durable state simultaneously, at most one SHALL apply an outstanding migration. The others SHALL either wait for it or refuse with a distinguishable cause, and SHALL NOT begin serving traffic against a state with an outstanding migration in either case. Exclusion SHALL be a property of the durable state rather than of the code path that starts a migration, so that an attempt reaching the state by another path is still excluded.

Where the instance holding the exclusion stops without completing, the exclusion SHALL be released without operator action and the next attempt SHALL resume the interrupted migration rather than starting a second concurrent application of it. An exclusion held longer than a configured bound SHALL be surfaced with the identity of the holder and the migration it is applying.

#### Scenario: Simultaneous starts apply once

- **WHEN** many instances start at once against a durable state with one outstanding migration
- **THEN** exactly one applies it
- **AND** exactly one completion entry exists for it

#### Scenario: The instances that did not apply do not serve

- **WHEN** an instance defers to another that is applying a migration
- **THEN** it reports itself not ready
- **AND** it accepts no exchange until the migration has completed

#### Scenario: Exclusion is enforced by the state

- **WHEN** a migration attempt reaches the durable state by a path that did not acquire the exclusion
- **THEN** it is still excluded
- **AND** no concurrent application occurs

#### Scenario: A dead holder does not block forever

- **WHEN** the instance applying a migration stops without completing it
- **THEN** the exclusion is released without operator action
- **AND** the next attempt resumes that migration rather than beginning a second application of it

#### Scenario: A long-held exclusion is surfaced

- **WHEN** the exclusion has been held for longer than the configured bound
- **THEN** the condition is surfaced naming the holder and the migration being applied
- **AND** it is not resolved by another instance seizing the exclusion

### Requirement: A failed migration does not advance the recorded version

A migration that fails SHALL leave the recorded schema version unchanged and SHALL record its failure with a machine-readable cause. The failure SHALL be distinguishable from a compatibility refusal, from an out-of-order arrival, from an altered migration, and from an exclusion held elsewhere.

An instance whose outstanding migration has failed SHALL NOT serve traffic at an ambiguous version: it SHALL report itself not ready with migration failure as the stated cause, and SHALL NOT retry indefinitely without recording each attempt and its cause. Where a migration is composed of steps, the record SHALL state which completed and which failed.

#### Scenario: The version stays put on failure

- **WHEN** a migration fails part-way through
- **THEN** the recorded schema version is unchanged
- **AND** the failure is recorded with a machine-readable cause

#### Scenario: Failure is distinguishable from refusal

- **WHEN** an operator inspects a component that will not serve
- **THEN** a failed migration, an out-of-range schema version, an altered migration, and an exclusion held elsewhere are reported as four distinct causes

#### Scenario: A failed migration does not serve

- **WHEN** a migration has failed and remains outstanding
- **THEN** the instance reports itself not ready with migration failure as the cause
- **AND** it does not accept new exchanges

#### Scenario: Retries are recorded

- **WHEN** a failing migration is attempted repeatedly
- **THEN** each attempt and its cause is recorded
- **AND** no attempt is retried silently

#### Scenario: Step-level failure is attributed

- **WHEN** a migration composed of several steps fails at one of them
- **THEN** the record names the steps that completed and the step that failed
- **AND** the cause is attributed to that step

### Requirement: Every migration is operable against by the code version preceding it

Because the operator's fleet is upgraded instance by instance, more than one code version SHALL be expected to operate against one durable state simultaneously. Every migration SHALL therefore be operable against by the code version immediately preceding the one that introduces it. Three points SHALL each hold: after the migration is applied and before any instance of the new code version starts, the preceding version SHALL continue to serve correctly; while instances of both versions run concurrently, each SHALL serve correctly and each SHALL read what the other wrote; and after every instance has been replaced, the new version SHALL serve correctly.

A change whose end state the preceding version cannot operate against SHALL be decomposed into an ordered sequence of steps, each individually satisfying the obligation above, and the system SHALL run correctly at every intermediate point of that sequence — not only at its first and last. Renaming, retyping, narrowing, or removing something the preceding version reads or writes SHALL NOT be a single migration. The sequence SHALL be declared as one sequence, with each step stating the range of code versions it is compatible with, rather than as unrelated migrations whose relationship is recorded nowhere.

Whether the preceding version can operate against a migration's end state SHALL be established before release by applying the migration and running that version's own behaviour suite against the resulting state, not by inspecting the migration's declaration or its author's intent. A step whose declared compatible code-version range excludes the immediately preceding version SHALL be refused unless it is a step of a declared sequence that states that exclusion.

A step that removes the shape the preceding version depends on SHALL state the earliest code version that may apply it. Applying such a step while an instance below that version is still serving SHALL be refused, or where the running instances cannot be determined, SHALL require explicit confirmation naming that risk.

#### Scenario: The preceding version serves against the migrated state

- **WHEN** a migration is applied and no instance of the new code version has started
- **THEN** instances of the preceding code version continue to serve correctly
- **AND** the behaviour suite of the preceding version passes against the migrated state unchanged

#### Scenario: Two code versions serve concurrently

- **WHEN** instances of the preceding and the new code version serve against one durable state at once
- **THEN** each serves correctly
- **AND** a subject written by either is read correctly by the other
- **AND** neither erases a value written by the other

#### Scenario: A rename is decomposed, never applied in one step

- **WHEN** a stored attribute the preceding version reads must be renamed
- **THEN** the change is expressed as an ordered sequence in which the new shape is introduced, both shapes are maintained, reads move to the new shape, and only then is the old shape removed
- **AND** at each of those points both code versions in play serve correctly

#### Scenario: Every intermediate point is exercised, not only the endpoints

- **WHEN** a decomposed sequence is verified with a deliberate defect introduced that manifests only between two of its steps
- **THEN** the verification fails and names the intermediate point
- **AND** a verification that exercises only the state before the first step and after the last does not report the sequence as verified

#### Scenario: A migration the preceding version cannot read is refused

- **WHEN** a migration is proposed whose end state the immediately preceding code version cannot operate against
- **THEN** it is refused before it is applied
- **AND** the refusal names the preceding version and what it would be unable to read
- **AND** the refusal is not deferred until the mixed-version state is observed in production

#### Scenario: A removal step names its earliest permitted code version

- **WHEN** a step removes a shape an earlier code version depends on
- **THEN** it states the earliest code version that may apply it
- **AND** applying it while an instance below that version is serving is refused, or requires explicit confirmation naming that instance

#### Scenario: The sequence is declared as a sequence

- **WHEN** a non-additive change is expressed as several migrations
- **THEN** they are recorded as one declared sequence with a stated compatible code-version range per step
- **AND** an operator can tell from the record which steps remain before the change is complete

### Requirement: A migration never requires a tenant to act

Sidecars run in tenants' infrastructure and are never force-upgraded, so an obligation a migration places on a tenant is an obligation that may never be met. A migration SHALL NOT require any tenant to upgrade a sidecar, re-establish a tunnel, re-enrol, obtain a new credential, re-create a mount point, re-claim a hostname, or take any other action in order for their traffic to continue being served.

Applying a migration SHALL leave every established tunnel established, every credential valid at the moment of application still valid, every verified hostname still verified, and every mount still matching. The contract version and capability set already negotiated on an established tunnel SHALL be unaffected by a schema change, and a schema change SHALL NOT cause a renegotiation, a reconnection, or a change in the fidelity a connected sidecar is served at.

Where a change genuinely cannot be made without an effect a tenant must act on, that effect SHALL be declared as a property of the migration before it is applied, SHALL enumerate the tenancies affected and what each would have to do, and SHALL be applied only under a confirmation naming that migration. Such a migration SHALL NOT be applied on the strength of a standing setting. An effect of this kind that the declaration did not state SHALL be a migration failure with a cause naming an undeclared tenant-visible effect.

#### Scenario: Established tunnels survive a migration

- **WHEN** a migration is applied while sidecars of several builds hold established tunnels
- **THEN** every tunnel remains established
- **AND** each continues to serve exchanges for its mount
- **AND** none renegotiates its contract version or capability set

#### Scenario: Credentials in force stay in force

- **WHEN** a migration is applied while credentials are in force
- **THEN** each authenticates afterwards exactly as it did before
- **AND** no tenant is required to obtain a new one

#### Scenario: A migration does not cause a fleet-wide reconnection

- **WHEN** a migration is applied to an installation holding many tunnels
- **THEN** no tunnel is ended as a consequence of the migration
- **AND** no reconnection attempt is caused by it

#### Scenario: Routing and hostname state survive a migration

- **WHEN** a migration is applied
- **THEN** every mount that matched a given request target before it matches the same one afterwards
- **AND** every verified hostname remains verified and continues to be served

#### Scenario: An unavoidable tenant-visible effect is declared and confirmed

- **WHEN** a migration whose application would oblige tenants to act is outstanding
- **THEN** it declares that effect, the tenancies affected, and what each would have to do
- **AND** it is applied only under a confirmation naming that migration
- **AND** a standing setting permitting such migrations does not permit it

#### Scenario: An undeclared tenant-visible effect is a failure

- **WHEN** a migration that declared no tenant-visible effect ends a tunnel, invalidates a credential, or unverifies a hostname
- **THEN** it is reported as failed with a cause naming an undeclared tenant-visible effect
- **AND** the condition is surfaced rather than left for the tenant to report

### Requirement: A code version can be rolled back across a migration

Rolling the code back to the version that preceded a migration SHALL NOT require the migration to be undone. The preceding version SHALL start and serve correctly against the migrated durable state, which follows from its declared schema range including the version the migration produced.

A migration that raises the recorded schema version above the declared highest of the immediately preceding code version SHALL be identified as blocking that rollback before it is applied, and applying it SHALL require explicit acknowledgement of that consequence. Attempting to start a code version whose declared range excludes the current schema version SHALL refuse with the out-of-range cause rather than operating on the state, and SHALL NOT downgrade, alter, or reinterpret the state in order to proceed.

#### Scenario: Rollback needs no schema undo

- **WHEN** the code is rolled back to the version preceding a migration while the migration remains applied
- **THEN** the preceding version starts and serves correctly
- **AND** no migration is undone

#### Scenario: A rollback-blocking migration is identified before it is applied

- **WHEN** a migration would raise the schema version above the preceding code version's declared highest
- **THEN** that consequence is stated before the migration is applied
- **AND** applying it requires explicit acknowledgement
- **AND** it is not discovered by attempting the rollback

#### Scenario: An excluded rollback refuses rather than adapting

- **WHEN** a code version whose declared range excludes the current schema version is started
- **THEN** it refuses with the out-of-range cause
- **AND** it makes no write to the durable state
- **AND** it does not reinterpret the state under an older version's rules

#### Scenario: Rollback does not lose what the newer version wrote

- **WHEN** the newer code version writes to a subject and the code is then rolled back
- **THEN** the preceding version reads the subject correctly
- **AND** values it does not recognise are preserved across its own writes

### Requirement: Reversibility is declared before a migration is applied

Every migration SHALL declare whether it can be undone, and that declaration SHALL be recorded with it in the applied set. A migration declared irreversible SHALL be identified as such before it is applied, so that irreversibility is a stated property rather than a discovery made when an undo is attempted.

An attempt to undo a migration declared irreversible SHALL be refused with a distinguishable cause and SHALL make no change to the durable state. A migration declared reversible SHALL have an inverse that is exercised rather than asserted: applying it, undoing it, and applying it again SHALL reproduce the same schema and the same store-level enforcement as applying it once. An undo SHALL be recorded as a further entry in the append-only history rather than by removing the forward entry, and where an undo declared possible fails, the record SHALL state what remains applied.

#### Scenario: Reversibility is visible before application

- **WHEN** the outstanding migrations are inspected before being applied
- **THEN** each states whether it can be undone
- **AND** an irreversible one is identified without applying it

#### Scenario: Undoing an irreversible migration is refused

- **WHEN** an undo is attempted for a migration declared irreversible
- **THEN** it is refused with a distinguishable cause
- **AND** the durable state is unchanged

#### Scenario: A declared inverse is exercised

- **WHEN** a migration declared reversible is applied, undone, and applied again
- **THEN** the resulting schema and store-level enforcement are identical to applying it once
- **AND** the recorded schema version is the same

#### Scenario: An undo appends to the history

- **WHEN** a migration is undone
- **THEN** a further entry records the undo, its cause, its time, and the build that performed it
- **AND** the forward entry is still present

#### Scenario: A failed undo states what remains

- **WHEN** an undo of a migration declared reversible fails part-way
- **THEN** the record states which of its effects were reversed and which remain
- **AND** the recorded schema version reflects a state a code version in the window can read

### Requirement: A migration that removes or truncates data does so only under explicit confirmation

A migration whose application would remove, truncate, overwrite, or narrow stored data SHALL declare that property, and SHALL be applied only under a confirmation that names that specific migration. A standing configuration, a blanket setting, or an environment-wide flag SHALL NOT constitute confirmation for a migration authored after it was set.

Without confirmation, such a migration SHALL be refused and SHALL remain outstanding, keeping the recorded schema version unadvanced and the instance not ready — it SHALL NOT be skipped silently, and its absence SHALL NOT be reported as success. A migration whose declaration does not state that it removes data, but whose application would, SHALL be refused with a cause naming an undeclared destructive effect.

What a destructive migration removed SHALL be recorded: the scope affected, a count per affected tenancy, and the time. That record SHALL be written before the removal takes effect, so that an interruption during removal still leaves evidence of what was being removed.

#### Scenario: Confirmation names the migration

- **WHEN** a migration declared to remove data is applied
- **THEN** the confirmation supplied names that migration
- **AND** a confirmation naming a different migration, or none, does not permit it

#### Scenario: A standing setting is not confirmation

- **WHEN** a blanket setting permitting destructive migrations is in force and a newly authored destructive migration is outstanding
- **THEN** it is still refused
- **AND** the refusal names the required per-migration confirmation

#### Scenario: An unconfirmed destructive migration is not skipped

- **WHEN** a destructive migration is outstanding and unconfirmed
- **THEN** the recorded schema version is unadvanced
- **AND** the instance reports itself not ready
- **AND** the migration run does not report success

#### Scenario: An undeclared destructive effect is refused

- **WHEN** a migration that did not declare removal would remove or truncate stored data
- **THEN** it is refused with a cause naming an undeclared destructive effect
- **AND** nothing is removed

#### Scenario: What was removed is recorded

- **WHEN** a confirmed destructive migration completes
- **THEN** the record states the scope affected, a count per affected tenancy, and the time
- **AND** the record does not contain the removed values themselves

#### Scenario: Evidence survives an interruption mid-removal

- **WHEN** a destructive migration is interrupted while removing
- **THEN** the record of what was to be removed is already present
- **AND** an operator can determine what was in scope without reconstructing it from the remaining state

### Requirement: Store-level enforcement survives every migration

Invariants that other capabilities require the durable store itself to enforce — the terminal-mount invariant, uniqueness among live siblings, uniqueness of full paths, the soft-delete gating of those uniqueness obligations, bounds on segment character set and length, and every other obligation stated as a property of the store rather than of a code path — SHALL still be enforced by the store after every migration.

After a migration completes, the installation SHALL verify that each such enforcement still refuses the write it exists to refuse, covering every enforcement obligation rather than a sample. A migration that must temporarily suspend an enforcement SHALL declare it and SHALL NOT complete with it absent; a migration that completes with an enforcement absent, weakened, or unverified SHALL be reported as failed and SHALL NOT advance the recorded schema version.

A migration's own writes reach the durable state without passing the ordinary validation path, so they SHALL satisfy the same invariants. State a migration writes that any capability's invariant would have refused SHALL cause the migration to fail with a cause naming the violated invariant, and the recorded schema version SHALL NOT advance. Where a migration suspended an enforcement while it ran, the verification on completion SHALL cover the state the migration itself wrote and not only the enforcement's presence, because an enforcement restored over state that violates it is not enforcement.

The closed enumerations other capabilities own — the reserved-path enumeration and the reserved control-surface hostname among them — SHALL still hold after a migration, and a migration SHALL NOT release a reserved name or produce a subject that occupies one.

#### Scenario: A migration's own write is held to the invariant

- **WHEN** a migration writes state that would create a child under a mount point, a second live sibling with an existing segment, or a segment outside the permitted character set or length
- **THEN** the migration fails with a cause naming the violated invariant
- **AND** the recorded schema version is unadvanced

#### Scenario: A suspended enforcement is verified against what the migration wrote

- **WHEN** a migration suspends an enforcement, writes state that violates it, and restores the enforcement
- **THEN** the verification on completion detects the violating state
- **AND** the migration is reported as failed rather than complete
- **AND** the presence of the restored enforcement alone does not satisfy the verification

#### Scenario: A reserved name is not released by a migration

- **WHEN** a migration would remove a prefix from the reserved-path enumeration, release the reserved control-surface hostname, or produce a mount whose full path falls under a reserved prefix
- **THEN** it is refused or reported as failed with a cause naming the reservation
- **AND** the reservation still holds afterwards

#### Scenario: The terminal-mount invariant still refuses after migration

- **WHEN** a migration completes and a write is attempted that would create a child under a mount point, reaching the store without passing the ordinary validation path
- **THEN** the write is refused by the store
- **AND** the refusal is the same one produced before the migration

#### Scenario: Uniqueness still refuses after migration

- **WHEN** a migration completes and a second live sibling with an existing segment is written directly to the store
- **THEN** the write is refused
- **AND** a name released by a soft delete is still reusable

#### Scenario: Verification covers every enforcement obligation

- **WHEN** the post-migration verification runs
- **THEN** every store-level enforcement obligation stated by any capability is exercised
- **AND** an obligation with no exercising check is reported as unverified

#### Scenario: A dropped enforcement fails the migration

- **WHEN** a migration suspends a store-level enforcement and completes without restoring it
- **THEN** the migration is reported as failed
- **AND** the recorded schema version is unadvanced
- **AND** the failure names the missing enforcement

#### Scenario: A temporary suspension is declared

- **WHEN** a migration must suspend an enforcement while it runs
- **THEN** it declares that before it is applied
- **AND** the suspension is enumerable as an in-progress condition while it holds

### Requirement: Projections are rebuilt across a schema version change, never assumed valid

The lookup surface and every other projection of durable state SHALL remain reconstructible from the durable state alone across a schema change: a migration SHALL NOT introduce a shape whose correct projection depends on information available only to the migration that produced it.

When the recorded schema version changes, projections SHALL be rebuilt from the durable state rather than carried forward as valid, and a rebuilt projection SHALL produce the same match, remainder, and no-match outcomes as one maintained incrementally at that version. An instance SHALL NOT serve new traffic from a projection built at a schema version other than the one currently recorded; it SHALL report itself not ready until the rebuild completes. This is deliberately narrower than the ordinary staleness rule, under which continuing to serve the last known-good routing state is correct: a projection built against a different schema shape is not known-good, so the correct response is to withhold new traffic rather than to serve it.

Rebuilding SHALL be bounded and observable, and a rebuild that cannot complete SHALL be enumerable as a degraded condition naming a schema change as its cause, distinguishable from a refresh failure caused by an unreachable durable store.

#### Scenario: A version change rebuilds the projection

- **WHEN** the recorded schema version changes
- **THEN** each projection is rebuilt from the durable state
- **AND** none is carried forward from before the change as valid

#### Scenario: The rebuilt projection matches the maintained one

- **WHEN** a projection is rebuilt after a migration
- **THEN** it produces the same match, remainder, and no-match outcomes as one maintained incrementally at that version

#### Scenario: Reconstructibility survives the migration

- **WHEN** a migration introduces a new shape that the projection depends on
- **THEN** the projection is still reconstructible from the durable state alone
- **AND** no information held only by the migration is required to reconstruct it

#### Scenario: A projection from the previous version is not served

- **WHEN** an instance holds a projection built before a schema version change
- **THEN** it accepts no new exchange until the projection has been rebuilt
- **AND** it reports itself not ready with a schema change as the stated cause

#### Scenario: The narrower rule is distinguishable from ordinary staleness

- **WHEN** an instance cannot refresh a projection because the durable store is unreachable
- **THEN** it continues to serve the state it last loaded successfully, as the routing capability requires
- **AND** when instead the projection was built at a different schema version, it does not serve it
- **AND** the two conditions are reported as distinct causes

#### Scenario: A rebuild that cannot complete is enumerable

- **WHEN** a rebuild after a schema change does not complete within its bound
- **THEN** the condition is enumerable with its onset and its effect on serving
- **AND** it names the schema change rather than an unreachable durable store

### Requirement: Migration progress is observable and a long migration is not a hang

While a migration is being applied, an operator SHALL be able to observe which migration is running, when it began, how long it has been running, and a measure of progress that advances as work is done. These SHALL be observable continuously rather than only as records at the beginning and the end, and SHALL be readable from the component's operational surface without reading the durable state directly.

A migration whose progress measure has not advanced for longer than a configured bound SHALL be surfaced as such, so that a stalled migration is distinguishable from a slow one. Completion SHALL record the duration and the outcome. A migration exceeding a configured expected duration SHALL be surfaced with the migration named, and SHALL NOT be ended or restarted without a record. Event identifiers, enumerated causes, and measurement names produced by migration SHALL follow the stable-identifier rule that governs every other signal in the system.

#### Scenario: Progress is observable while it runs

- **WHEN** a migration is being applied
- **THEN** an operator can observe which migration is running, when it began, its elapsed time, and a progress measure
- **AND** these are observable continuously rather than only at start and finish

#### Scenario: A slow migration is distinguishable from a stalled one

- **WHEN** a migration's progress measure stops advancing for longer than the configured bound
- **THEN** the condition is surfaced as a stalled migration
- **AND** it is distinguishable from a migration that is advancing slowly

#### Scenario: A long migration does not appear as a hang

- **WHEN** a migration runs for longer than its configured expected duration
- **THEN** the condition is surfaced naming that migration and its elapsed time
- **AND** the liveness signal continues to report success throughout
- **AND** the progress measure continues to be readable throughout

#### Scenario: Completion is recorded with duration and outcome

- **WHEN** a migration completes
- **THEN** its duration and outcome are recorded
- **AND** both are readable afterwards from the applied set

#### Scenario: A migration is not ended without a record

- **WHEN** a running migration is ended before completing
- **THEN** the reason it was ended and the point it reached are recorded
- **AND** no silent restart occurs

### Requirement: Whether a migration can be applied while traffic is served is declared

Each migration SHALL declare whether it can be applied while the installation serves traffic. A migration declared unable to be SHALL be refused while any instance is serving, with a cause naming that declaration, and SHALL NOT be applied partially in the attempt.

A migration declared safe to apply alongside traffic SHALL not cause a lookup to fail or a mutation to be refused for reasons attributable to the migration, other than the refusals this capability itself defines. Where such a migration nevertheless degrades serving beyond a configured bound, the condition SHALL be surfaced naming that migration. The effect of a migration on serving SHALL be attributable to the migration rather than appearing as an unexplained increase in ordinary failures.

#### Scenario: A traffic-unsafe migration is refused on a serving installation

- **WHEN** a migration declared unable to be applied alongside traffic is attempted while instances are serving
- **THEN** it is refused with a cause naming that declaration
- **AND** no part of it is applied

#### Scenario: A traffic-safe migration does not break lookups

- **WHEN** a migration declared safe to apply alongside traffic is applied while lookups run continuously
- **THEN** every lookup for a mount present before and after the migration matches
- **AND** no lookup observes an empty or partially populated lookup surface

#### Scenario: Degradation during a traffic-safe migration is attributed

- **WHEN** a migration declared safe to apply alongside traffic degrades serving beyond the configured bound
- **THEN** the condition is surfaced naming that migration
- **AND** the effect is attributable to it rather than appearing as an unexplained rise in ordinary failures

#### Scenario: The declaration is visible before application

- **WHEN** the outstanding migrations are inspected
- **THEN** each states whether it can be applied alongside traffic
- **AND** an operator can plan a drain from that statement rather than from experience

#### Scenario: A wrongly declared migration is caught rather than trusted

- **WHEN** a migration declaring itself safe to apply alongside traffic is applied to an installation under continuous lookups and mutations, and it causes a lookup or a mutation to fail
- **THEN** the verification fails and attributes the failure to that declaration
- **AND** the migration is not released on the strength of the declaration having been made

### Requirement: A migration touching tenant-attributed state is recorded in the audit trail

A migration that reads, alters, or removes tenant-attributed state SHALL produce an audit record stating the migration's identifier, the acting operator principal, the build that applied it, the time, the nature of the change, the scope affected per tenancy, and the outcome. Such a record SHALL be produced whether the outcome was success, refusal, or failure, and SHALL be distinguishable from an action taken by a principal of the affected tenancy, as the isolation capability requires of every operator action.

Where the audit record for a migration cannot be written, the migration SHALL be refused rather than applied unrecorded, on the same terms the isolation capability sets for a mutation whose record cannot be written.

A migration SHALL NOT modify, remove, reorder, or reinterpret an existing audit record as an effect of changing the schema. A schema change to the trail's own shape SHALL be additive and SHALL leave every existing record readable with the meaning it had when written. Deliberate retention, expiry, or erasure of audit records is not a schema change and is not within this capability: a migration whose declared purpose is to remove audit records SHALL be refused with a cause naming that the retention policy is unstated, and SHALL remain refused until the capability that owns retention states it. This capability SHALL NOT resolve, by implication, the conflict between an immutable trail and any erasure obligation.

Where a migration's record falls within a tenant's own scope under the isolation capability's scope rule, it SHALL NOT name another tenancy or disclose any count, size, or attribute belonging to another tenancy.

#### Scenario: A migration over tenant state is recorded

- **WHEN** a migration alters tenant-attributed state
- **THEN** an audit record exists naming the migration, the operator principal, the build, the time, the change, the per-tenancy scope, and the outcome

#### Scenario: An operator migration is distinguishable from a tenant action

- **WHEN** a tenant reads the audit records in their own scope after such a migration
- **THEN** the record is identifiable as an operator action rather than an action by a principal of their tenancy

#### Scenario: An unwritable audit record refuses the migration

- **WHEN** the audit record for a migration over tenant-attributed state cannot be written
- **THEN** the migration is refused and the state is unchanged
- **AND** the condition is reported to an operator
- **AND** it is not discarded silently

#### Scenario: A migration cannot amend the trail as a side effect

- **WHEN** a schema change would modify, remove, or reorder an existing audit record
- **THEN** it is refused with a distinguishable cause
- **AND** the records are unchanged
- **AND** the attempt is recorded

#### Scenario: A migration whose purpose is to remove audit records is refused

- **WHEN** a migration declares that its purpose is to remove or expire audit records
- **THEN** it is refused with a cause naming that the retention policy is unstated
- **AND** no audit record is removed
- **AND** the refusal does not resolve the retention question by permitting or forbidding erasure generally

#### Scenario: A schema change to the trail preserves meaning

- **WHEN** the shape of the audit trail itself is changed by a migration
- **THEN** every record written before the change is still readable
- **AND** each carries the meaning it had when it was written
- **AND** none is rewritten, reordered, or dropped

#### Scenario: A migration record discloses no other tenancy

- **WHEN** a tenant reads a migration record affecting their own scope
- **THEN** it names no other tenancy
- **AND** it discloses no count, size, or attribute belonging to another tenancy

### Requirement: A migration never moves data across a tenancy boundary

Every subject in the durable state SHALL be attributed to the same tenancy after a migration as before it. This SHALL be verified after each migration that touches tenant-attributed state, per tenancy, rather than assumed from the migration's intent.

A migration that would attribute a tenancy to a subject that has none SHALL refuse rather than derive one: it SHALL NOT assign a default tenancy, the tenancy of a neighbouring subject, or the tenancy of the operator applying it. A migration that merges, splits, or re-keys subjects SHALL NOT do so across tenancies, and an attempt SHALL be refused with a distinguishable cause. A migration that introduces a structure shared between tenants SHALL introduce it already satisfying the isolation capability's obligation on shared infrastructure; one that does not SHALL be refused before it is applied rather than found to leak afterwards.

After a migration, the scope verification that governs ordinary reads SHALL still hold: no subject SHALL have become readable within a tenancy that could not read it before.

#### Scenario: Attribution is verified, not assumed

- **WHEN** a migration touching tenant-attributed state completes
- **THEN** a per-tenancy verification confirms that every subject's tenancy attribution is unchanged
- **AND** a difference is reported as a migration failure

#### Scenario: A missing tenancy is refused, not derived

- **WHEN** a migration encounters a subject with no tenancy attribution
- **THEN** it refuses with a cause naming an unattributed subject
- **AND** it assigns no default, neighbouring, or operator tenancy

#### Scenario: Merging across tenancies is refused

- **WHEN** a migration would merge, split, or re-key subjects belonging to different tenancies into one
- **THEN** it is refused with a distinguishable cause
- **AND** no subject changes tenancy

#### Scenario: A shared structure a migration would introduce is checked before it is applied

- **WHEN** a migration would introduce a structure shared between tenants that does not satisfy the isolation capability's obligation on shared infrastructure
- **THEN** the migration is refused before it is applied
- **AND** the refusal names that obligation
- **AND** the leak is not discovered by a lookup crossing the boundary afterwards

#### Scenario: Nothing becomes readable in another scope

- **WHEN** a migration completes
- **THEN** no subject is readable within a tenancy that could not read it before
- **AND** the verification that establishes this is per tenancy rather than aggregate

#### Scenario: A cross-tenancy effect fails the migration rather than being corrected later

- **WHEN** post-migration verification finds a subject attributed to a different tenancy than before
- **THEN** the migration is reported as failed
- **AND** the condition is surfaced rather than corrected by a subsequent migration without record

### Requirement: Applying every migration to an empty state reproduces the cumulative schema

Applying the full ordered set of migrations to an empty durable state SHALL produce the same schema — the same stored attributes and collections, the same store-level enforcement, the same defaults, and the same recorded version — as applying them cumulatively to a state that has carried data throughout. This equivalence SHALL be verified automatically and a difference SHALL be a failure, so that a contributor's fresh setup is the same schema an installation is running rather than an approximation of it.

There SHALL be no second authoritative description of the schema that can drift from the migrations. Where a derived description exists for convenience, it SHALL be generated from the migrations and its disagreement with them SHALL be a failure rather than a discrepancy to reconcile by hand.

A migration that only succeeds where data already exists — one depending on a subject it did not create — SHALL be caught by the empty-state application rather than by a contributor's setup failing. The comparison SHALL cover enforcement and defaults, not merely the presence of stored attributes and collections, because it is the enforcement that the invariants of other capabilities rest on.

#### Scenario: Fresh and cumulative schemas are identical

- **WHEN** the full ordered set of migrations is applied to an empty durable state
- **AND** the same set is applied cumulatively to a state that carried data throughout
- **THEN** the resulting schemas are identical in stored attributes, collections, enforcement, defaults, and recorded version

#### Scenario: The comparison is automated and fails on a difference

- **WHEN** a migration produces a schema on an empty state that differs from the cumulative result
- **THEN** the comparison reports a failure naming the difference
- **AND** the difference is not left to be noticed by a contributor

#### Scenario: There is no second source of truth

- **WHEN** a derived description of the schema exists
- **THEN** it is generated from the migrations
- **AND** a disagreement between it and the migrations is a failure

#### Scenario: A migration depending on pre-existing data is caught

- **WHEN** a migration assumes a subject exists that no earlier migration created
- **THEN** the empty-state application fails
- **AND** the failure names that migration

#### Scenario: Enforcement is part of the comparison

- **WHEN** a fresh schema is compared with a cumulative one
- **THEN** every store-level enforcement obligation and default is compared
- **AND** a fresh state missing an enforcement present in the cumulative one is a failure

#### Scenario: A fresh setup satisfies the same invariants

- **WHEN** a durable state built from empty by applying every migration is exercised
- **THEN** it refuses the same writes an installation's state refuses
- **AND** its recorded version equals the newest version the build declares

### Requirement: An encoded value in durable state carries its own encoding identifier

Where the durable state holds a value in an encoding the code must interpret — a serialised structure, a compressed payload, an encoded identifier, or any other representation whose meaning is not the stored octets themselves — that value SHALL carry an identifier of its own encoding alongside it, and the interpretation applied SHALL be selected from that identifier rather than from the recorded schema version, the running build, or the value's length or shape. This is the record-level counterpart of the schema version: a schema version tells a component what the state's shape is, and an encoding identifier tells it how to read a particular value written by a version other than itself. The version a protected record carries to identify the derivation that protected it is owned by the capabilities that own cryptographic material, is taken as given here, and is not restated by this capability.

A value in an encoding the running code does not know SHALL fail closed with an enumerated cause, SHALL be recorded, and SHALL NOT be interpreted under any other encoding the code does know, tried against each encoding in turn, or overwritten. The shape of any failure visible to a client or a credential presenter remains owned by the capability that owns that class of value, so this obligation SHALL NOT be read as requiring an externally distinguishable response. Introducing a new encoding SHALL NOT invalidate values in a prior encoding while any code version inside the support window still writes it, and both SHALL be readable throughout.

Moving stored values from one encoding to another SHALL be a migration in its own right, subject to every obligation of this capability, and SHALL NOT be performed opportunistically on read without a record. Re-protecting a record under a new generation of material without changing its encoding is not an encoding change and is governed by the capability that owns that material, not by this one.

#### Scenario: Interpretation follows the identifier, not the build

- **WHEN** a value written in an older encoding is read by a build whose default encoding is newer
- **THEN** it is interpreted under the encoding its identifier names
- **AND** the build's own default encoding does not determine the interpretation
- **AND** the recorded schema version does not determine the interpretation

#### Scenario: An unknown encoding fails closed rather than being guessed

- **WHEN** a value carries an encoding identifier the running code does not know
- **THEN** the operation depending on it fails with an enumerated cause that is recorded
- **AND** the value is not interpreted under any encoding the code does know
- **AND** no attempt is made against the encodings in turn
- **AND** the value is not overwritten

#### Scenario: The encoding is not inferred from the value

- **WHEN** a value's stored form resembles that of another encoding
- **THEN** the identifier still determines the interpretation
- **AND** no interpretation is selected from the value's length or shape

#### Scenario: Both encodings are readable during the window

- **WHEN** a new encoding is introduced while a code version inside the support window still writes the prior one
- **THEN** values in both encodings are readable
- **AND** values in the prior encoding are not invalidated

#### Scenario: Re-encoding is a migration, not a side effect of a read

- **WHEN** stored values must be moved to a new encoding
- **THEN** the change is applied as a migration subject to the obligations of this capability
- **AND** no value is re-encoded opportunistically during a read without a record

#### Scenario: A re-encoding migration records its scope

- **WHEN** a re-encoding migration completes
- **THEN** the record states the scope affected and the counts per tenancy
- **AND** it does not contain any re-encoded value or the material required to interpret one

#### Scenario: Re-protection under new material is not a schema change

- **WHEN** stored records are re-protected under a new generation of material with their encoding unchanged
- **THEN** the recorded schema version does not advance
- **AND** the sweep is not recorded as a migration in the applied set
- **AND** no obligation of this capability is applied to it

### Requirement: Sidecar-local durable state is versioned by the same rules

A sidecar that keeps durable state of its own SHALL version it by the obligations of this capability: a version recorded in that state, a declared supported range, an ordered and recorded set of migrations, and refusal rather than reinterpretation outside the range. The asymmetry runs the other way from the proxy's: tenants both upgrade and downgrade sidecars on their own schedule, so a sidecar SHALL expect to meet local state written by a version other than itself in either direction.

Local state at a version outside the running sidecar's declared range SHALL cause it to refuse to start, with a cause distinguishable from a configuration failure, a credential failure, an unverifiable tunnel endpoint, and an unreachable proxy. A sidecar SHALL NOT discard, recreate, reinitialise, or overwrite local state whose recorded version it cannot operate against, and SHALL NOT require the tenant to delete local state in order to upgrade. A sidecar starting with no prior local state SHALL initialise it at its own version and record that version.

This obligation concerns the version of the local state as a whole. The treatment of an individual stored record that fails to decrypt or fails authentication is owned by the credential capability and is taken as given here; a version incompatibility of the state SHALL be distinguishable from it.

The version of local state and the migrations applied to it SHALL be readable from the sidecar's operational surface alongside its build provenance.

#### Scenario: A downgraded sidecar refuses newer local state

- **WHEN** a sidecar is replaced with an earlier version whose declared range excludes the version of the local state present
- **THEN** it refuses to start with a distinguishable cause
- **AND** the local state is unchanged

#### Scenario: Version-incompatible local state is not recreated

- **WHEN** a sidecar finds local state whose recorded version its declared range excludes
- **THEN** it does not discard, recreate, or overwrite it
- **AND** it reports the condition rather than proceeding with empty state
- **AND** the cause is distinguishable from an individual stored record that failed authentication

#### Scenario: The refusal is distinguishable from a credential failure

- **WHEN** an operator or tenant inspects a sidecar that will not start
- **THEN** local state incompatibility, a configuration failure, a credential failure, and an unverifiable endpoint are reported as distinct causes

#### Scenario: An upgrade preserves local state

- **WHEN** a sidecar is upgraded to a version that migrates its local state
- **THEN** the state it held before the upgrade remains usable afterwards
- **AND** the tenant is not required to delete it

#### Scenario: A fresh sidecar records its version

- **WHEN** a sidecar starts with no prior local state
- **THEN** it initialises the state and records the version it initialised it at
- **AND** a subsequent start reads that version rather than inferring it

#### Scenario: Local state version is observable

- **WHEN** the sidecar's operational surface is queried
- **THEN** the version of its local state and the migrations applied to it are reported
- **AND** they are reported together with its build identity
