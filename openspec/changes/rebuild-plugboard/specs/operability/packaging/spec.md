## Purpose

Defines the obligations every deployable component carries as a distributed artifact, before it runs: that each component ships as one self-contained thing; that whatever the artifact declares about its own configuration is generated from the same schema its startup validation reads, so the two cannot drift; that a release gate proves the published artifact actually starts and reports itself ready rather than merely that it built; that its provenance is fixed when it is produced and cannot be restated by a deployment; that the contract and durable-schema versions it supports are readable from it without running it, so an operator can judge a pairing before deploying; that it is reproducible, verifiable, minimal, and free of secrets; that its inputs are pinned, inventoried and screened on a recurring schedule; that everything it redistributes carries an established origin and stated terms; that a version identifier already published never comes to mean different content, because tenants pin sidecar versions indefinitely and every guarantee here is bound to the content it evaluated; and that every one of those gates has been demonstrated to fail against an artifact that violates it.

This capability exists because the reference system's published artifacts could not boot, on both sides at once, and the single workflow claiming to prove the product ran could not have passed. The proxy raised at startup on a signing value set in no packaging artifact; two further values were declared in a build stage that never reached the runnable artifact; the sidecar's published artifact died on a configuration item its own packaging never declared; and the deployment check asserted a plain-transport success status while the component's own shipped defaults redirected and demanded a protected durable store that the checked deployment did not serve. Every one of those is a packaging failure that no amount of correct component behaviour prevents.

Four boundaries are load-bearing, and each obligation named in them has exactly one owner.

This capability owns the obligations common to every deployable, and owns them outright. `sidecar/program` states none of them a second time; it states only the delta that follows from the sidecar's machine being the tenant's, and each of its requirements that touches one of these obligations names this capability as the owner and holds its rule as given. `operability/observability` owns what a *running* component reports and measures — that every component reports its build provenance at startup and on demand, that configuration is validated in one pass before anything accepts a connection and the values in force are recorded, and that liveness and readiness are answered on a surface separated from tenant traffic; those rules hold as given. This capability owns what an *artifact* declares and guarantees before it runs. `tunnel/wire-contract` owns how two connected peers negotiate a contract version, `operability/schema-migration` owns what running code does about a durable schema version it cannot operate against, and `tunnel/conformance` owns the suite that is the authority on the contract and what a result entitles an implementation to claim; this capability owns only that the corresponding declaration is readable from a stopped artifact and that a release is gated on it.

The set of separately deployed components is enumerated here and nowhere else, and every other capability that needs it refers to this enumeration rather than restating a component list of its own. The component that terminates client-facing protocols, which `design.md` D16 makes a separate deployable, is called **the client-facing terminator** throughout this capability; `tunnel/wire-contract` calls the role it holds the client-facing role, and `proxy/edge-hygiene` states its edge obligations against whichever component terminates the client connection. Those are three names for obligations on one component, not three components.

Four words are used narrowly here, because three of them already carry another meaning elsewhere in the set. A **deployable** is a member of the enumerated set of separately deployed components, and **artifact** always means the released content of one of them for one platform variant — never the conformance suite's own distribution, which `tunnel/conformance` calls an artifact in its own sense. An **input** is something a build draws on, not something a request or a conformance case supplies. An **identity**, unqualified, is an artifact's verifiable content identity; the identity of a principal, a credential, or a listener endpoint is `auth/sidecar-credentials`', `security/key-custody`'s and `tunnel/listener`'s and is always named as such. A **release gate** is a check whose recorded outcome a publication depends on, as distinct from the validation a component performs on itself at startup.

The conformance suite's own distribution is not a member of that set. `tunnel/conformance` requires the suite to be an independently executable artifact a third party can obtain, and that artifact is governed there; nothing in this capability applies to it, and it SHALL NOT be counted as a deployable whose absence from a release fails a gate here.

## ADDED Requirements

### Requirement: Every deployable component releases as exactly one artifact

The set of components that are deployed separately SHALL be enumerated, and every member of that set SHALL be released as exactly one artifact per published platform variant. At minimum the set SHALL contain the proxy, the sidecar, and the component that terminates client-facing protocols which `design.md` D16 makes a separate deployable. No member SHALL be exempt from any requirement of this capability on the ground that it is operator-run, that it is not distributed to tenants, or that it is deployed by the same party that builds it.

A component that is deployed separately and has no artifact satisfying this capability SHALL NOT be released. Where a new separately-deployed component is introduced, it SHALL be bound by every requirement here without any of them being extended to name it, and a release that publishes it without the gates this capability requires SHALL fail.

Two components that are deployed independently SHALL NOT share one artifact, because a shared artifact makes their versions inseparable and forces an operator upgrading one to upgrade the other.

#### Scenario: Each separately deployed component has its own artifact

- **WHEN** the release for a version is examined
- **THEN** every component in the enumerated set has an artifact of its own
- **AND** no two independently deployed components are carried by the same artifact

#### Scenario: The operator-run components are not exempt

- **WHEN** the artifact for the proxy and the artifact for the client-facing terminator are examined
- **THEN** each is subject to the same packaging, gating, provenance, and inventory obligations as the sidecar's artifact
- **AND** no obligation is waived on the ground that the operator builds and deploys them itself

#### Scenario: A new deployable is bound without being named

- **WHEN** a further separately deployed component is introduced and published
- **THEN** its release fails unless it has its own artifact and that artifact passes every gate this capability requires
- **AND** the failure names the obligations not satisfied

#### Scenario: A component with no conforming artifact does not ship

- **WHEN** a component in the set has no artifact, or has one that does not satisfy this capability
- **THEN** the release does not proceed
- **AND** the refusal names that component

### Requirement: An artifact carries everything it needs to start and declares what it needs from outside

An artifact SHALL carry every component of itself that it needs in order to start: its executable material, every execution environment it depends on, and every file it reads that is not supplied by the deployment. Starting it SHALL require no construction step, nothing installed at the destination beyond the external dependencies it declares, no companion artifact, and no retrieval of any part of itself at start or during operation. This obligation is stated here for every deployable and nowhere else. `sidecar/program` adds only the tenant-side narrowing of what an artifact may require of the machine it lands on, and does not restate this rule.

Whatever an artifact requires from outside itself in order to start — a durable store, a credential store, a signal destination, a network endpoint — SHALL be enumerated in a declaration the artifact carries, readable without running it. An artifact that cannot start without an external dependency absent from that declaration SHALL NOT be considered to satisfy this requirement, and the release gate SHALL detect that case by starting it with only the declared dependencies present.

#### Scenario: The artifact starts with no retrieval of its own parts

- **WHEN** the published artifact is started with every outbound network path blocked except those its declared external dependencies require
- **AND** valid values are supplied for the configuration items the schema marks required
- **THEN** it starts and reports itself ready
- **AND** it retrieved no part of itself from any location

#### Scenario: Nothing is installed at the destination

- **WHEN** the artifact is started in an environment containing no software other than the artifact itself
- **THEN** it starts and reports itself ready
- **AND** it performs no construction step

#### Scenario: An undeclared external dependency is a packaging failure

- **WHEN** a component is changed so that starting it requires an external dependency its declaration does not list
- **AND** the gate starts the published artifact with only the declared dependencies present
- **THEN** the gate fails
- **AND** the failure names the dependency that was required and not declared

#### Scenario: The external dependency declaration is readable without running the artifact

- **WHEN** an operator interrogates an artifact for what it requires from outside itself, without starting it
- **THEN** the complete declared set is returned
- **AND** the set matches what the component actually requires in order to reach readiness

### Requirement: The artifact's declared configuration is generated from the configuration schema

Whatever an artifact declares about its own configuration — the items it names, the values it carries for them, and which of them it expects the deployment to supply — SHALL be generated from the same configuration schema that the component's startup validation reads. The declaration SHALL NOT be maintained as a second, hand-edited statement of the same facts. This is the load-bearing requirement of this capability: the reference system's configuration contract existed in three places that drifted, and that drift, not any component defect, is why nothing booted.

A build in which the generated declaration differs from the schema SHALL fail rather than produce an artifact, and the failure SHALL name each item that diverged and the direction of the divergence. Adding, removing, or renaming a schema item without regenerating the declaration SHALL be caught this way. This obligation is owned here and binds every deployable, with one generation and one divergence check used for all of them and the check enforced as a release gate rather than a convention. `sidecar/program` does not restate it; it adds only that the sidecar's declaration must state, for each item the deployment supplies, whether only the operator can issue it or the tenant's own infrastructure determines it, and that statement is generated and gated on the same terms as every other property of an item.

Where an item's value is carried in the artifact rather than supplied by the deployment, that value SHALL be the value the schema states, and an artifact carrying a value the schema does not state for that item SHALL fail the same gate.

#### Scenario: A schema item added without touching the artifact still appears in what the artifact declares

- **WHEN** an item is added to the configuration schema and no packaging declaration is edited
- **AND** the artifact is built
- **THEN** the item appears in what the built artifact declares about its configuration
- **AND** the value or the expectation-to-be-supplied it declares is the one the schema states

#### Scenario: An artifact whose declared set differs from the schema fails its release gate

- **WHEN** an artifact's declared configuration set differs from the schema in any item
- **THEN** the release gate fails
- **AND** the failure names each diverged item and states whether it was present only in the schema or only in the declaration

#### Scenario: A renamed item is caught

- **WHEN** a schema item is renamed and an artifact declaration still carries the former name
- **THEN** the gate fails naming both the former and the current name

#### Scenario: A carried value that contradicts the schema is caught

- **WHEN** an artifact carries, for an item it declares, a value the schema does not state for that item
- **THEN** the gate fails naming that item, the carried value, and the schema's value

#### Scenario: Every deployable is checked by the same gate

- **WHEN** the declaration of the proxy's artifact, the sidecar's artifact, and the client-facing terminator's artifact are each compared against their component's schema
- **THEN** the same divergence check is applied to each
- **AND** a divergence in any one of them fails the release

### Requirement: The shipped example configuration is generated from the same schema and is complete on its own

The example configuration published alongside an artifact SHALL be generated from the same schema as the artifact's own declaration and the component's startup validation, so that all three derive from one source and no two of them can disagree. A release in which any two of the three disagree SHALL fail.

The example SHALL name every item the schema declares, SHALL carry the schema's stated value for every item that has one, and SHALL mark, rather than populate, every item the schema marks as secret and every required item the schema states no value for. Used verbatim with a value supplied for each item it marks that way, it SHALL pass validation with no item reported missing, and the items it marks SHALL be the only items an operator must supply. An example that requires an operator to discover an item not named in it SHALL NOT be considered complete, because discovering configuration by repeated restart is the ergonomic failure the reference system's correct no-defaults policy shipped with.

The example is distributed material. It SHALL NOT carry a usable value for any item the schema marks as secret, and a release whose published example carries such a value SHALL fail on the same terms as an artifact containing a secret.

#### Scenario: The example is complete

- **WHEN** the shipped example is used verbatim, with a value supplied for each item it marks as requiring one
- **THEN** validation reports no missing item
- **AND** the component starts
- **AND** no item outside those it marked had to be supplied

#### Scenario: Any disagreement among the three fails the release

- **WHEN** the schema, the artifact's declaration, and the shipped example do not name the same item set
- **THEN** the release fails
- **AND** the failure names the item and the two sources that disagree about it

#### Scenario: A secret item is marked rather than populated

- **WHEN** the shipped example is examined for every item the schema marks as secret
- **THEN** each is present and marked as requiring a value
- **AND** none carries a usable value

#### Scenario: A schema addition reaches the example without editing it

- **WHEN** an item is added to the schema and the example is not edited
- **AND** the release is produced
- **THEN** the shipped example names the new item

#### Scenario: An example carrying a usable secret value fails the release

- **WHEN** the published example carries a usable value for an item the schema marks as secret
- **THEN** the release fails naming that item
- **AND** the failure is not waived on the ground that the example is not the artifact
- **AND** the value is treated as disclosed rather than as an editing mistake

### Requirement: A declaration that does not reach the runnable artifact is a build failure

A configuration item declared at any point during an artifact's construction SHALL be present in the runnable artifact, or the build SHALL fail naming that item. A declaration made in an intermediate construction step that does not carry into the artifact the deployment actually runs SHALL be treated as absent, because it is absent — this is the reference system's exact failure, where two required values were declared in a construction stage that ended before the runnable artifact began, and the artifact then raised at startup on their absence.

The check SHALL be made against the artifact as published rather than against the instructions that produced it, so that an item lost between a construction step and the runnable result is detected rather than inferred to be present.

#### Scenario: An item lost between construction steps fails the build

- **WHEN** a configuration item is declared in an intermediate construction step and is absent from the runnable artifact
- **THEN** the build fails
- **AND** the failure names that item and states that it did not reach the runnable artifact

#### Scenario: The check reads the published artifact, not the build instructions

- **WHEN** the build instructions declare an item and the published artifact does not carry it
- **THEN** the check fails
- **AND** it is not satisfied by the declaration's presence in the instructions

#### Scenario: A complete carry-through passes

- **WHEN** every item declared during construction is present in the runnable artifact with the value the schema states
- **THEN** the check passes

#### Scenario: The failure is distinguishable from a schema divergence

- **WHEN** an item present in the schema and in the generated declaration is lost during construction
- **THEN** the failure names a value that did not reach the artifact
- **AND** it is distinguishable from a declaration that diverged from the schema

### Requirement: The configuration schema is retrievable from every artifact without running it

Every artifact SHALL make its component's configuration schema retrievable without starting the component and without network access, so that an operator can determine what to supply before the first attempt to run it. The retrieved schema SHALL state, for every item, whether it is required, whether it is secret, and what value the artifact carries for it where it carries one.

This binds the proxy's, the sidecar's, and the client-facing terminator's artifacts identically. `sidecar/program` owns the content and closure of the sidecar's schema — that it is the single enumeration of every value the sidecar's behaviour depends on and that nothing outside it is consulted — and this capability owns its retrievability from the artifact. The schema an artifact returns SHALL be the same schema that generated its declaration and its shipped example and that its startup validation reads.

An item the schema marks as secret SHALL be disclosed as secret and never by value. The retrieval SHALL NOT return a value, a placeholder that would validate, a length, a prefix, or a digest for such an item, and SHALL NOT be a path by which material `security/key-custody` places behind a no-read rule becomes readable — no artifact carries a value for a secret item in the first place, and this retrieval SHALL NOT be the exception that reintroduces one.

#### Scenario: The schema is readable from a stopped artifact

- **WHEN** an operator interrogates any deployable's artifact for its configuration schema without starting it and with no network available
- **THEN** the complete schema is returned
- **AND** each item states whether it is required and whether it is secret

#### Scenario: Supplying exactly what was returned is sufficient

- **WHEN** a component is started with exactly the items the interrogation reported as required and nothing else
- **THEN** validation reports no missing item

#### Scenario: The retrieved schema is the schema in force

- **WHEN** the schema retrieved from an artifact is compared against the item set that artifact's startup validation rejects on
- **THEN** the two are identical
- **AND** an item required by validation and absent from the retrieved schema fails the release gate

#### Scenario: An artifact that must be started to disclose its schema fails the gate

- **WHEN** an artifact's schema can be obtained only by starting the component, or only with network access
- **THEN** the release gate fails
- **AND** the failure names the artifact and states that the schema was not retrievable from it while stopped

#### Scenario: A partial schema is a failure, not a shorter schema

- **WHEN** the schema an artifact returns omits an item, or omits whether an item is required or secret
- **THEN** the release gate fails naming the item and the omitted property
- **AND** the omission is not treated as the item being optional or not secret

#### Scenario: A secret item is disclosed as secret and never by value

- **WHEN** an artifact's schema is retrieved and every item it marks as secret is examined
- **THEN** each is reported as secret and as required or not
- **AND** none carries a value, a validating placeholder, a length, a prefix, or a digest
- **AND** the retrieval is not a path by which any material held behind a no-read rule becomes readable

### Requirement: A release gate starts the published artifact and asserts its own readiness signal

For every component and every published platform variant, a gate SHALL run the artifact exactly as published, supply values only for the items the schema marks required that the artifact does not itself carry, and assert that the component reports itself ready through the readiness signal `operability/observability` defines. The gate SHALL NOT pass on any weaker evidence.

The gate SHALL obtain the artifact from where it is published rather than rebuilding it or constructing a local equivalent, because an artifact that starts when rebuilt and fails when published is the failure this gate exists to catch. It SHALL supply no configuration item beyond those described above; supplying an item the artifact should have carried for itself would conceal exactly the drift the generated declaration is meant to prevent.

"As published" means the exact content a deployer would obtain, retrieved from a distribution location by the means a deployer would use. A release MAY make that content obtainable before it is announced as available, so that the gates run against the bytes rather than against a candidate; from the moment those bytes are obtainable under a version identifier, the rule that an identifier is never reused for different content binds them, and a gate failure SHALL be resolved by publishing a new identifier rather than by replacing the content under that one.

Where a component's readiness depends on a peer — the sidecar's on an established tunnel and a reachable backend, and the client-facing terminator's on its contract connection to its counterpart, both as `operability/observability` defines readiness for them — the gate SHALL supply that peer as one of the artifact's declared external dependencies and SHALL still assert readiness rather than substituting a weaker signal. A component whose readiness cannot be reached in the gate because a dependency it requires is absent from its declaration SHALL fail the gate for the undeclared dependency, not be exempted from asserting readiness.

A gate that asserts only that a build succeeded, that an artifact was produced, that a process was created, or that a port was bound SHALL NOT be considered to satisfy this requirement.

#### Scenario: The gate starts what was published and asserts readiness

- **WHEN** the gate runs for a published artifact
- **THEN** it obtains that artifact from where it is published
- **AND** it supplies only the required items the artifact does not carry
- **AND** it passes only when the component reports itself ready through its own readiness signal

#### Scenario: A build-success check does not satisfy the gate

- **WHEN** a gate asserts only that the artifact was produced without starting it
- **THEN** it does not satisfy this requirement
- **AND** the release does not proceed on its evidence

#### Scenario: A rebuilt equivalent does not satisfy the gate

- **WHEN** a gate builds the component locally and starts the result instead of the published artifact
- **THEN** it does not satisfy this requirement

#### Scenario: An artifact that cannot start is caught before release

- **WHEN** a component is changed so that the published artifact fails startup validation on an item its own declaration does not carry
- **THEN** the gate fails
- **AND** the failure names the item the component refused to start without
- **AND** the release does not proceed

#### Scenario: Supplying more than the required items is not permitted

- **WHEN** a gate supplies a value for a configuration item the artifact's own declaration already carries a value for, or for an item the schema does not mark required
- **THEN** the gate is reported as not satisfying this requirement
- **AND** the item it supplied beyond the permitted set is named
- **AND** the release does not proceed on its evidence

#### Scenario: A readiness that depends on a peer is still asserted

- **WHEN** the gate runs for the sidecar's artifact and for the client-facing terminator's artifact
- **THEN** each is supplied the peer its declared external dependencies name
- **AND** each is required to report itself ready through its own readiness signal
- **AND** neither is passed on a weaker signal on the ground that its readiness depends on another component

#### Scenario: A gate failure is resolved by a new identifier, not by replacing content

- **WHEN** an artifact obtainable under a version identifier fails a gate
- **THEN** the corrected content is published under a different identifier
- **AND** publishing it under the identifier that failed is refused

### Requirement: The gate asserts readiness, never a traffic surface or a status the shipped defaults contradict

The gate's assertion SHALL be made against the component's own readiness signal on the operational surface `operability/observability` separates from tenant traffic. It SHALL NOT be made by exercising a surface the component serves to clients or to a peer, and SHALL NOT be made against a surface before the component reports itself ready.

A gate that asserts a particular response from a client-facing surface SHALL NOT be considered to satisfy this requirement, for two reasons the reference system demonstrated together: the component's own shipped defaults may make that response the wrong expectation, and the surface may answer before the component is ready, so the assertion can pass while the component is not serving and fail while it is. The reference's deployment check asserted a plain-transport success status while the component's shipped configuration redirected such requests and required a protected durable store the checked deployment did not provide, so the one check claiming to prove the product ran could not have passed.

Where a gate additionally exercises a client-facing surface, that assertion SHALL be made only after readiness has been observed, and its failure SHALL be reported distinguishably from a readiness failure.

#### Scenario: Readiness is the assertion

- **WHEN** the gate evaluates a started artifact
- **THEN** it reads the component's readiness signal on the operational surface
- **AND** it does not derive readiness from any response on a client-facing surface

#### Scenario: A probe of a traffic surface does not satisfy the gate

- **WHEN** a gate asserts a status from a surface the component serves to clients, and nothing else
- **THEN** it does not satisfy this requirement

#### Scenario: A shipped default that contradicts the assertion is caught

- **WHEN** a gate's expectation of a client-facing surface is inconsistent with the component's shipped configuration
- **THEN** the gate fails
- **AND** the failure names the shipped value that made the expectation unreachable
- **AND** it is reported distinguishably from the component having failed to become ready

#### Scenario: A surface probed before readiness is not evidence

- **WHEN** a gate exercises a client-facing surface before the readiness signal reports ready
- **THEN** the result is not accepted as evidence of readiness
- **AND** the gate is reported as not satisfying this requirement

### Requirement: The gate runs the artifact with its shipped protective defaults in force

The gate SHALL run the component with every protective value at the value the shipped configuration states, and SHALL supply its declared external dependencies in a form that satisfies those values. Where a component ships requiring a protected connection to a durable store, the gate SHALL provide a store that offers that protection rather than relaxing the component's requirement.

A gate that alters a protective value, disables a shipped protection, or substitutes a permissive value in order to reach readiness SHALL NOT be considered to satisfy this requirement, and SHALL be reported as a gate that proves a configuration nobody deploys. Where a gate must run with any value differing from the shipped one, that difference SHALL be recorded with the gate's result, and the result SHALL NOT be presented as evidence for the shipped configuration — the same rule `tunnel/conformance` applies to a relaxed configuration in a conformance run.

#### Scenario: The shipped protective configuration is what starts

- **WHEN** the gate starts the published artifact
- **THEN** every protective value in force is the value the shipped configuration states
- **AND** the declared external dependencies are supplied in a form that satisfies them

#### Scenario: Relaxing a protection to reach readiness fails the gate

- **WHEN** a gate substitutes a permissive value for a shipped protective value so that the component becomes ready
- **THEN** the gate is reported as not satisfying this requirement
- **AND** the release does not proceed on its evidence

#### Scenario: An external dependency that cannot satisfy the shipped requirement is a gate failure

- **WHEN** the gate supplies a durable store that does not offer the protection the shipped configuration requires
- **THEN** the component refuses to start and the gate fails
- **AND** the failure names the unsatisfied requirement rather than reporting an unexplained startup failure

#### Scenario: A recorded difference does not transfer

- **WHEN** a gate necessarily runs with a value differing from the shipped one
- **THEN** the difference is recorded with the result
- **AND** the result is not presented as evidence for the shipped configuration

### Requirement: The platforms a component is published for are declared, and every published variant is gated identically

For each component, the set of platform variants it is published for SHALL be declared, and the declaration SHALL be readable without running any artifact. The component tenants run themselves SHALL be published for every platform the declaration names, because a tenant's platform is not the operator's to choose.

Every published variant SHALL pass the same gates, evaluated against that variant, before the release proceeds. A release in which one variant was gated and the others were published on the strength of its result SHALL NOT proceed. A variant that cannot be gated SHALL NOT be published, and a variant that is published SHALL have its own recorded gate result.

#### Scenario: Every declared platform has a published artifact

- **WHEN** a release is examined against the declared platform set for the tenant-run component
- **THEN** an artifact exists for every declared platform
- **AND** a declared platform with no artifact fails the release

#### Scenario: One variant's result does not cover the others

- **WHEN** the gates are run against one published variant and not against the others
- **THEN** the release does not proceed
- **AND** the refusal names the variants with no result of their own

#### Scenario: A variant that fails its own gate blocks the release

- **WHEN** one published variant fails to start and report ready while the others succeed
- **THEN** the release does not proceed
- **AND** the failure names that variant

#### Scenario: An ungateable variant is not published

- **WHEN** a platform variant cannot be started and evaluated by the gates
- **THEN** it is not published
- **AND** the declared platform set does not claim it

### Requirement: Provenance is fixed when the artifact is produced and no deployment can alter it

That every component reports a version, the source revision it was built from, and whether that source tree was modified, at startup and on demand, and that an absent provenance is reported as explicitly unknown rather than as a value resembling a version, are `operability/observability`'s rules and hold here as given for every component. What this capability owns is the other half: that the provenance is a property of the build and of nothing else.

Provenance SHALL be fixed at the moment the artifact is produced. No configuration item, no value supplied by the deployment, no value supplied by a peer, and no modification to the environment the component runs in SHALL be capable of changing any part of what it reports. An artifact whose provenance can be restated by the deployment SHALL fail its release gate, because a fleet inventory that a deployment can falsify is not an inventory. This binds the proxy, the sidecar, and the client-facing terminator identically, and the non-configurability SHALL be proven by a gate rather than assumed. `sidecar/program` does not restate it; it adds only that the sidecar's provenance is obtainable from four places — the stopped artifact, the startup record, its local surface, and the establishment declaration the proxy records — and that all four must agree, so that an inventory taken inside the tenant's infrastructure and one taken from the proxy identify the same build.

An artifact SHALL NOT be produced without provenance. A build that cannot determine its source revision SHALL fail rather than produce an artifact that reports an unknown revision, except where the build is explicitly declared as one produced outside revision control, in which case the artifact SHALL report that explicitly and SHALL be distinguishable from every released build.

#### Scenario: Provenance is not configurable

- **WHEN** a deployment supplies configuration items whose names or values resemble a version, a revision, or a modification state
- **THEN** the component reports the provenance fixed at build time, unchanged
- **AND** where such an item is in the component's reserved configuration namespace and the schema does not declare it, the component refuses to start rather than accepting it

#### Scenario: A peer cannot restate provenance

- **WHEN** a peer sends a value resembling a version or a revision for the component receiving it
- **THEN** the receiving component's own reported provenance is unchanged

#### Scenario: An alterable provenance fails the gate

- **WHEN** the gate starts a published artifact with configuration attempting to restate its provenance and finds the reported provenance changed
- **THEN** the gate fails
- **AND** the failure names the item that altered it

#### Scenario: A build with no determinable revision does not silently ship

- **WHEN** an artifact is built where the source revision cannot be determined and the build is not declared as one produced outside revision control
- **THEN** the build fails
- **AND** no artifact is produced

### Requirement: Provenance distinguishes a build from a modified working tree and is retrievable from the artifact without running it

An artifact's provenance SHALL distinguish a build produced from an unmodified source tree at a revision from a build produced from a modified tree at the same revision. The two SHALL NOT report identically, because a build from a modified tree corresponds to no reviewable source state and an operator holding one must be able to know that.

Provenance SHALL be retrievable from the artifact without starting the component and without network access, in addition to the reporting `operability/observability` requires at startup and on demand. The value retrieved from the stopped artifact SHALL be identical to every value the running component reports, and a discrepancy between them SHALL fail the release gate.

#### Scenario: A modified tree is distinguishable

- **WHEN** two artifacts are built at the same source revision, one from an unmodified tree and one from a tree carrying uncommitted changes
- **THEN** their provenance differs
- **AND** the second states that the tree was modified

#### Scenario: Provenance is readable from a stopped artifact

- **WHEN** an operator interrogates an artifact for its provenance without starting it and with no network available
- **THEN** the version, the source revision, and the modification state are returned

#### Scenario: The stopped and running values agree

- **WHEN** the provenance retrieved from an artifact is compared with what the started component reports
- **THEN** the two are identical

#### Scenario: A discrepancy fails the gate

- **WHEN** an artifact's retrievable provenance differs from what the started component reports
- **THEN** the gate fails naming both values

### Requirement: Each artifact declares the contract version range it speaks, readable without running it

Every artifact whose component speaks the wire contract SHALL declare the inclusive lowest and highest contract versions that component supports, and the optional capabilities it can declare, retrievable from the artifact without starting it and without network access. `tunnel/wire-contract` owns how a range is negotiated between two connected peers and what happens when there is no overlap; those rules hold as given. The delta this capability adds is that the range is a property of the artifact, readable from the artifact, so that an operator can determine what a build supports before deploying it and without connecting it to anything.

The declared range SHALL NOT be inferable from the artifact's build version, and no consumer SHALL be required to start or connect the component in order to learn it. Where `sidecar/program` requires the sidecar to report its range at startup and on demand, that is the running-component instance of this obligation; what is required here is that the range is readable from the artifact while stopped, and that the proxy's, the sidecar's, and the client-facing terminator's artifacts each declare theirs by the same rule.

#### Scenario: The range is readable from a stopped artifact

- **WHEN** an operator interrogates an artifact for its contract support without starting it and with no network available
- **THEN** the lowest and highest supported contract versions are returned
- **AND** the optional capabilities the component can declare are returned

#### Scenario: Every contract-speaking deployable declares its range

- **WHEN** the artifacts for the proxy, the sidecar, and the client-facing terminator are each interrogated
- **THEN** each returns its own contract version range
- **AND** none of them requires a connection in order to answer

#### Scenario: The build version does not imply the contract range

- **WHEN** two artifacts with different build versions support the same contract range
- **THEN** both declare the same range
- **AND** neither range is derived from a build version

#### Scenario: An artifact declaring no range does not release

- **WHEN** an artifact for a contract-speaking component carries no contract version range
- **THEN** the release gate fails naming the absent declaration

### Requirement: Each artifact declares the durable schema version range it supports, readable without running it

Every artifact whose component operates against durable state SHALL declare the inclusive lowest and highest durable schema versions that component supports, retrievable from the artifact without starting it and without network access. `operability/schema-migration` owns what the running code does when the recorded version falls outside that range, and that the range cannot be widened at runtime; those rules hold as given. The delta here is that the range is readable from the artifact before it is deployed, so an operator can tell whether a candidate build can operate against the state an installation already holds — a question that must be answerable before a start attempt, because for durable state there is no per-connection alternative and an out-of-range version refuses startup entirely.

A component that holds no durable state SHALL declare that explicitly rather than omitting the declaration, so that an absent range is never ambiguous between "holds none" and "did not say".

`operability/schema-migration` requires every migration to be operable against by the code version immediately preceding the one that introduces it, so that two code versions can serve one durable state while a fleet is upgraded instance by instance. That obligation is discharged there and is not restated; the consequence for a release is: a candidate artifact's declared range SHALL include every schema version the release preceding it could operate against, unless the release is a declared step of a sequence that states that exclusion. A release whose artifact declares a range that excludes the version the preceding release's artifact declared as its highest SHALL fail, naming both ranges, because the two builds could then not serve one state concurrently and the upgrade the migration capability requires to be possible would not be. The comparison SHALL be made from the two artifacts' declarations, so the incompatibility is found at release rather than during the upgrade.

#### Scenario: The durable schema range is readable from a stopped artifact

- **WHEN** an operator interrogates an artifact for its durable schema support without starting it
- **THEN** the lowest and highest supported schema versions are returned

#### Scenario: An operator can tell before deploying that a build is too old for the state

- **WHEN** an installation's recorded schema version is above the highest version a candidate artifact declares
- **THEN** the operator determines the incompatibility from the artifact and the recorded version alone
- **AND** no start attempt is required to discover it

#### Scenario: Holding no durable state is declared, not omitted

- **WHEN** an artifact for a component that operates against no durable state is interrogated
- **THEN** it states explicitly that it holds none
- **AND** that is distinguishable from an artifact that failed to declare a range

#### Scenario: An absent declaration fails the release gate

- **WHEN** an artifact for a component that does operate against durable state declares no schema version range
- **THEN** the release gate fails naming the absent declaration

#### Scenario: A release that could not serve alongside its predecessor fails

- **WHEN** a candidate artifact declares a durable schema range whose lowest version is above the highest the preceding release's artifact declared
- **AND** the release is not a declared step of a sequence stating that exclusion
- **THEN** the release fails naming both ranges
- **AND** the failure is determined from the two declarations rather than by attempting the upgrade

#### Scenario: A declared sequence step may state the exclusion

- **WHEN** a release is a declared step of a sequence that states which code versions it is compatible with, and that statement excludes the preceding release
- **THEN** the release proceeds
- **AND** the exclusion is recorded with the release rather than inferred from the ranges

### Requirement: A declared range is the range the component enforces, and neither is widenable

For every range an artifact declares — contract versions, durable schema versions, and the optional capabilities the component can declare — the value read from the stopped artifact SHALL be identical to the value the started component reports and to the value it actually enforces. A discrepancy in any direction SHALL fail the release gate. This equality is what this requirement owns; the runtime consequences of a version outside a range are owned elsewhere — refusal of a tunnel with no overlapping version by `tunnel/wire-contract`, and refusal of startup against out-of-range durable state by `operability/schema-migration` — and are not restated here.

No configuration item, no deployment value, and no value supplied by a peer SHALL widen any range or capability set an artifact declares, or add a capability the build cannot perform. A capability the build cannot perform SHALL appear in neither the artifact's declaration nor the component's runtime declaration, and the two sets SHALL be identical. A configuration item attempting any of these SHALL be rejected as invalid in the single startup validation pass rather than partially honoured, and SHALL NOT cause the component to start with a declaration its artifact does not carry.

#### Scenario: The artifact's declaration is what the component enforces

- **WHEN** an artifact declaring a contract range is started and offered an exchange at a version outside that range
- **THEN** the exchange is not served
- **AND** the range the component reports is the range the artifact declared

#### Scenario: Configuration does not widen a range

- **WHEN** a deployment supplies configuration naming a contract version or a durable schema version outside the declared range
- **THEN** the declared and enforced ranges are unchanged
- **AND** the configuration is rejected as invalid rather than partially honoured

#### Scenario: A capability the build cannot perform is declared nowhere

- **WHEN** a build cannot perform an optional capability
- **THEN** that capability appears in neither the artifact's declaration nor the started component's declaration
- **AND** the two sets are identical

#### Scenario: A declaration the component contradicts fails the gate

- **WHEN** an artifact declares a range wider than the started component enforces
- **THEN** the release gate fails naming both ranges

### Requirement: Pairing viability is determinable from the artifacts alone

Given two artifacts, an operator SHALL be able to determine whether the components they contain can interoperate, without starting either and without connecting them. For any two artifacts whose components speak the wire contract to each other — a proxy and a sidecar, and equally a proxy and the client-facing terminator D16 introduces — that determination SHALL be whether their declared contract ranges overlap and whether each capability one requires of the other is in the other's declared set. For a component artifact and an installation, it SHALL be whether the declared durable schema range contains the recorded version. The determination SHALL be made by the same rule for every such pairing, and SHALL NOT be available for one pairing and unavailable for another.

A determination that requires running a component, establishing a tunnel, or reading a log SHALL NOT be considered to satisfy this requirement. Because sidecar versions in production are not the operator's to change, an operator planning a contract change against a fleet they do not control has no other way to answer the question, and answering it by deploying and observing the failure is what this requirement exists to prevent.

Where two artifacts cannot interoperate, the incompatibility SHALL be attributable to a named range rather than reported as a bare negative.

An optional capability one artifact does not declare SHALL NOT by itself make a pairing non-viable. `tunnel/wire-contract` establishes a tunnel between peers whose optional capability sets differ and refuses the individual exchange or mount that needs what the peer did not declare; that rule holds as given, and this determination SHALL therefore report a missing optional capability as the set of behaviours that pairing cannot serve, distinguishably from a non-overlapping version range, which makes the pairing unusable outright. Reporting the two the same way would tell an operator to hold back an upgrade that would in fact have worked for everything they serve.

#### Scenario: A missing optional capability narrows the pairing rather than voiding it

- **WHEN** two artifacts declare overlapping contract ranges and one declares an optional capability the other does not
- **THEN** the pairing is reported as viable
- **AND** the behaviours that require the undeclared capability are named as the ones it cannot serve
- **AND** the report is distinguishable from a pairing whose contract ranges do not overlap

#### Scenario: Two artifacts are compared without being started

- **WHEN** a proxy artifact and a sidecar artifact are each interrogated for their declared contract ranges
- **THEN** whether the pairing is viable follows from the two declarations
- **AND** neither artifact was started and no connection was made

#### Scenario: The terminator pairing is determined by the same rule

- **WHEN** a proxy artifact and a client-facing terminator artifact are each interrogated for their declared contract ranges and capability sets
- **THEN** whether that pairing is viable follows from the two declarations by the same rule as the proxy-and-sidecar pairing
- **AND** neither artifact was started and no connection was made

#### Scenario: A non-viable pairing names the range

- **WHEN** two artifacts declare non-overlapping contract ranges
- **THEN** the determination states both ranges
- **AND** the incompatibility is attributed to the contract range rather than reported as an unspecified failure

#### Scenario: An installation is checked against an artifact before deployment

- **WHEN** an operator holds an installation's recorded schema version and a candidate artifact
- **THEN** whether the artifact can operate against that state follows from the artifact's declared range
- **AND** no deployment is required to determine it

#### Scenario: A determination requiring a running component does not satisfy this

- **WHEN** the only way to learn an artifact's declared range is to start it or connect it
- **THEN** the artifact does not satisfy this requirement
- **AND** its release gate fails

### Requirement: A declared contract range is not published beyond the conformance evidence for it

That an implementation declares support for a contract version only where a conformance result exists for that version and for the capability set it declares, that the result is bound to the contract version, the suite revision, the declared capability set, the build evaluated and the configuration in effect, and that the obligation is discharged before release rather than checked on the wire, are `tunnel/wire-contract`'s and `tunnel/conformance`'s rules and hold here as given.

The delta this capability adds is that the obligation is enforced as a release gate against the artifact: a release SHALL NOT publish an artifact whose declared contract range or declared capability set exceeds the conformance evidence bound to that build, and the evidence for what an artifact declares SHALL be retrievable by an operator holding the artifact. A release that widens a declared range or a declared capability set without a result bound to the widened declaration and to that build SHALL fail.

#### Scenario: A declaration beyond the evidence blocks the release

- **WHEN** an artifact declares a contract version for which no conformance result bound to that build exists
- **THEN** the release fails
- **AND** the failure names the version and the missing evidence

#### Scenario: A widened capability set requires new evidence

- **WHEN** an artifact declares an optional capability that the build's conformance result did not cover
- **THEN** the release fails
- **AND** it does not proceed on the strength of the earlier result

#### Scenario: The evidence is retrievable by the holder of the artifact

- **WHEN** an operator holding a published artifact asks what its declared range was proven against
- **THEN** the conformance result bound to that build, that version, and that declaration is retrievable
- **AND** it states the suite revision and the configuration in effect

#### Scenario: A rebuild does not inherit the evidence

- **WHEN** a new artifact is produced with a change to the component's contract handling
- **THEN** the earlier result does not satisfy the gate for the new artifact
- **AND** the release requires a result bound to the new build

### Requirement: The same source and inputs yield an artifact identifiable as the same build

Building a component twice from the same source revision and the same pinned inputs SHALL produce artifacts identifiable as the same build. The dimensions along which two such artifacts are permitted to differ SHALL be enumerated and declared, and a difference outside that enumeration SHALL be reported as a reproducibility failure naming the differing content.

Every property of the environment a build is performed in that the artifact's content depends on SHALL be part of the recorded input set, so that a rebuild is performed against a stated environment rather than an incidental one. A build whose output depends on a property of its environment that the recorded set does not state SHALL be a reproducibility failure naming that property, and SHALL NOT be excused by the rebuild having been performed elsewhere.

The enumeration of permitted differences SHALL be a declared property of the release process rather than whatever the producing environment happens to yield, so that a newly introduced source of variation is a detected failure rather than an unnoticed widening. Widening the enumeration SHALL require an explicitly recorded approval attributed to the party granting it, SHALL NOT be applied within the same change that introduced the variation it would permit, and SHALL NOT be applied to results already recorded. Reproducibility SHALL be verified rather than asserted: a gate SHALL rebuild against the recorded input set and compare.

#### Scenario: Two builds of one revision match

- **WHEN** a component is built twice from the same source revision with the same pinned inputs
- **THEN** the two artifacts are identifiable as the same build
- **AND** any difference between them falls within the declared enumeration

#### Scenario: An undeclared difference is a failure

- **WHEN** two builds of the same revision differ in content outside the declared enumeration
- **THEN** the reproducibility gate fails
- **AND** the failure names the differing content

#### Scenario: A newly introduced source of variation is detected

- **WHEN** a change causes a build to embed a value that varies between builds of the same revision
- **THEN** the reproducibility gate fails
- **AND** extending the enumeration within that same change does not make it pass
- **AND** any widening of the enumeration records the party that approved it

#### Scenario: An unrecorded environment dependence is a failure

- **WHEN** two builds of the same revision from the same recorded input set differ because the artifact's content depends on a property of the environment the recorded set does not state
- **THEN** the reproducibility gate fails naming that property
- **AND** the failure is not excused by the rebuild having been performed in a different environment

#### Scenario: A different revision yields a different build

- **WHEN** a component is built from a source revision differing by one change
- **THEN** the artifact is not identifiable as the same build as one from the prior revision

### Requirement: An artifact carries a verifiable identity independent of where it was obtained

Every published artifact SHALL carry an identity a deployer can verify to determine that what they received is what was published, and the verification SHALL NOT depend on trusting the location the artifact was obtained from. A deployer holding only the artifact and the project's published verification material SHALL be able to complete the verification.

The identity SHALL bind the artifact's content, its provenance, and the component and platform variant it is, so that an artifact cannot be presented as a different component, a different platform variant, or a different build than the one verified. Verification SHALL be possible without starting the component.

#### Scenario: A deployer verifies what they received

- **WHEN** a deployer holds a published artifact and the project's published verification material
- **THEN** the artifact's identity verifies
- **AND** the verification requires neither trusting the location it was obtained from nor starting the component

#### Scenario: The outcome depends on content, not on origin

- **WHEN** an unaltered copy of a published artifact is obtained from a location the project does not control and verified
- **THEN** verification succeeds
- **AND** when the same copy is verified with any part of its content altered, verification fails
- **AND** neither outcome differs from the outcome for a copy obtained from the project's own location

#### Scenario: Identity binds the component and the variant

- **WHEN** an artifact is presented as a different component or a different platform variant than the one its identity binds
- **THEN** verification fails naming the mismatch

#### Scenario: Identity binds the provenance

- **WHEN** an artifact's identity is checked against the provenance it reports
- **THEN** the two agree
- **AND** a disagreement fails verification

### Requirement: A modified artifact is distinguishable from an official one

An artifact whose content has been altered after publication SHALL fail verification against the published identity, and the failure SHALL state that the content does not match rather than being reported as an absent or unreadable identity.

The identity SHALL bind every part of the artifact, including material the component does not read at run time and every declaration the artifact carries. A gate SHALL demonstrate this by altering each enumerated class of the artifact's content in turn and requiring verification to fail for every one; a class whose alteration leaves verification passing SHALL be reported as unbound, and the release SHALL NOT proceed while any class is unbound.

An artifact built by a party other than the project SHALL be distinguishable from an official one by a holder who has only the artifact and the project's published verification material — including a build produced from the project's own unmodified source, because the question a deployer asks is not whether the source was the same but whether the artifact is the one the project published.

#### Scenario: Altered content fails verification

- **WHEN** any content of a published artifact is altered
- **THEN** verification fails stating that the content does not match the published identity
- **AND** the failure is distinguishable from an artifact carrying no identity at all

#### Scenario: An unofficial build of the same source is distinguishable

- **WHEN** a third party builds the component from the project's unmodified source and publishes the result
- **THEN** a holder can determine that the artifact is not the one the project published
- **AND** the determination requires only the artifact and the project's published verification material

#### Scenario: Every class of content is bound by the identity

- **WHEN** each enumerated class of an artifact's content is altered in turn, including material the component does not read at run time and each declaration the artifact carries
- **THEN** verification fails for every one of them
- **AND** a class whose alteration leaves verification passing is reported as unbound and blocks the release

#### Scenario: A build from a modified tree is distinguishable from a release

- **WHEN** an artifact built from a modified source tree is offered as a release
- **THEN** its provenance states the tree was modified
- **AND** the release gate refuses it

### Requirement: The artifact contains only what the component needs to run

An artifact SHALL contain only the material the component requires in order to run, together with the declarations this capability requires it to carry: no source it does not read, no test material, no fixture, no development or example tooling, no documentation beyond what it serves, and no second component. A release gate SHALL enumerate the artifact's contents and fail on the presence of a class of material the component does not need at run time.

The declarations this capability requires an artifact to carry — its configuration schema, its generated configuration declaration, its external-dependency declaration, its provenance, its declared version ranges, its dependency inventory, and the terms under which it redistributes what it contains — SHALL be present and SHALL NOT be reported by this gate as material the component does not need. Their absence SHALL fail their own requirement's gate. The two gates SHALL be enumerated so that no obligation of this capability is satisfiable only by violating another.

The reference system got this right for the component tenants run and wrong for the one that terminates untrusted traffic, which is the inversion this requirement exists to prevent: the obligation is heaviest on the component with the largest attack surface, and it SHALL NOT be satisfied for one deployable and waived for another.

#### Scenario: Non-runtime material is absent

- **WHEN** the contents of any published artifact are enumerated
- **THEN** no test material, fixture, development tooling, or unused source is present

#### Scenario: The check binds every deployable

- **WHEN** the contents check is applied to the proxy's artifact, the sidecar's artifact, and the client-facing terminator's artifact
- **THEN** the same enumeration and the same failure conditions apply to each

#### Scenario: An added class of material fails the gate

- **WHEN** a change causes an artifact to include a class of material the component does not read at run time
- **THEN** the gate fails naming that material

#### Scenario: Removing needed material fails the start gate instead

- **WHEN** material the component does read at run time is excluded from the artifact
- **THEN** the artifact fails to start and report ready
- **AND** the failure is reported by the start gate rather than by the contents check

### Requirement: Construction-time material does not reach the artifact

No material whose only purpose was to construct the artifact SHALL be present in the published artifact: no tool used to produce or assemble it, no material retained only to make a later construction faster, no intermediate product of construction, and no credential used to obtain an input. Where an artifact is constructed in more than one step, material present in an earlier step SHALL NOT be present in the runnable result unless the component reads it at run time.

A release gate SHALL detect construction-time material in the published artifact and fail naming it. This is distinct from the configuration case: a value declared in a construction step and lost is a start failure, while a construction tool retained in the runnable result is a surface the component does not need and an operator did not agree to run.

#### Scenario: No construction tooling is present

- **WHEN** the published artifact's contents are enumerated
- **THEN** no tool used to produce or assemble the artifact is present
- **AND** no material retained only to make a later construction faster is present

#### Scenario: A credential used to obtain an input does not persist

- **WHEN** an input is obtained during construction using a credential
- **THEN** that credential is absent from the published artifact
- **AND** the gate fails if it is present

#### Scenario: Intermediate material does not carry through

- **WHEN** an artifact is constructed in more than one step
- **THEN** no intermediate product of an earlier step is present in the runnable result unless the component reads it at run time

#### Scenario: The failure is distinguishable from a lost configuration value

- **WHEN** construction-time material is found in a published artifact
- **THEN** the gate names it as construction-time material retained
- **AND** the report is distinguishable from a configuration value that failed to reach the artifact

### Requirement: An artifact requires no more privilege than the component needs

Every artifact SHALL run as an unprivileged identity, SHALL require no privileged capability of its host, and SHALL require no writable location other than one it was explicitly configured with. Where a component requires no writable location, it SHALL run with none available. This binds every deployable — the reference system granted it to the component tenants run and not to the one terminating untrusted traffic — and SHALL be proven by a gate. `sidecar/program` does not restate it; it adds only that the sidecar's one permitted writable location is the credential store path it was configured with, that it requires none where no store is configured, and that it acquires none for diagnostics, body spooling, or a cache, because it shares the machine with the backend it serves.

The gate SHALL start the published artifact as an unprivileged identity with no privileged capability granted and every location read-only except those the configuration declares, and SHALL require readiness under those conditions. A component that reaches readiness only with a privilege it does not declare SHALL fail the gate naming the privilege.

#### Scenario: Every artifact starts unprivileged

- **WHEN** each published artifact is started as an unprivileged identity with no privileged capability granted
- **THEN** each starts and reports itself ready

#### Scenario: Only declared writable locations are available

- **WHEN** an artifact is started with every location read-only except those its configuration declares writable
- **THEN** it starts and reports itself ready

#### Scenario: An undeclared privilege requirement fails the gate

- **WHEN** a component reaches readiness only when granted a privileged capability its declaration does not name
- **THEN** the gate fails naming the privilege
- **AND** the release does not proceed

#### Scenario: An undeclared writable location fails the gate

- **WHEN** a component reaches readiness only when a location its configuration does not declare is writable
- **THEN** the gate fails naming the location

### Requirement: No artifact contains a secret, and the release gate proves it

No artifact SHALL contain any secret: no credential, no key, no protection material, no token, and no value the configuration schema marks as secret. A secret present in a distributed artifact is disclosed to every party who can obtain that artifact, and no access control on the distribution location changes that, because artifacts are copied.

An artifact SHALL NOT carry a value for any item the schema marks as secret — not a placeholder that validates, not an example value, and not a development or test value. That a component refuses to start where a configured item equals a value published in the project's own example, development, or test configuration or shipped in any artifact, and that the material protecting stored items is never embedded in a shipped artifact, image, or package, are `security/key-custody`'s rules and hold as given; the delta here is that no value for a secret item SHALL be in the artifact in the first place, whatever class of material it belongs to, and that a gate SHALL prove its absence before publication rather than leaving the absence to be discovered by a component refusing to start.

A secret found in an artifact after publication SHALL be treated as disclosed and rotated, and SHALL NOT be treated as remediated by republishing the artifact without it.

#### Scenario: A secret in an artifact blocks the release

- **WHEN** a value for an item the schema marks as secret is present in an artifact being released
- **THEN** the gate fails naming the item
- **AND** the artifact is not published

#### Scenario: A placeholder that validates is still a secret in the artifact

- **WHEN** an artifact carries, for a secret item, a value that would pass validation
- **THEN** the gate fails
- **AND** the failure is not waived on the ground that the value is not a real credential

#### Scenario: Material retained from construction is detected

- **WHEN** a credential used during construction remains anywhere in the published artifact, including in material the component does not read
- **THEN** the gate fails naming where it was found

#### Scenario: A secret published in an artifact is treated as disclosed

- **WHEN** a secret is found in an already-published artifact
- **THEN** it is treated as disclosed and rotated
- **AND** republishing the artifact without it is not treated as remediation on its own

### Requirement: Every input is pinned to an immutable identity

Every input an artifact is built from SHALL resolve to one immutable identity recorded before the build, so that two builds of one source revision draw the same inputs. An input specified in a form that can resolve to different content at different times SHALL fail the build naming that input.

This SHALL apply to every class of input, including inputs the artifact inherits rather than names directly and inputs drawn only because another input requires them, and SHALL NOT be satisfied for the directly named inputs alone. A build that resolves an input by whatever is current at the time it runs SHALL be treated as unreproducible, because it is: the reproducibility gate and the pinning gate constrain the same property from two directions.

#### Scenario: A floating input fails the build

- **WHEN** an input is specified in a form that can resolve to different content at different times
- **THEN** the build fails naming that input

#### Scenario: Transitive inputs are pinned too

- **WHEN** the recorded input set for a build is examined
- **THEN** every input, including transitive ones and those the artifact inherits rather than names directly, resolves to one immutable identity

#### Scenario: The recorded input set reproduces the build

- **WHEN** a component is rebuilt using only the recorded input set
- **THEN** the inputs drawn are identical to those of the original build
- **AND** the artifact is identifiable as the same build

#### Scenario: A changed input is a changed build

- **WHEN** an input's pinned identity is advanced
- **THEN** the resulting artifact is not identifiable as the same build as before the advance
- **AND** the change is attributable to that input

#### Scenario: An unresolvable pinned identity fails rather than substitutes

- **WHEN** a rebuild draws an input whose recorded pinned identity no longer resolves to any content
- **THEN** the build fails naming that input and its recorded identity
- **AND** no other content is substituted for it
- **AND** the failure is distinguishable from the input having changed content under the same identity

#### Scenario: Content that changed under a pinned identity is a failure

- **WHEN** an input resolves at its recorded identity to content differing from the content that identity recorded
- **THEN** the build fails naming that input
- **AND** the artifact is not published

### Requirement: The dependency inventory is discoverable from the artifact and matches its contents

Every artifact SHALL carry an inventory of the dependencies it contains, retrievable without starting the component and without network access, naming each dependency and the pinned identity it was drawn at. The inventory SHALL include transitive dependencies and everything the artifact inherits rather than names directly, because a vulnerability in an input nobody named directly is not a lesser vulnerability.

The inventory SHALL match the artifact's actual contents. A release gate SHALL compare the two and fail on a dependency present in the artifact and absent from the inventory, or named in the inventory and absent from the artifact.

#### Scenario: The inventory is readable from a stopped artifact

- **WHEN** an operator interrogates a published artifact for its dependency inventory without starting it and with no network available
- **THEN** the complete inventory is returned with each dependency's pinned identity

#### Scenario: A dependency absent from the inventory fails the gate

- **WHEN** an artifact contains a dependency the inventory does not name
- **THEN** the gate fails naming that dependency

#### Scenario: A dependency named but not present fails the gate

- **WHEN** the inventory names a dependency the artifact does not contain
- **THEN** the gate fails naming that dependency

#### Scenario: Transitive dependencies are inventoried

- **WHEN** a dependency is included only because another dependency requires it
- **THEN** it appears in the inventory with its pinned identity

#### Scenario: An artifact with no inventory does not release

- **WHEN** an artifact carries no dependency inventory, or carries one retrievable only over the network or only by starting the component
- **THEN** the release gate fails naming the artifact
- **AND** an empty inventory is not accepted as evidence that the artifact contains no dependency

#### Scenario: An inventory naming no pinned identity is incomplete

- **WHEN** the inventory names a dependency without the pinned identity it was drawn at
- **THEN** the gate fails naming that dependency
- **AND** the entry is not treated as satisfying the inventory for that dependency

### Requirement: Everything an artifact redistributes carries an established origin and stated terms

An artifact is distributed to parties outside the operator, the sidecar's to every tenant. For every item an artifact contains that the project did not author — every dependency, and every non-code item it carries such as an asset it serves — the origin and the terms under which it may be redistributed SHALL be established and recorded before publication, and SHALL be retrievable by a holder of the artifact without starting the component.

An item whose origin cannot be established SHALL NOT be included in a published artifact, and a blanket statement of terms covering the artifact as a whole SHALL NOT be treated as establishing the terms of an item it contains. A release gate SHALL compare the recorded terms against the artifact's contents and fail on an item present with no established origin or no stated terms, and on a recorded item absent from the artifact.

An item whose terms forbid redistribution, or whose terms impose an obligation the release does not discharge, SHALL block the release naming the item and the obligation. This requirement binds every deployable: the reference system shipped a body of non-code assets of unestablished origin under one blanket claim with no attribution, for a feature that was inert in production, and no gate objected.

#### Scenario: Every redistributed item has an established origin

- **WHEN** the contents of any published artifact are enumerated against the recorded origins and terms
- **THEN** every item the project did not author has an established origin and stated terms
- **AND** the record is retrievable by a holder of the artifact without starting the component

#### Scenario: An item of unestablished origin blocks the release

- **WHEN** an artifact contains an item whose origin is not established
- **THEN** the release does not proceed
- **AND** the block names that item
- **AND** a blanket statement covering the artifact as a whole does not satisfy the gate for it

#### Scenario: Terms that forbid redistribution block the release

- **WHEN** an item's recorded terms forbid redistribution, or impose an obligation the release does not discharge
- **THEN** the release does not proceed
- **AND** the block names the item and the obligation not discharged

#### Scenario: The record and the contents must agree

- **WHEN** the recorded set of redistributed items and the artifact's actual contents differ in either direction
- **THEN** the gate fails naming the item and which of the two carried it

#### Scenario: The obligation binds every deployable

- **WHEN** the check is applied to the proxy's artifact, the sidecar's artifact, and the client-facing terminator's artifact
- **THEN** the same enumeration and the same blocking conditions apply to each
- **AND** no artifact is exempted on the ground that the operator deploys it itself

### Requirement: A published version identifier is never reused for different content

Once an artifact has been published under a version identifier, that identifier SHALL NOT be published again with different content, for that component and platform variant. An attempt to publish content differing from what that identifier already carries SHALL be refused naming the identifier and both verifiable identities, and SHALL NOT be resolvable by overwriting.

This obligation is load-bearing because tenants pin sidecar versions indefinitely and the operator cannot make them move. Every guarantee this capability establishes — a gate outcome, a conformance result, a dependency inventory, a declared version range — is bound to an artifact's verifiable identity and is worthless if the identifier an operator or a tenant pins can come to mean different content later.

Withdrawing a published artifact SHALL be possible, SHALL be recorded with the reason and the party withdrawing it, and SHALL NOT release the identifier for reuse: a withdrawn identifier SHALL remain permanently attributable to the content it carried, and an attempt to republish it with different content SHALL be refused on the same terms as any other reuse.

#### Scenario: Republishing an identifier with different content is refused

- **WHEN** a release attempts to publish, under a version identifier already published for that component and variant, content whose verifiable identity differs
- **THEN** the publication is refused
- **AND** the refusal names the identifier and both verifiable identities
- **AND** the already-published content is unchanged

#### Scenario: Republishing identical content is not a violation

- **WHEN** a publication is attempted for an identifier already published, with content whose verifiable identity is identical
- **THEN** the already-published content is unchanged
- **AND** the attempt is not reported as a reuse violation

#### Scenario: A withdrawn identifier is not reusable

- **WHEN** a published artifact is withdrawn and a later release attempts to publish different content under the same identifier
- **THEN** the publication is refused
- **AND** the withdrawal record names the reason and the withdrawing party
- **AND** the identifier remains attributable to the content it carried

#### Scenario: A recorded guarantee stays bound to the content it evaluated

- **WHEN** a gate outcome, a conformance result, or a dependency inventory is retrieved for a version identifier
- **THEN** it is bound to the verifiable identity of the content that identifier carries
- **AND** it is not returned for content that identity does not match

### Requirement: A known-vulnerable input blocks release, and an exception is explicit and bounded

Every input in an artifact's inventory SHALL be assessed against known vulnerabilities before the artifact is published. An input with a known vulnerability at or above a declared severity threshold SHALL block the release, and the block SHALL name the input, the vulnerability, and the pinned identity that carries it.

An exception SHALL be possible but SHALL be explicit: recorded, attributed to the party accepting it, carrying the reason it was accepted, and bounded by a declared expiry after which it no longer suppresses the block. An exception SHALL NOT be expressible as a permanent suppression, and an expired exception SHALL restore the block rather than being renewed silently.

The assessment SHALL apply identically to every component. The reference system screened the component tenants run and left the one terminating untrusted traffic with no screening at all, which is the inversion this requirement forbids.

#### Scenario: A vulnerable input blocks the release

- **WHEN** an input in an artifact's inventory has a known vulnerability at or above the declared threshold
- **THEN** the release does not proceed
- **AND** the block names the input, the vulnerability, and the pinned identity

#### Scenario: Every component is assessed by the same rule

- **WHEN** the assessment is applied to the proxy's, the sidecar's, and the client-facing terminator's artifacts
- **THEN** the same threshold and the same blocking behaviour apply to each

#### Scenario: An exception is attributed and bounded

- **WHEN** a block is accepted as an exception
- **THEN** the exception records the accepting party, the reason, and an expiry
- **AND** it cannot be recorded without an expiry

#### Scenario: An expired exception restores the block

- **WHEN** an exception's expiry has passed and the vulnerability is still present
- **THEN** the release is blocked again
- **AND** the block is not suppressed by the expired exception

### Requirement: The vulnerability assessment recurs on a schedule and is attributed to the released artifact

The assessment SHALL be performed on a declared recurring interval as well as on every change, because a disclosure arrives without a change to the source and an artifact that was clean when published does not stay clean. The recurring assessment SHALL be performed against the currently published artifacts and their inventories, not against the current source alone.

Its outcome SHALL be observable, and a newly disclosed vulnerability in a published artifact SHALL produce a report naming the artifact, the input, and the vulnerability, whether or not any change has been made since publication. An interval elapsing without an assessment SHALL itself be reported rather than passing unnoticed.

#### Scenario: A disclosure with no change is found

- **WHEN** a vulnerability is disclosed in an input of an already-published artifact and no change has been made to the source
- **THEN** the recurring assessment reports it within its declared interval
- **AND** the report names the published artifact, the input, and the vulnerability

#### Scenario: The assessment reads the published artifact's inventory

- **WHEN** the recurring assessment runs
- **THEN** it assesses the inventories of the currently published artifacts
- **AND** it is not satisfied by assessing the current source alone

#### Scenario: A missed interval is reported

- **WHEN** the declared interval elapses with no assessment performed
- **THEN** that is reported
- **AND** it is not treated as an assessment with no findings

#### Scenario: The outcome is observable

- **WHEN** an operator asks when the published artifacts were last assessed and with what result
- **THEN** the time and the outcome of the most recent assessment are retrievable

#### Scenario: An assessment that could not obtain vulnerability information is not a clean result

- **WHEN** an assessment runs but cannot obtain the vulnerability information it assesses against, or assesses only part of the published artifact set
- **THEN** it is reported as not performed, naming what it could not assess
- **AND** it does not satisfy the interval
- **AND** it is not recorded as an assessment with no findings

#### Scenario: An artifact no longer assessable is reported rather than dropped

- **WHEN** a published artifact's inventory cannot be retrieved for the recurring assessment
- **THEN** that artifact is reported as unassessed naming why
- **AND** it is not omitted from the assessment's scope silently

### Requirement: An unattended input advance never changes a declared range or the wire contract

An input advance applied without human approval SHALL NOT be capable of changing an artifact's declared contract version range, its declared durable schema version range, its declared capability set, or the wire contract itself. A release gate SHALL compare those declarations before and after any unattended advance and SHALL refuse the advance where any of them differs.

An advance beyond a declared class of change SHALL require human approval, and the class SHALL be evaluated from the advance itself rather than from a description of it. The reference system invoked a check that classified each advance and then never read its result, so every advance merged on the terms of the smallest, and an advance to the component encoding the wire protocol reached the released state with nobody in the loop.

#### Scenario: An advance that moves a declared range is refused

- **WHEN** an unattended input advance would change an artifact's declared contract range, durable schema range, or capability set
- **THEN** the advance is refused
- **AND** the refusal names the declaration that would have changed

#### Scenario: The classification is read, not merely produced

- **WHEN** an advance deliberately constructed to fall beyond the class permitted without approval is offered
- **THEN** it does not proceed without approval
- **AND** the refusal names the class the advance was assigned
- **AND** an invocation that produces a classification and then admits the advance on the terms of the smallest class is reported as not satisfying this requirement

#### Scenario: A wire-contract input never advances unattended

- **WHEN** an unattended advance would change the wire contract or the material generated from it
- **THEN** it is refused regardless of the class it would otherwise be assigned

#### Scenario: A permitted advance still passes every gate

- **WHEN** an advance within the permitted class proceeds
- **THEN** the resulting artifact still passes every release gate before publication
- **AND** it is not published on the strength of the advance's class alone

### Requirement: Every release gate is demonstrated to fail against a deliberately non-conforming artifact

Each release gate this capability requires SHALL be demonstrated to fail against an artifact deliberately constructed to violate the specific obligation that gate exists to enforce. The demonstration SHALL be executed automatically rather than asserted by inspection, and a gate with no such demonstration SHALL NOT be counted as a gate.

The catalogue this requirement establishes is a catalogue of defective **artifacts**, and is distinct from `tunnel/conformance`'s catalogue of defective wire counterparts. Neither SHALL substitute for the other: an artifact defect is not detectable by running the conformance suite, and a wire defect is not detectable by inspecting an artifact. A gate for a packaging obligation SHALL NOT be discharged by a conformance result, and a conformance obligation SHALL NOT be discharged by a packaging gate outcome.

A catalogue of deliberately non-conforming artifacts SHALL be maintained, each defective in one named way and each paired with the gate whose obligation it violates. At minimum the catalogue SHALL include: an artifact whose declared configuration set diverges from the schema; one whose declaration was lost between construction stages; one that cannot start without an undeclared external dependency; one that becomes ready only with a relaxed protective value; one whose provenance a configuration item can restate; one declaring a contract range wider than it enforces; one whose declared durable schema range excludes the highest version the preceding release declared; one declaring a contract version with no conformance evidence; one that is not reproducible; one whose content has been altered after publication; one retaining construction-time material; one requiring an undeclared privilege; one containing a value for a secret item; one carrying a floating input; one whose inventory omits a dependency it contains; one carrying an input with a known vulnerability above the threshold; one redistributing an item whose origin or distribution terms are not established; and one published under a version identifier already published with different content.

Running the gates against each catalogue member SHALL produce a failure naming the obligation that member violates, and running them against the same artifact with the defect removed and nothing else changed SHALL produce a pass. Where a requirement of this capability is added, the catalogue SHALL gain a member that violates it before the requirement is considered gated.

#### Scenario: Each deliberate defect is detected

- **WHEN** the gates are run against a member of the catalogue
- **THEN** at least one gate fails
- **AND** the failure names the obligation that member violates

#### Scenario: The corrected artifact passes

- **WHEN** the gates are run against the same artifact with the defect removed and nothing else changed
- **THEN** every gate passes

#### Scenario: A gate with no demonstration is not a gate

- **WHEN** a release gate has no catalogue member demonstrating that it fails
- **THEN** it is reported as unverified
- **AND** the release does not count it as satisfied

#### Scenario: A new obligation gains a defect before it counts as gated

- **WHEN** a requirement is added to this capability
- **THEN** the catalogue gains a member that violates it and the gates are demonstrated to reject that member
- **AND** until then the obligation is reported as ungated

#### Scenario: A defect detected by the wrong gate is reported

- **WHEN** a catalogue member is rejected by a gate other than the one it is paired with
- **THEN** the pairing is reported as incorrect
- **AND** the paired gate is reported as unverified

#### Scenario: Neither catalogue stands in for the other

- **WHEN** an artifact defective in one of the ways enumerated here is evaluated by a conformance run, and a wire counterpart defective in one of the ways `tunnel/conformance` enumerates is evaluated by the packaging gates
- **THEN** neither evaluation detects the other's defect
- **AND** a packaging obligation reported as discharged by a conformance result is reported as ungated
- **AND** a conformance obligation reported as discharged by a packaging gate outcome is reported as unproven

### Requirement: A gate that does not execute is a failure, never a pass

This requirement owns the rule for every gate whose outcome a release or a merge depends on, including the gate that runs the conformance suite. `tunnel/conformance` states, and retains, only what is specific to that gate — that it must be demonstrated to fail its caller on a non-conformant verdict — and does not restate this rule.

An invocation intended to run a gate that executes nothing, cannot find what it was meant to run, is misconfigured, or exits without evaluating its obligation SHALL be treated as a failed gate. It SHALL NOT be reported as a clean result, and the release or merge it protects SHALL NOT proceed on its outcome.

Where the same obligation is enforced in more than one place — a local guardrail and a release gate, for instance — each invocation SHALL be verified independently, because the reference system's local guardrail invoked a misspelled option and therefore silently enforced nothing for months while the release gate ran the correct one and nobody compared them. Two invocations of one obligation SHALL be demonstrated to reject the same catalogue member, and a divergence between them SHALL be reported.

A gate's own verification SHALL be executed on a declared recurring interval as well as on change, so that a gate broken by a change elsewhere is found without waiting for a change to the gate.

#### Scenario: A no-op invocation fails

- **WHEN** an invocation intended to run a gate evaluates no obligation
- **THEN** the gate is reported as failed
- **AND** the release does not proceed on its outcome

#### Scenario: A misconfigured invocation is reported, not silently clean

- **WHEN** a gate invocation is misconfigured such that it cannot run what it was meant to run
- **THEN** the misconfiguration is reported
- **AND** it is not recorded as a clean run

#### Scenario: Two invocations of one obligation are compared

- **WHEN** the same obligation is enforced by a local guardrail and by a release gate
- **THEN** both are demonstrated to reject the same catalogue member
- **AND** a divergence between what they enforce is reported

#### Scenario: Gate verification recurs

- **WHEN** the declared interval elapses with no change to any gate
- **THEN** the gate verification has nevertheless executed within that interval
- **AND** its outcome is observable

### Requirement: The gate set is enumerated and a release records which gates it passed

The set of gates that must pass before an artifact is published SHALL be enumerated, and a release SHALL record, per artifact and per published platform variant, the outcome of every gate in that set. A release in which any gate in the set has no recorded outcome for an artifact SHALL NOT proceed, and an absent outcome SHALL NOT be treated as a pass.

The recorded outcomes SHALL be retrievable after publication, bound to the artifact's verifiable identity, so that an operator holding an artifact can determine which gates it passed, at what content, and when. A gate added to the set SHALL apply to the next release rather than being deemed satisfied by earlier ones.

#### Scenario: Every gate has a recorded outcome per variant

- **WHEN** a release is examined
- **THEN** every gate in the enumerated set has a recorded outcome for every published artifact and platform variant

#### Scenario: An absent outcome is not a pass

- **WHEN** a gate in the set has no recorded outcome for an artifact
- **THEN** the release does not proceed
- **AND** the refusal names the gate and the artifact

#### Scenario: The outcomes are retrievable by the holder of the artifact

- **WHEN** an operator holding a published artifact asks which gates it passed
- **THEN** the recorded outcomes are retrievable and bound to that artifact's verifiable identity

#### Scenario: A newly added gate is not retroactively satisfied

- **WHEN** a gate is added to the enumerated set
- **THEN** the next release records its outcome
- **AND** earlier releases are not reported as having passed it
