## Purpose

Defines the sidecar as a program a tenant runs inside their own infrastructure, rather than as a peer that speaks the wire contract. It covers what the sidecar must be configured with and how it refuses to run without it, how it starts, signals readiness, drains and exits, how it composes and dials the request against the tenant's backend from local configuration alone, how it protects, bounds and manages the one hop no other capability owns, how it performs the translation only a component adjacent to the backend can perform, how it protects a credential on somebody else's disk, what an operator with no access to the proxy can see when it is stuck, and the bounds it imposes on itself so that it cannot exhaust the machine it shares with the backend it serves.

Two conditions govern everything here. The operator cannot upgrade this artifact, cannot see the machine it runs on, and cannot read its logs; and the tenant's platform team decides whether it is allowed to run at all. So its configuration must be discoverable without a support conversation, its failures must be attributable from inside the tenant's own infrastructure, and it must never be able to be steered by the traffic it carries.

One boundary is load-bearing. `operability/packaging` owns every obligation the sidecar carries as a distributed artifact in common with the proxy and the client-facing terminator — that it is one self-contained artifact, that what it declares about its own configuration is generated from the schema its startup validation reads, that its provenance is fixed when it is produced, that the contract and durable-schema version ranges it supports are readable from it while stopped, that it requires no privilege it does not declare, that it carries no secret, and every release gate that proves those things. This capability states only the delta that follows from the machine being the tenant's, and where it states one of those obligations it does so as the tenant-specific instance of packaging's rule, never as a second statement of it.

## ADDED Requirements

### Requirement: Configuration is a declared schema

The sidecar SHALL have a declared configuration schema that is the single enumeration of every value its behaviour depends on. For each item the schema SHALL state its name, its accepted form, whether it is required, whether it carries a secret, and the bound or set of values it accepts. The sidecar SHALL NOT consult any configuration item absent from the schema, and no code path SHALL read a value the schema does not declare.

An item present in the sidecar's own reserved configuration namespace that the schema does not declare SHALL be reported as a validation failure naming it, together with the declared names most closely resembling it. A misspelled name is otherwise indistinguishable from an omitted one, which is the condition that makes discovering the required set expensive.

That the schema is retrievable from the artifact itself without starting it and without network access, that the retrieved schema is the one the startup validation reads, and that a schema an artifact discloses only when started fails a release gate, are `operability/packaging`'s obligations on every deployable and hold here as given. What this requirement owns is the schema's content and closure for the sidecar: that it is the single enumeration, that nothing outside it is consulted, and that a name resembling a declared one is reported rather than ignored.

#### Scenario: The schema enumerates every consulted value

- **WHEN** the artifact is interrogated for its schema, and is then started with exactly the items that interrogation returned and nothing else
- **THEN** it passes validation, starts, and serves
- **AND** the set of items it reports as in force is the set the interrogation returned, item for item

#### Scenario: An unknown item in the reserved namespace is a failure

- **WHEN** the sidecar is started with an item in its own configuration namespace that the schema does not declare
- **THEN** it refuses to start
- **AND** the refusal names that item
- **AND** the refusal names the declared item it most closely resembles

#### Scenario: Unrelated configuration outside the namespace is ignored

- **WHEN** the environment the sidecar starts in carries configuration belonging to other software
- **THEN** those items are neither consulted nor reported as failures

#### Scenario: The enumeration is closed in both directions

- **WHEN** each item the schema declares is varied across the values it accepts in turn
- **THEN** each variation produces an observable difference in the sidecar's behaviour
- **AND** an item whose variation produces none is reported as a schema entry the sidecar does not consult
- **AND** a behaviour that varies with no schema item is reported as a value consulted from outside the schema

### Requirement: Each value in force is attributable to the operator or to the shipped configuration

That every value the sidecar's behaviour depends on is explicitly configured, that a missing required value is a refusal rather than an implicit default, and that a defensible default is carried by the configuration the artifact ships with rather than by the code that reads it, are the observability capability's rules and hold here as given. What this capability adds is that the origin of each value in force is reportable, and that emptiness is not absence.

The sidecar SHALL report, for every schema item, whether the value in force came from the operator or from the shipped configuration. It SHALL report that origin for an operator-supplied value that happens to equal the shipped default, rather than collapsing the two.

A required item supplied with an empty value, or with a value consisting only of separating whitespace, SHALL be a validation failure. It SHALL be reported distinguishably from that item being absent, SHALL NOT be accepted as a supplied value, and SHALL NOT cause a shipped default to be applied in its place.

#### Scenario: A default in force is distinguishable from a set value

- **WHEN** the configuration in force is reported
- **THEN** each item states whether its value came from the operator or from the shipped configuration

#### Scenario: A set value equal to the default is still attributed to the operator

- **WHEN** an operator supplies, for an item with a shipped default, the same value that default states
- **THEN** the reported origin of that value is the operator
- **AND** it is distinguishable from the same item left unset

#### Scenario: An empty value is not treated as absent

- **WHEN** a required item is supplied with an empty value
- **THEN** the sidecar refuses to start naming that item
- **AND** the refusal distinguishes an empty value from an absent one
- **AND** no shipped default is applied in its place

#### Scenario: A whitespace-only value is not a value

- **WHEN** a required item is supplied with a value consisting only of separating whitespace
- **THEN** the sidecar refuses to start naming that item
- **AND** the outcome is the same as for an empty value and differs from a value that was accepted

### Requirement: Validation completes before the credential, the endpoint, or the backend is touched

That configuration validation is a single pass, and that one refusal names every failing item with what was wrong with each, are the observability capability's rules and hold here as given. What this capability adds is what that pass must precede on a sidecar, which is everything: it SHALL complete before the sidecar opens or accepts any connection, contacts the tunnel endpoint, reads or decrypts its credential store, or dials the backend.

A refusal SHALL therefore be reachable with the tunnel endpoint unresolvable, the credential store absent, and the backend not running, and SHALL name exactly the faults it would name with all three available. No fault the schema can detect SHALL be deferred to the moment the item is first used, because an item consulted only when a bidirectional stream is established would otherwise fail days after the deployment that broke it.

#### Scenario: Refusal precedes every connection

- **WHEN** the sidecar refuses to start on configuration validation
- **THEN** no connection to the tunnel endpoint was attempted at any point
- **AND** no connection to the backend was attempted
- **AND** no credential store was read or decrypted
- **AND** no local surface accepted a connection

#### Scenario: Validation does not depend on any dependency being available

- **WHEN** the sidecar is started with a faulty configuration, an unresolvable tunnel endpoint, no credential store, and no backend running
- **THEN** it refuses to start
- **AND** the faults named are exactly those named for the same configuration with all three dependencies available

#### Scenario: A fault is not deferred to first use

- **WHEN** the sidecar is started with a fault in an item consulted only when a bidirectional stream is established
- **THEN** it refuses to start naming that item
- **AND** it does not start and fail when the first such stream arrives

### Requirement: Validation covers form, range, and relationships between items

Validation SHALL reject an item that is present but unparseable, present but outside its declared bound, or present but inconsistent with another item, and SHALL report each such fault in the same pass as absent items. Presence SHALL NOT be accepted as a substitute for validity.

The relationships validated SHALL include at minimum: that an ordering between two configured durations is satisfied where one must complete inside the other; that a bound the sidecar declares over the tunnel is consistent with the bound it enforces locally on the same dimension; that mutually exclusive items are not both set; and that an item required only because another is set is present when it is. A relationship fault SHALL name both items, not one.

#### Scenario: An unparseable value is a fault, not a default

- **WHEN** an item declared to be a duration is supplied with a value that is not one
- **THEN** the sidecar refuses to start naming that item and its declared form
- **AND** it does not proceed with any substituted value

#### Scenario: An out-of-range value is rejected with its bound

- **WHEN** an item is supplied with a value outside its declared bound
- **THEN** the refusal names the item, the supplied value, and the bound

#### Scenario: An inconsistent pair names both items

- **WHEN** a drain period is configured longer than the shutdown deadline it must complete inside
- **THEN** the sidecar refuses to start
- **AND** the refusal names both items and the relationship between them

#### Scenario: A conditionally required item is enforced

- **WHEN** an item is set whose presence makes a second item required
- **AND** that second item is absent
- **THEN** the refusal names the second item and the item that required it

### Requirement: The configuration in force is retrievable on demand and secrets are reported as presence alone

That the configured values in force are recorded at startup with secrets redacted is the observability capability's rule and holds here as given. What this capability adds is that the same set SHALL be retrievable on demand from the sidecar's local operational surface for as long as it runs, that the retrieved set SHALL match the recorded one and both SHALL match the values the sidecar actually applies, and that the redaction is total rather than partial.

Every item the schema marks as carrying a secret SHALL be reported as present or absent and never by value, in whole or in part. No prefix, suffix, length, or digest of a secret value SHALL be reported, because a length or a digest is enough to confirm a guess. A non-secret identifier of the credential the sidecar holds MAY be reported, because it is what correlates the sidecar with the proxy's own records.

#### Scenario: Secrets are reported as presence only

- **WHEN** the configuration in force is recorded or retrieved
- **THEN** each secret item is reported as present or absent
- **AND** no octet, prefix, length, or digest of any secret value appears

#### Scenario: The retrieved set matches the recorded set

- **WHEN** an operator retrieves the configuration in force from a running sidecar
- **THEN** it matches what was recorded at startup item for item
- **AND** every schema item appears in it, including those that are absent

#### Scenario: A secret is not confirmable by length or digest

- **WHEN** two sidecars are configured with secret values of different lengths and different contents
- **THEN** neither report discloses a length, a prefix, a suffix, or a digest
- **AND** the two reports are indistinguishable in respect of those items beyond stating each as present

### Requirement: Configuration is fixed for the lifetime of the process

The sidecar SHALL apply its configuration once, at startup, and SHALL NOT re-read, reload, or otherwise change any configured value while it runs. A configuration change SHALL take effect by starting a new instance, and the sidecar SHALL NOT offer a signal, surface, or command that alters a value in force.

This is not an omission. The parameters the sidecar declares when it establishes a tunnel are fixed for that tunnel's life by the wire contract, and a reload would silently put the declared parameter and the enforced parameter into disagreement. Because a change requires a restart, the sidecar's diagnostics SHALL be sufficient at their default level rather than requiring verbosity to be raised, since raising it would destroy the state being diagnosed.

#### Scenario: A running sidecar does not change its configuration

- **WHEN** the configuration source the sidecar started from is altered while it runs
- **THEN** the values in force are unchanged
- **AND** the values it reports are unchanged

#### Scenario: No reload signal exists

- **WHEN** every signal and every local surface the sidecar exposes is exercised
- **THEN** none of them changes a configured value in force

#### Scenario: Declared and enforced bounds cannot diverge

- **WHEN** a sidecar has established a tunnel declaring a concurrency and a frame-size bound
- **THEN** the bounds it enforces for the life of that tunnel are the ones it declared
- **AND** no change to its configuration source alters either

### Requirement: The sidecar's footprint on the tenant's machine is the configured store path alone

That the sidecar is released as one self-contained artifact requiring no interpreter, no toolchain, no companion artifact, no construction step at the destination and no retrieval of any part of itself; that it starts in an environment containing nothing but itself and its declared external dependencies; and that it runs as an unprivileged identity requiring no privileged capability of its host and no writable location other than one it was explicitly configured with, are `operability/packaging`'s obligations on every deployable and hold here as given. What this capability adds is the narrowing that follows from the machine being the tenant's rather than the operator's: the sidecar shares it with the backend it serves, and the tenant's platform team decides whether it may run at all.

The one writable location the sidecar MAY require SHALL be the credential store path it was configured with. Where no credential store is configured it SHALL require none, and SHALL start and serve with every location it can see read-only. It SHALL NOT require a writable location in order to record diagnostics, to spool a request or response body, or to hold any cache, and it SHALL NOT acquire one for those purposes while it runs.

A configured store path the sidecar cannot read or write SHALL be a refusal naming that path and the access it lacked, reported in the single startup validation pass rather than at first use, and distinguishable from a store that is present and empty.

#### Scenario: No writable location is required without a store

- **WHEN** the artifact is started with no credential store configured and every location it can see is read-only
- **THEN** it starts and serves normally

#### Scenario: The configured store is the only location written

- **WHEN** a sidecar with a configured credential store serves exchanges carrying bodies larger than it will hold in memory, and long-lived streams, with every location read-only except that store
- **THEN** it continues to serve
- **AND** no location other than the configured store path is written at any point

#### Scenario: A configured store path that is unusable is a named failure

- **WHEN** a credential store path is configured at a location the sidecar cannot read or write
- **THEN** it refuses to start
- **AND** the refusal names that path and the access it lacked
- **AND** the refusal is distinguishable from an empty store
- **AND** it is named in the same validation pass as every other failing item

#### Scenario: A diagnostic never demands a writable location

- **WHEN** the sidecar is asked for every diagnostic its local surface offers while every location it can see is read-only
- **THEN** each is answered
- **AND** none is refused for want of a writable location

### Requirement: The declared configuration states which items only the operator can issue

That the artifact's declared configuration and its shipped example are both generated from the same schema the startup validation reads, that a divergence between any two of the three fails the build naming the item and the direction of the divergence, that the example is complete on its own, and that the published artifact started with only what its own declaration carries plus a value for each item the example marks reaches readiness under a release gate, are `operability/packaging`'s obligations on every deployable and hold here as given. What this capability adds is what the deploying party's identity demands of the sidecar's declaration in particular.

The party deploying this artifact is a tenant who cannot read the operator's configuration and may have no way to ask. For every item the schema marks as supplied by the deployment, the schema and the shipped example SHALL therefore state which of two origins it has: a value only the operator can issue, or a value determined inside the tenant's own infrastructure. That statement SHALL be generated from the schema on the same terms as every other property of an item, and an item stating neither origin SHALL fail the same divergence gate as an item absent from the declaration.

No item whose origin is the tenant's own infrastructure SHALL require the tenant to inspect any of the operator's configuration in order to determine it, and no item whose origin is the operator SHALL be marked as one the tenant determines. Discovering, by repeated restart or by a support conversation, that a value had to come from the operator is the failure this states against: the sidecar's schema and example are the only documentation the deploying tenant has.

#### Scenario: Every supplied item states its origin

- **WHEN** the sidecar's schema is retrieved from its artifact and every item it marks as supplied by the deployment is examined
- **THEN** each states whether only the operator can issue it or the tenant's own infrastructure determines it
- **AND** the shipped example carries the same statement for each item it marks

#### Scenario: An item with no stated origin fails the gate

- **WHEN** an item the schema marks as supplied by the deployment states neither origin
- **THEN** the gate fails naming that item
- **AND** the failure is reported on the same terms as an item missing from the declaration

#### Scenario: A misattributed item fails the gate

- **WHEN** an item only the operator can issue is stated as one the tenant's own infrastructure determines
- **THEN** the gate fails naming that item and both origins

#### Scenario: A tenant needs nothing of the operator's beyond the operator-issued items

- **WHEN** a tenant deploys the artifact holding only the shipped example and the values for the items it states the operator issues
- **THEN** every remaining item it marks is determinable from within the tenant's own infrastructure
- **AND** no item required to reach readiness is discovered only by a failed start

### Requirement: The provenance a tenant reads and the provenance the proxy records are the same

That every component reports a version, the source revision it was built from and whether that tree was modified, at startup and on demand, that a sidecar reports it when establishing a tunnel, and that an absent provenance is reported as explicitly unknown, are `operability/observability`'s rules; that provenance is fixed when the artifact is produced, that no configuration item, environment property or peer value can restate it, that a build from a modified tree does not report identically to one from an unmodified tree at the same revision, and that it is retrievable from the stopped artifact, are `operability/packaging`'s. Both hold here as given. What this capability adds is that the sidecar reports it in a place the operator cannot reach and in a place the tenant cannot reach, and the two must agree.

The four places the sidecar's provenance is obtainable — the stopped artifact, the startup record, the local operational surface, and the establishment declaration the proxy records — SHALL report identical values. An inventory taken from the proxy and an inventory taken inside the tenant's own infrastructure SHALL therefore identify the same build, and neither party SHALL need access to the other's to establish it. A disagreement between any two of the four SHALL be a defect rather than two readings to be reconciled.

#### Scenario: All four places agree

- **WHEN** a sidecar artifact is interrogated while stopped, then started, then interrogated on its local surface, and then establishes a tunnel
- **THEN** the same version, revision, and modification state are obtained in all four places

#### Scenario: The operator and the tenant reach the same answer separately

- **WHEN** an operator reads a connected sidecar's provenance from the proxy and a tenant reads it from the sidecar's local surface
- **THEN** the two answers are identical
- **AND** neither party required access to the other's component to obtain it

#### Scenario: A disagreement is a defect, not a reconciliation

- **WHEN** a sidecar's establishment declaration states a provenance differing from what its local surface reports
- **THEN** that is reported as a defect naming both values
- **AND** neither value is preferred over the other as the authoritative one

#### Scenario: Provenance is answerable with the proxy unreachable

- **WHEN** the sidecar's local surface is interrogated for its provenance while no tunnel is established and the tunnel endpoint is unresolvable
- **THEN** the version, revision, and modification state are returned
- **AND** they are the values the establishment declaration carries once a tunnel is established

### Requirement: The contract range and capability set are answerable from inside the tenant's infrastructure

That the artifact declares the inclusive lowest and highest contract versions it supports and the optional capabilities it can declare, that the declaration is readable from the stopped artifact without network access, that it is not inferable from the build version, that no configuration or peer value widens it or adds a capability the build cannot perform, and that the artifact's declaration and the started component's declaration are identical, are `operability/packaging`'s obligations and hold here as given. How a range is negotiated between two connected peers is `tunnel/wire-contract`'s. What this capability adds is that the sidecar answers with it from a surface reachable only from inside the tenant's infrastructure.

The running sidecar SHALL answer its supported contract range and the optional capabilities it can declare from its own local operational surface, at startup and on demand, without a reachable tunnel endpoint and without establishing a tunnel. The set it declares at establishment SHALL be the set it answers with there. Because the operator cannot reach this surface and the tenant cannot reach the proxy, an answer that required a tunnel would be unobtainable by exactly the party diagnosing a tunnel that will not establish.

The answer SHALL NOT change once a tunnel is established. The version negotiated for a tunnel is a property of that tunnel and SHALL be reported separately from the range, so that a sidecar serving at a negotiated version still answers with every version it supports.

#### Scenario: The range is answerable with no endpoint reachable

- **WHEN** the sidecar's local surface is interrogated for its contract support while the tunnel endpoint is unresolvable
- **THEN** the lowest and highest contract versions it supports are returned
- **AND** the optional capabilities it can declare are returned

#### Scenario: The answered set is the set declared at establishment

- **WHEN** a sidecar that answered with a range and a capability set establishes a tunnel
- **THEN** its establishment declaration carries that same range and that same set

#### Scenario: A refused establishment does not suppress the answer

- **WHEN** establishment is refused because no contract version is common to the sidecar and the proxy
- **THEN** the local surface still answers with the sidecar's own supported range
- **AND** a tenant can report that range to the operator without proxy access

#### Scenario: The negotiated version is reported separately from the range

- **WHEN** a tunnel is established at a negotiated version below the highest the sidecar supports
- **THEN** the answered range is unchanged
- **AND** the negotiated version is reported as a property of that tunnel rather than as the range

### Requirement: Startup is an ordered sequence with observable intermediate states

Startup SHALL proceed in this order, and each step SHALL complete before the next begins: configuration validation; construction of the local operational surface; verification of the endpoint the sidecar will authenticate to; acquisition of the credential; tunnel establishment; assessment of backend reachability; readiness.

The liveness signal SHALL be answerable from the moment the local operational surface is constructed, before any tunnel or backend work is attempted, so that a sidecar stuck on establishment is distinguishable from one that never started. The readiness signal SHALL be answerable at that same moment and SHALL report failure with a reason for every instant before the last step completes.

A failure at any step SHALL name the step, and SHALL NOT be reported as a failure of a later step that was never reached.

#### Scenario: Liveness answers before a tunnel exists

- **WHEN** a sidecar is started and its tunnel endpoint does not answer
- **THEN** its liveness signal reports success
- **AND** its readiness signal reports failure with a reason naming the absent tunnel

#### Scenario: The backend is not contacted before the tunnel is established

- **WHEN** a sidecar is starting and has not yet established a tunnel
- **THEN** it has opened no connection to the backend

#### Scenario: A failure names the step it occurred at

- **WHEN** endpoint verification fails during startup
- **THEN** the reported failure names endpoint verification
- **AND** it is not reported as an authentication failure or as a backend failure

#### Scenario: A backend that is down does not prevent starting

- **WHEN** a sidecar starts while its backend refuses connections
- **THEN** it establishes its tunnel
- **AND** its readiness signal reports failure with a reason naming the backend
- **AND** it becomes ready without a restart once the backend answers

### Requirement: The credential is not materialised until the endpoint has verified

That the sidecar verifies the endpoint's presented identity against the configured endpoint before presenting a credential, and that a configuration which would accept any identity is a refusal to start, are the sidecar-credentials capability's rules and hold here as given. What this capability adds is an ordering strong enough that a failed verification leaves nothing to steal.

The sidecar SHALL NOT read, decrypt, or otherwise materialise its credential until verification of the endpoint has succeeded. Where verification fails, the credential store SHALL not have been read, no credential SHALL exist anywhere in the process, and the reported failure SHALL name endpoint verification, distinguishably from an authentication failure returned by the proxy and from an unreadable store.

The sidecar SHALL NOT follow a redirection of its tunnel endpoint to another host, whatever form that redirection takes, and SHALL treat one as a condition to report rather than to retry against the named host. A sidecar already holding a materialised credential from an earlier establishment SHALL NOT present it to an endpoint whose identity fails to verify on a later attempt.

#### Scenario: A failed verification leaves the credential unread

- **WHEN** a sidecar connects to an endpoint whose identity does not verify against the configured one
- **THEN** the credential store is not read
- **AND** no credential exists in the process
- **AND** the reported failure names endpoint verification

#### Scenario: A redirected endpoint receives nothing

- **WHEN** the configured endpoint answers by directing the sidecar to another host
- **THEN** the sidecar does not connect to that host
- **AND** no credential is presented anywhere
- **AND** the condition is reported rather than retried silently

#### Scenario: A held credential is not presented on a later failed verification

- **WHEN** a sidecar that has established a tunnel loses it, and the endpoint it reconnects to presents an identity that does not verify
- **THEN** the credential it already holds is not presented
- **AND** the reported failure names endpoint verification rather than a lost tunnel

#### Scenario: Verification failure is distinguishable from the two failures it resembles

- **WHEN** endpoint verification fails, the proxy refuses a presented credential, and the credential store cannot be read, in separate runs
- **THEN** the three reported failures carry different enumerated reasons

### Requirement: Backend reachability is proven by the sidecar and never inferred

That a sidecar's readiness depends on an established tunnel and a reachable backend, that it reports failure for the whole period it is draining, that it recovers without a restart, that it is never a constant, and that liveness reports failure only where a restart is the remedy, are the observability capability's rules and hold here as given. What this capability adds is how the backend half of that judgement is arrived at.

Backend reachability SHALL be assessed by the sidecar's own means against the configured origin. It SHALL NOT be inferred from the tunnel being established, from the tunnel answering the contract's liveness exchange, from the proxy having selected this sidecar, or from the most recent exchange having succeeded. A sidecar that has carried no exchange for an extended period SHALL still report the current reachability of its backend rather than the reachability its last exchange implied.

The liveness signal SHALL NOT report failure because the tunnel is absent, because the backend is unreachable, or because renewal of the credential is failing, since none of those is remedied by replacing the process.

#### Scenario: An unreachable backend means not ready

- **WHEN** a sidecar's tunnel is established and its backend refuses connections
- **THEN** its readiness signal reports failure with a reason naming the backend
- **AND** its liveness signal reports success

#### Scenario: An established tunnel does not vouch for the backend

- **WHEN** the tunnel is established and answering the contract's liveness exchange while the backend has stopped accepting connections
- **THEN** readiness reports failure
- **AND** the reported reason names the backend rather than the tunnel

#### Scenario: A stale success is not reported as reachability

- **WHEN** a sidecar's last exchange succeeded and its backend has since stopped accepting connections, with no exchange carried in between
- **THEN** readiness reports failure naming the backend
- **AND** the report does not depend on an exchange arriving to discover the condition

#### Scenario: A failing renewal does not fail liveness

- **WHEN** credential renewal has been failing for an extended period
- **THEN** the liveness signal reports success
- **AND** the readiness signal reflects the degraded state

### Requirement: Readiness states an enumerated reason that discloses no secret

Where readiness reports failure the response SHALL carry a reason drawn from a stable enumerated set distinguishing at minimum: no tunnel established; tunnel establishment in progress; establishment refused for an unusable credential; establishment refused for contract-version incompatibility; credential renewal failing; backend unreachable; and draining. The reason values SHALL be the published identifiers the observability capability treats as an interface, not prose. What the renewal-failure signal must additionally carry, including the remaining lifetime and its escalation as that lifetime shrinks, is the sidecar-credentials capability's and holds here as given.

A probe response SHALL carry state and reason only. It SHALL NOT carry credential material, key material, the contents of any configured secret, or any part of a client request or backend response.

#### Scenario: Reasons distinguish causes of unreadiness

- **WHEN** a sidecar is unready because no tunnel is established, and separately because its backend is unreachable
- **THEN** the two responses carry different enumerated reasons

#### Scenario: A refused establishment is distinguishable from a slow one

- **WHEN** establishment is refused because the credential is no longer valid
- **THEN** the reason names an unusable credential
- **AND** it differs from the reason reported while establishment is merely in progress

#### Scenario: A version incompatibility is its own reason

- **WHEN** establishment is refused because no contract version is common to the sidecar and the proxy
- **THEN** the reason names contract-version incompatibility
- **AND** it differs from the reason for an unusable credential and from the reason for an unreachable endpoint

#### Scenario: A probe discloses nothing sensitive

- **WHEN** every readiness and liveness response the sidecar can produce is collected
- **THEN** none contains credential material, key material, a configured secret, or any part of carried traffic

### Requirement: Termination signals produce exactly one shutdown

A termination signal SHALL begin the shutdown sequence, and every signal that means terminate SHALL begin the same sequence. The sidecar SHALL NOT close a tunnel carrying work as its first response to such a signal.

A second termination signal received while shutdown is in progress SHALL end the sidecar promptly without waiting out the remaining period, and SHALL be recorded distinguishably from a shutdown that completed its sequence. Further signals SHALL have no additional effect. Concurrent or repeated signals SHALL NOT produce two shutdown sequences, two drain notices, or two exits.

A signal the sidecar cannot handle, and destruction of the process, SHALL leave the tunnel to end as an unannounced loss. The sidecar SHALL NOT attempt to make an unannounced loss look announced, and SHALL NOT extend its own shutdown beyond its configured deadline in order to finish draining.

#### Scenario: A signal begins a drain, not a close

- **WHEN** a sidecar carrying in-flight exchanges receives a termination signal
- **THEN** it declares that it is draining before it closes anything
- **AND** its tunnel remains established while in-flight work continues

#### Scenario: Every terminating signal takes the same path

- **WHEN** the sidecar is terminated by each of the signals that mean terminate, in separate runs
- **THEN** each produces the same shutdown sequence and the same exit status

#### Scenario: A second signal ends it promptly

- **WHEN** a second termination signal arrives during shutdown
- **THEN** the sidecar ends without waiting out the remaining period
- **AND** the record distinguishes this from a completed shutdown sequence

#### Scenario: Repeated signals do not repeat the sequence

- **WHEN** many termination signals arrive in quick succession
- **THEN** exactly one drain notice is sent
- **AND** exactly one shutdown record is produced

#### Scenario: A destroyed process is an unannounced loss

- **WHEN** the sidecar's process is destroyed with no opportunity to act
- **THEN** no drain notice and no tunnel close is sent
- **AND** the ending is left to be observed as an unannounced loss

### Requirement: Shutdown withdraws readiness first, releases the backend hop, and exits successfully

The drain notice, the period in-flight work is given, the spreading of what remains across a configured window, the single deadline governing the whole sequence, and the prohibition on continuing past it are the sidecar-registry capability's withdrawal lifecycle and hold here as given; the record of what a drain abandoned is the observability capability's. This capability SHALL NOT introduce a second ordering or a second deadline. What it adds are the two ends of the sequence that are local to the process.

Readiness SHALL be withdrawn before the drain is declared, so that a scheduler placing traffic on this instance stops before the proxy stops selecting it. Every connection the sidecar holds to the backend SHALL be closed before the process exits, so that no backend connection outlives the sidecar that opened it.

An orderly shutdown SHALL exit with the success status whether or not work remained when the deadline elapsed, because a tenant redeploys far more often than an operator withdraws a proxy instance and an abandoned exchange is not a failure of the process. What was abandoned SHALL be attributable from the record, never from the exit status.

#### Scenario: Readiness is withdrawn before the drain is declared

- **WHEN** a sidecar carrying exchanges and bidirectional streams is terminated
- **THEN** its readiness signal reports failure before the drain is declared over the tunnel
- **AND** the drain is declared before any exchange or stream is ended

#### Scenario: Shutdown completes early when nothing remains

- **WHEN** all in-flight work completes before the drain period elapses
- **THEN** the tunnel is closed and the process exits without waiting out the remainder

#### Scenario: An abandoning shutdown is still a success exit

- **WHEN** a shutdown ends work at its deadline
- **THEN** the process exits with the success status
- **AND** the status is the same as for a shutdown in which nothing remained
- **AND** the abandonment is attributable from the record it produced

#### Scenario: Backend connections do not outlive the shutdown

- **WHEN** the sidecar exits after a drain
- **THEN** every connection it held to the backend has been closed
- **AND** the backend observes no connection attributable to that sidecar afterwards

#### Scenario: A backend that will not close does not prevent the exit

- **WHEN** a backend connection cannot be closed cleanly before the configured deadline elapses
- **THEN** the sidecar abandons it and exits
- **AND** the condition is recorded
- **AND** the process does not remain running past the deadline on its account

### Requirement: Failure classes have distinct, stable exit statuses

The sidecar SHALL exit with the success status only after an orderly shutdown. It SHALL exit with distinct non-zero statuses for, at minimum: a configuration validation failure; a construction failure, being an inability to build the sidecar's own working state before any traffic is carried; and a runtime failure, being an unrecoverable fault after it began serving.

Each status SHALL be documented, SHALL be stable across releases, and SHALL NOT be reused for another class. The same class of failure SHALL always yield the same status, and every non-zero exit SHALL be accompanied by a record naming the class and the specific cause within it.

#### Scenario: The three classes are distinguishable by status alone

- **WHEN** the sidecar is made to fail on configuration, on construction, and at runtime in separate runs
- **THEN** the three exit statuses differ from each other and from the success status

#### Scenario: A class always yields its own status

- **WHEN** several different configuration faults each cause a refusal
- **THEN** every one of them exits with the configuration status
- **AND** the accompanying record names which fault it was

#### Scenario: An orderly shutdown is the only success exit

- **WHEN** every way the sidecar can end is exercised
- **THEN** only an orderly shutdown exits with the success status

#### Scenario: A status is never reused

- **WHEN** the documented statuses are compared
- **THEN** no two failure classes share one
- **AND** none collides with the success status

### Requirement: Conditions fatal at startup are distinguished from conditions to be survived

The sidecar SHALL enumerate which conditions end the process and which it continues to run through. Fatal conditions SHALL include at minimum: a configuration validation failure; a configuration that would accept an unverifiable endpoint identity; and a credential store that is present but unreadable at startup. Survivable conditions SHALL include at minimum: an unreachable tunnel endpoint; a refused authentication; a lost tunnel; an unreachable backend; and a failing credential renewal while the current credential is valid.

The sidecar SHALL NOT exit on a survivable condition, since exiting turns a recoverable outage into a restart loop that discards the diagnostics an operator needs. It SHALL NOT retry a fatal condition, since retrying makes a misconfiguration look like an outage. A condition's classification SHALL be evident from the reported failure.

An unreadable credential store is fatal but cannot be discovered at startup, because the ordering this capability requires defers reading the store until the endpoint has verified, and endpoint unreachability is survivable. The classification SHALL follow the condition rather than the moment: the sidecar SHALL exit on it whenever it is discovered, with the same status and the same reported failure as if it had been discovered before the first establishment attempt, and the deferral SHALL be stated rather than left to be inferred from a sidecar that ran for hours and then exited. Until the store has been read, readiness SHALL report the establishment step it is waiting on and SHALL NOT report the store as readable.

#### Scenario: A survivable condition does not end the process

- **WHEN** the tunnel endpoint is unreachable for an extended period
- **THEN** the sidecar continues to run, reporting itself unready
- **AND** it does not exit
- **AND** its diagnostics remain answerable throughout

#### Scenario: A fatal condition is not retried

- **WHEN** the credential store is present but cannot be decrypted with the supplied key material
- **THEN** the sidecar exits with the construction status
- **AND** it makes no repeated attempt to establish a tunnel
- **AND** the reported failure names an unreadable store, distinct from an empty store

#### Scenario: A deferred fatal condition is still fatal when it is found

- **WHEN** a sidecar with an unreadable credential store is started against an unreachable endpoint, runs unready for an extended period, and the endpoint then becomes reachable and verifies
- **THEN** the sidecar exits at that point with the construction status
- **AND** the reported failure is the same one it would have given had the endpoint been reachable from the start
- **AND** while the store was unread its readiness named the establishment step it was waiting on rather than reporting the store as readable

#### Scenario: A refused authentication is survived, not fatal

- **WHEN** the proxy refuses the presented credential
- **THEN** the sidecar reports the refusal and remains running and unready
- **AND** the process does not exit

#### Scenario: An invalidated credential does not end the process

- **WHEN** a tunnel is ended with a reason naming the credential as no longer valid, and the sidecar therefore ceases to attempt establishment with it
- **THEN** the process remains running and reports itself unready with that reason
- **AND** its local diagnostics remain answerable, so the condition is diagnosable rather than lost to a restart loop

### Requirement: The backend origin is taken only from local configuration

The scheme, host, and port the sidecar connects to SHALL come from the configuration supplied on the machine the sidecar runs on, and from no other source. The sidecar SHALL NOT accept an origin, or any component of one, from the proxy, from the tunnel establishment exchange, from a frame carried over the tunnel, from a discovery service, or from any location reachable over the network.

Because a tunnel is admitted for exactly one mount, the configured origin is the single origin that tunnel serves. An origin arriving from any other source SHALL be ignored and recorded as a protocol violation rather than applied. Changing the origin SHALL require a new instance. The origin in force SHALL be reported at startup and on demand.

#### Scenario: A proxy-supplied origin has no effect

- **WHEN** a frame carried over the tunnel asserts an origin other than the configured one
- **THEN** the sidecar connects to the configured origin
- **AND** the assertion is recorded as a protocol violation
- **AND** no connection is opened to the asserted origin

#### Scenario: The origin is unchanged by the mount the exchange names

- **WHEN** an exchange names a mount other than the one the tunnel was admitted for
- **THEN** no connection is opened to any origin derived from that name
- **AND** the exchange is refused or handled under the bound mount

#### Scenario: No origin is discovered at run time

- **WHEN** the sidecar serves exchanges over an extended period
- **THEN** every connection it opens is to the configured origin
- **AND** it made no request to any service in order to learn an origin

#### Scenario: The origin in force is reportable

- **WHEN** an operator interrogates a running sidecar
- **THEN** the scheme, host, and port it dials are reported
- **AND** they match the configured values

### Requirement: No component of a received request can influence the origin dialled

No field, target component, or body octet of a request the sidecar receives SHALL be capable of changing the scheme, host, or port it connects to. This holds for every component without exception, and the sidecar SHALL apply the rule itself rather than relying on the edge having removed anything.

Without this the sidecar is an open relay with a credential, sitting inside the tenant's own network with reachability the public internet does not have. It is the single most consequential property in this capability, and in the reference system it was the one genuinely good defence with no owner.

#### Scenario: An authority field does not retarget the connection

- **WHEN** a carried request bears an authority field naming a different host and port
- **THEN** the sidecar connects to the configured origin
- **AND** the authority field is carried to the backend as an ordinary field or regenerated for the sidecar's own hop, never consumed as a destination

#### Scenario: An absolute target does not retarget the connection

- **WHEN** a carried request's target names its own scheme and authority
- **THEN** no connection is opened to that authority
- **AND** the exchange is reset with the enumerated reason for an unusable target

#### Scenario: A forwarding field does not retarget the connection

- **WHEN** a carried request bears fields conventionally naming an original host, protocol, or port
- **THEN** the origin dialled is unchanged

#### Scenario: A field naming an internal address does not retarget the connection

- **WHEN** a carried request bears a field whose value is an address on the tenant's own network or a well-known infrastructure metadata address
- **THEN** the origin dialled is unchanged
- **AND** no connection is opened to that address

#### Scenario: The affinity key does not retarget the connection

- **WHEN** an exchange carries an affinity key whose value resembles an origin
- **THEN** the origin dialled is unchanged

#### Scenario: Body and trailer content do not retarget the connection

- **WHEN** a carried request's body octets and trailer fields contain values resembling origins
- **THEN** the origin dialled is unchanged
- **AND** the octets are delivered to the backend unaltered

#### Scenario: A bidirectional establishment does not retarget the connection

- **WHEN** a bidirectional stream establishment arrives naming an authority other than the configured origin
- **THEN** the sidecar establishes the backend hop against the configured origin
- **AND** no connection is opened to the named authority

#### Scenario: A backend redirection does not retarget the connection

- **WHEN** the backend answers with a redirection naming another host
- **THEN** the sidecar issues no second request
- **AND** the redirection is relayed as an ordinary response

### Requirement: The remainder is validated before a connection is opened, and rejection is never repair

Before opening any connection for an exchange, the sidecar SHALL validate the remainder the contract carried. It SHALL reject a remainder that does not begin with exactly one path separator, that begins with two or more separators and is therefore authority-relative, that carries a scheme or an authority of its own, that contains a literal null octet or a control octet, or that resolves above the origin's own root.

Rejection SHALL be the outcome. The sidecar SHALL NOT sanitise, collapse, resolve, decode, re-encode, or otherwise repair a remainder and proceed. It MAY compute a normalised form solely in order to decide whether the remainder escapes the base, and SHALL dial with the remainder exactly as received, never with the normalised form. It SHALL NOT percent-decode any octet in order to inspect it, and SHALL NOT reject a remainder because a percent-encoded octet within a segment would, if decoded, be a separator or a full stop — those octets are opaque segment content that no hop decodes.

A rejection SHALL reset the exchange with an enumerated reason distinguishable from a backend connection failure, and no connection SHALL have been opened. The sidecar SHALL perform this validation on every exchange regardless of what the edge is believed to have done, because the peer at the other end of the tunnel may be of any version or any implementation.

#### Scenario: A remainder with no leading separator is rejected

- **WHEN** a remainder arrives that does not begin with a path separator
- **THEN** no connection to the backend is opened
- **AND** the exchange is reset with the enumerated reason for an unusable target

#### Scenario: An authority-relative remainder is rejected

- **WHEN** a remainder arrives beginning with two separators followed by a host name
- **THEN** no connection is opened to that host
- **AND** the exchange is reset with the same enumerated reason
- **AND** the reason is distinguishable from a backend connection failure

#### Scenario: A remainder carrying a scheme is rejected

- **WHEN** a remainder arrives carrying its own scheme and authority
- **THEN** no connection is opened and the exchange is reset

#### Scenario: A remainder that escapes the base is rejected, not resolved

- **WHEN** a remainder arrives whose parent segments would resolve above the origin's root
- **THEN** the exchange is reset
- **AND** the backend receives no request
- **AND** no request bearing the resolved form is issued

#### Scenario: A remainder with dot segments that do not escape is dialled as received

- **WHEN** a remainder arrives containing parent segments that resolve within the origin's root
- **THEN** the backend receives the remainder exactly as it arrived
- **AND** it does not receive a normalised form

#### Scenario: Percent-encoded octets are carried, not decoded or rejected

- **WHEN** a remainder arrives containing percent-encoded separators and percent-encoded full stops within its segments
- **THEN** the exchange is not rejected
- **AND** the backend receives those octets still encoded
- **AND** no octet is decoded in order to inspect it

#### Scenario: A control or null octet is rejected

- **WHEN** a remainder arrives containing a literal null octet or a control octet
- **THEN** no connection is opened and the exchange is reset

#### Scenario: Validation does not depend on the edge

- **WHEN** a remainder that the edge should have rejected arrives from a peer of any version
- **THEN** the sidecar rejects it on its own account
- **AND** the outcome is identical to the outcome for the same remainder from any other peer

### Requirement: The query component is preserved verbatim

The query the contract carried SHALL reach the backend octet for octet. The sidecar SHALL NOT decode, re-encode, reorder, deduplicate, sort, add to, or remove from it, and SHALL NOT participate in it in any way beyond carrying it. A query SHALL take no part in deciding what is dialled.

An absent query and an empty query SHALL be distinguishable at the backend, and the sidecar SHALL preserve which of the two it received.

#### Scenario: Repeated keys and encoded octets survive

- **WHEN** a remainder carries a query with repeated keys and percent-encoded octets
- **THEN** the backend receives that query unaltered
- **AND** no key is reordered, merged, or removed

#### Scenario: An empty query is distinguishable from none

- **WHEN** one exchange carries a query separator with nothing after it and another carries no query separator at all
- **THEN** the backend can distinguish the two

#### Scenario: A query resembling an origin changes nothing

- **WHEN** a query contains a value that is a scheme and authority
- **THEN** the origin dialled is unchanged
- **AND** the query reaches the backend unaltered

#### Scenario: Unusual separators within the query are not interpreted

- **WHEN** a query uses separators other than the conventional one between its pairs
- **THEN** the octets reach the backend unaltered
- **AND** the sidecar parses no structure within them

### Requirement: The sidecar's own surfaces are never reachable as a backend origin

The sidecar's local operational and diagnostic surfaces SHALL be bound separately from anything it dials. It SHALL refuse to start where the configured origin resolves to the address and port of one of its own surfaces, and the refusal SHALL name that collision.

No request carried over the tunnel SHALL be capable of reaching a readiness signal, a liveness signal, a diagnostic surface, a configuration report, or a credential store belonging to the sidecar. Where a client's request would do so, the exchange SHALL be refused rather than served.

#### Scenario: An origin naming the sidecar's own surface fails validation

- **WHEN** the configured origin is the address and port of the sidecar's own operational surface
- **THEN** it refuses to start
- **AND** the refusal names the collision

#### Scenario: No carried request reaches a local surface

- **WHEN** carried requests target every path the sidecar's own surfaces answer on
- **THEN** each is dialled against the configured origin like any other exchange
- **AND** none is answered by the sidecar's own surfaces

#### Scenario: The credential store is not reachable as content

- **WHEN** a carried request's remainder names the configured credential store path
- **THEN** the sidecar reads no credential state on account of it
- **AND** the exchange is dialled against the backend or refused, and the store's contents are not returned

### Requirement: Backend connection bounds are the sidecar's own and distinct from the proxy's

The sidecar SHALL enforce its own configured bounds on the backend hop, comprising at minimum: the time allowed to establish a connection to the backend; the time from issuing the request until the backend's first response octet; and the time between successive body octets in either direction. These SHALL be configured locally on the sidecar, SHALL be independent of the bounds the proxy applies to the same exchange, and SHALL NOT be derived from any value the proxy sends.

Where a bound the proxy applies expires before the sidecar's own, the sidecar SHALL abandon the backend work on receiving the cancellation rather than continuing it. The sidecar SHALL NOT hold a connection attempt, a request, or a response for an exchange that has been reset, because a backend that keeps working for a client that is gone is amplification aimed at the tenant's own origin.

The sidecar SHALL NOT apply a total-duration bound of its own to any exchange. Total duration is determined by the timeout class of the route, which the proxy owns and which the sidecar has no local means to know; a sidecar that imposed one would silently truncate every unbounded-total class. An exchange SHALL therefore be carried for as long as octets continue to flow within the idle bound, and SHALL be ended on elapsed time only by a cancellation the proxy sends.

#### Scenario: The sidecar's bounds are its own

- **WHEN** the sidecar is configured with backend bounds different from the proxy's
- **THEN** it applies its own values
- **AND** no value the proxy sends changes them

#### Scenario: Cancellation abandons the backend work

- **WHEN** an exchange is reset while the sidecar is awaiting the backend's first octet
- **THEN** the sidecar abandons the request against the backend
- **AND** it holds no connection or buffer for that exchange afterwards

#### Scenario: A resetting client does not leave the backend working

- **WHEN** a client disconnects during a large response and the exchange is reset
- **THEN** the sidecar stops reading from the backend
- **AND** the backend observes the request as ended rather than continuing to produce octets

#### Scenario: An unending response is not cut off by a total bound

- **WHEN** a backend emits octets indefinitely within the configured idle bound
- **THEN** the sidecar continues to carry them for as long as they continue
- **AND** no configured item of the sidecar's ends the exchange on elapsed time
- **AND** it ends only when a cancellation arrives, a hop closes, or the idle bound elapses

#### Scenario: The idle bound resets on delivery

- **WHEN** a backend delivers an octet after a period of silence shorter than the idle bound
- **THEN** the exchange continues
- **AND** the idle bound is measured again from that delivery

### Requirement: Backend connections are reused within bounds and never reused unsafely

The sidecar SHALL bound the number of connections it holds to the backend and the period an idle one is retained, both by configuration. A connection SHALL be returned for reuse only where the exchange that used it completed cleanly and the connection's state is known good.

A connection SHALL NOT be reused where the exchange on it was reset, where the response was truncated, where the backend signalled that it is closing, or where any framing ambiguity remains. A connection carrying an upgraded or bidirectional session SHALL never be returned for reuse. A connection the backend has closed SHALL never be handed to a new exchange as though it were usable.

Exhausting the connection bound SHALL cause new exchanges to wait within a configured bound and then be refused with an enumerated reason naming the bound, never to grow the number of connections beyond it.

#### Scenario: A clean exchange yields a reusable connection

- **WHEN** a series of exchanges is carried against the backend one after another, each completing cleanly
- **THEN** the number of connections the backend observes is fewer than the number of exchanges
- **AND** it does not grow with the number of exchanges once the configured connection bound is reached

#### Scenario: A reset exchange's connection is closed

- **WHEN** an exchange is reset mid-response
- **THEN** the connection it used is closed rather than returned for reuse
- **AND** no later exchange is carried on it

#### Scenario: An upgraded session's connection is never pooled

- **WHEN** a bidirectional session over the backend hop ends
- **THEN** its connection is closed
- **AND** no request exchange is carried on it afterwards

#### Scenario: A backend-closed connection is not handed out

- **WHEN** the backend closes an idle pooled connection and a new exchange arrives
- **THEN** the exchange is not failed on account of the stale connection
- **AND** it is carried on a connection the backend accepts

#### Scenario: The connection bound refuses rather than grows

- **WHEN** more concurrent exchanges arrive than the configured connection bound permits
- **THEN** the number of connections to the backend does not exceed the bound
- **AND** exchanges that cannot obtain one within the configured wait are refused with a reason naming that bound

### Requirement: Protection of the backend hop is decided by configuration and cannot be waived silently

The backend hop is the one hop no other capability owns: the tunnel listener defines what protects the sidecar's connection to the proxy, and edge hygiene defines what protects the client's connection to the edge, but what protects the sidecar's connection to the tenant's backend is the sidecar's own.

Whether the sidecar protects that connection, and whether it verifies the backend's identity, SHALL be determined by the configured origin and by configured items validated in the one validation pass. Where the configured origin calls for a protected connection, the sidecar SHALL verify the backend's presented identity against the configured host, and SHALL refuse the exchange with the enumerated outcome for an unverifiable backend rather than continuing unverified. It SHALL NOT fall back to an unprotected connection because a protected one could not be established, and SHALL NOT promote an unprotected connection in band.

Verification SHALL NOT be waivable by a setting that accepts any identity. Where a deployment's backend presents an identity no public trust path validates — the common case inside a tenant's own network — the deployment SHALL configure the identity or the trust source to expect, and a configuration that would instead accept whatever answers SHALL be a validation failure naming that item. The choice in force SHALL be reported with the configuration in force, so that an operator can tell whether the hop inside the tenant's network is protected without reading the artifact's source.

#### Scenario: An unverifiable backend is refused, not served

- **WHEN** the configured origin calls for a protected connection and the backend presents an identity that does not verify against the configured host
- **THEN** no request is issued to it
- **AND** the exchange carries the enumerated outcome for an unverifiable backend
- **AND** that outcome is distinguishable from a refused connection and from a connect-bound expiry

#### Scenario: Protection is not downgraded on failure

- **WHEN** a protected connection to the backend cannot be established
- **THEN** the sidecar does not attempt an unprotected connection to the same origin
- **AND** the exchange is refused with the enumerated outcome rather than served

#### Scenario: Accepting any backend identity fails validation

- **WHEN** the sidecar is configured for a protected backend origin and for accepting any identity that origin presents
- **THEN** it refuses to start in the one validation pass
- **AND** the refusal names that item alongside any other faults present

#### Scenario: A pinned or privately trusted backend identity is honoured

- **WHEN** the sidecar is configured with the backend identity or trust source to expect, and the backend presents an identity that validates against it
- **THEN** the exchange is carried
- **AND** no public trust path is required for it to succeed

#### Scenario: The protection in force is reportable

- **WHEN** an operator retrieves the configuration in force
- **THEN** it states whether the backend hop is protected and whether the backend's identity is verified
- **AND** the stated values are the ones the sidecar applies

### Requirement: Backend failures are distinct outcomes the contract can carry

Each way the backend hop can fail SHALL produce its own enumerated outcome, carried over the contract as a reset or a failure the proxy can attribute. The set SHALL distinguish at minimum: the configured host cannot be resolved; the connection was refused; the connection attempt exceeded its bound; the backend's identity could not be verified where the configured origin requires it; the first response octet did not arrive within its bound; the body went idle beyond its bound; and the backend closed or failed part-way through a response it had begun.

Every one of these SHALL be a published code of the wire contract's own enumeration for the failure of a far hop, not a vocabulary of this capability's. The sidecar SHALL NOT convey one of them as a description accompanying a broader code, because a description is diagnostic text the proxy may not branch on and the proxy must be able to attribute each of these conditions separately. Where a condition arises that the contract's enumeration at the negotiated version does not distinguish, the sidecar SHALL convey the nearest code the contract does define for the failure of a far hop and SHALL record the finer condition locally, rather than inventing a code the proxy cannot interpret.

The sidecar SHALL NOT substitute a response of its own for a backend that failed. It SHALL NOT synthesise a status, a header field, a body octet, or a trailer section the backend did not produce, and SHALL NOT complete a truncated response as though it had ended normally. A response the sidecar had already begun to relay SHALL be truncated with the enumerated reason rather than replaced.

#### Scenario: Refusal and timeout are distinguishable

- **WHEN** the backend refuses a connection, and separately accepts it but never answers
- **THEN** the two outcomes carry different enumerated reasons

#### Scenario: Every backend outcome is a contract code

- **WHEN** each backend failure mode is exercised in turn and the frames conveyed are examined
- **THEN** each carries a published code of the contract's enumeration
- **AND** none is distinguished only by an accompanying description
- **AND** the proxy attributes each condition separately without interpreting any description

#### Scenario: An undistinguished condition falls back rather than inventing

- **WHEN** a backend condition arises that the contract's enumeration at the negotiated version does not distinguish
- **THEN** the code conveyed is the nearest one the contract defines for the failure of a far hop
- **AND** the finer condition is recorded locally
- **AND** no code outside the contract's enumeration is conveyed

#### Scenario: An unresolvable host is its own outcome

- **WHEN** the configured host cannot be resolved
- **THEN** the outcome names resolution failure
- **AND** it is distinguishable from a refused connection

#### Scenario: A mid-response failure truncates rather than replaces

- **WHEN** the backend closes part-way through a response whose head the sidecar has already relayed
- **THEN** the exchange is reset with the enumerated reason for a failure after the head
- **AND** no generated body, status, or trailer section is substituted

#### Scenario: No error body is invented

- **WHEN** every backend failure mode is exercised in turn
- **THEN** in no case does the sidecar produce body octets the backend did not produce

#### Scenario: A truncated response is not completed

- **WHEN** a backend declares a representation length and then closes early
- **THEN** the sidecar does not pad, complete, or re-declare the response
- **AND** the outcome names the truncation

### Requirement: The backend hop's liveness is the sidecar's to prove and to report

No probe can span both hops, so the sidecar SHALL prove the liveness of the backend hop itself. For a bidirectional session it SHALL run a keepalive against the backend at a configured interval, SHALL answer the backend's own keepalive probes at its own hop, and SHALL NOT carry a keepalive of either hop across the tunnel.

Where the backend stops answering within the configured bound, the sidecar SHALL reset the affected stream with the enumerated code for a counterpart that stopped answering, so that the proxy can attribute the loss to the backend rather than to the tunnel. The sidecar SHALL NOT treat its own tunnel liveness as evidence that the backend is answering, and SHALL NOT treat backend liveness as evidence about the client.

Keepalive traffic SHALL NOT reset any idle bound measured on application traffic, at either hop.

#### Scenario: A silent backend is reported as such

- **WHEN** the backend stops answering the sidecar's keepalive on an otherwise idle session
- **THEN** the sidecar resets that stream with the enumerated code for a counterpart that stopped answering
- **AND** the tunnel and its other streams are unaffected

#### Scenario: Keepalive is answered at the hop that received it

- **WHEN** the backend sends a keepalive probe
- **THEN** the sidecar answers it
- **AND** no keepalive frame is carried over the tunnel

#### Scenario: Tunnel liveness does not vouch for the backend

- **WHEN** the tunnel continues to answer the contract's liveness exchange while one session's backend has stopped answering
- **THEN** that session is reset with the backend named
- **AND** it is not held open on the strength of the tunnel's liveness

#### Scenario: Keepalive does not hold an idle session open

- **WHEN** keepalive traffic continues on a session carrying no application frames for longer than the configured idle bound
- **THEN** the session is ended on the idle bound
- **AND** the keepalive traffic did not extend it

### Requirement: The backend hop's frame extensions are negotiated and resolved by the sidecar, within a bound

The wire contract requires the hop that terminates a frame-transforming extension to resolve it before placing a frame on the tunnel, and the proxy owns that resolution and its bounds on the client hop. The backend hop is the sidecar's, and the same obligation with the same danger falls here.

The sidecar SHALL negotiate any frame-transforming extension on the backend hop independently of what was negotiated on the client hop, SHALL NOT relay an offer or a selected parameter set between the two hops, and SHALL place on the tunnel only frames whose payloads are untransformed with the extension's indicator clear. A frame arriving from the backend bearing an extension indicator the backend hop did not negotiate SHALL be treated as a protocol violation of that hop and SHALL end the stream, not the tunnel.

The sidecar SHALL enforce a configured bound on the size of a single message after any expansion it performs, and SHALL enforce it as the message is expanded so that the memory held never exceeds the bound however small the transformed form was. Reaching the bound SHALL end the stream concerned with an enumerated reason naming the bound. This bound is load-bearing rather than economical: the sidecar shares a machine with the tenant's own application, and a modest frame from the backend that expands without bound takes down the application the sidecar exists to serve.

#### Scenario: An expansion bomb from the backend is bounded

- **WHEN** the backend sends a small transformed frame whose untransformed form exceeds the configured bound
- **THEN** the stream is ended with the enumerated reason naming that bound
- **AND** the memory held for that message never exceeds the bound
- **AND** the tunnel and its other streams continue

#### Scenario: Negotiation on one hop does not follow to the other

- **WHEN** an extension is negotiated on the client hop
- **THEN** the establishment request the sidecar issues to the backend carries no offer derived from it
- **AND** the parameters the sidecar and the backend agree are not visible to the client

#### Scenario: Frames placed on the tunnel are untransformed

- **WHEN** the backend hop negotiates a frame-transforming extension and the backend sends a transformed frame
- **THEN** the frame the sidecar places on the tunnel carries the untransformed octets with the extension's indicator clear
- **AND** the octets the client receives are byte-identical to the backend's untransformed payload

#### Scenario: An unnegotiated indicator is a stream fault, not a tunnel fault

- **WHEN** the backend sends a frame bearing an extension indicator that the backend hop did not negotiate
- **THEN** that stream is ended with the enumerated reason for a protocol violation on the backend hop
- **AND** the tunnel remains established and its other streams are undisturbed

### Requirement: The gRPC-Web to gRPC translation is a declared capability, never an assumption

The sidecar SHALL declare its ability to translate between the browser-oriented gRPC-Web framing and a gRPC backend as an optional capability at tunnel establishment, named by its published contract identifier. It SHALL NOT perform the translation on a tunnel where the capability was not declared and agreed, and the proxy SHALL NOT direct an exchange requiring it to a sidecar that did not declare it.

A sidecar that cannot reach a gRPC backend, or that is not configured for the translation, SHALL NOT declare the capability. Declaring it SHALL be a statement about this build and this configuration, not a hope; an exchange requiring it SHALL be refused with the capability named rather than attempted and failed.

The translation exists here because only the component adjacent to the backend can perform it. Nothing at the edge can, and a sidecar that silently buffers instead of translating produces a call that hangs rather than one that errors.

#### Scenario: The capability is declared and recorded

- **WHEN** a sidecar configured for the translation establishes a tunnel
- **THEN** it declares the capability by its published identifier
- **AND** the proxy records it as available for that sidecar

#### Scenario: An undeclared sidecar is not asked to translate

- **WHEN** an exchange requiring the translation is matched to a mount whose only sidecar did not declare the capability
- **THEN** the exchange is refused with the capability named
- **AND** no request is carried to that sidecar

#### Scenario: An unconfigured sidecar declares nothing

- **WHEN** a sidecar is started without the translation configured
- **THEN** it does not declare the capability
- **AND** it performs no translation on any exchange

#### Scenario: A need discovered after dispatch is reset, not degraded

- **WHEN** a sidecar that did not declare the capability receives a backend response requiring it
- **THEN** it resets the stream with the capability named
- **AND** it does not deliver a partially translated response

### Requirement: Translation is applied only where configured and is otherwise inert

The translation SHALL be applied only for the exchanges the sidecar's configuration selects, identified by the mount and by an enumerated set of content types. Where it is not configured, or where an exchange's content type is not in that set, every body octet SHALL be delivered unchanged in both directions.

Matching an exchange to an enumerated variant SHALL be by an explicitly stated rule, and an exchange the rule does not match SHALL be carried untranslated rather than translated on a resemblance. A body whose final octets happen to resemble the in-body trailer framing SHALL NOT be interpreted where translation is inert; those octets are body content, and lifting them out of the body would corrupt an unrelated payload.

#### Scenario: An unconfigured route is byte-identical

- **WHEN** the translation is not configured for a mount
- **THEN** every request and response body carried for it is delivered octet for octet as received

#### Scenario: A content type outside the set is not translated

- **WHEN** a carried exchange's content type is not among the enumerated variants
- **THEN** its body is carried unchanged
- **AND** no trailer section is lifted out of or inserted into it

#### Scenario: A body resembling the framing is not interpreted

- **WHEN** translation is inert and a response body's final octets resemble the in-body trailer framing
- **THEN** the client receives those octets as part of the body
- **AND** they are neither removed from the body nor promoted to a trailer section

#### Scenario: A near-miss variant is not guessed at

- **WHEN** an exchange bears a content type differing from an enumerated variant only by an unrecognised parameter, and the configured rule does not match it
- **THEN** its body is carried octet for octet in both directions
- **AND** no trailer section is lifted out of or inserted into it
- **AND** the outcome is identical to that for a content type bearing no resemblance at all

### Requirement: The in-body trailer frame is translated faithfully in both directions

Where translation is in force, the sidecar SHALL convert the length-prefixed trailer frame carried inside a gRPC-Web request body into a real trailer section on the request it issues to the backend, and SHALL convert the trailer section the backend returns into a length-prefixed trailer frame appended after the last message frame of the response body.

The call status the backend reports SHALL be conveyed on every outcome including success, because the framing carries it in the body and there is no other place for it. Message frames SHALL be emitted as they arrive rather than aggregated, so that a server-streaming call remains a stream. A response consisting of a status and no message frames SHALL still carry a trailer frame. Fields carrying structured error detail SHALL be conveyed intact, and the header and trailer sections SHALL each be bounded by a configured maximum.

The text-encoded variant of the framing, in which the frames are base64 encoded, SHALL be translated on both the frame boundaries and the payload. Translation of it SHALL be incremental: the memory held for an exchange SHALL NOT exceed the exchange's configured buffered-octet bound however large the body is, so a body larger than that bound is translated rather than refused.

#### Scenario: A successful call carries its status in the body

- **WHEN** a translated unary call succeeds
- **THEN** the client receives the message frame followed by a trailer frame carrying the success status
- **AND** the status is present even though the call succeeded

#### Scenario: A streaming call is not aggregated

- **WHEN** a backend emits message frames over an extended period
- **THEN** each is delivered to the client as it arrives
- **AND** the trailer frame follows the last of them

#### Scenario: A request trailer frame becomes a real trailer section

- **WHEN** a translated request body ends with a length-prefixed trailer frame
- **THEN** the backend receives those fields as a real trailer section
- **AND** the frame's octets are not delivered as body content

#### Scenario: A status-only response still carries a trailer frame

- **WHEN** a backend returns a failure status with no message frames
- **THEN** the client receives a trailer frame carrying that status
- **AND** the response is not empty

#### Scenario: Structured error detail survives

- **WHEN** a backend returns a status accompanied by a field carrying structured error detail
- **THEN** that field reaches the client inside the trailer frame with its octets intact

#### Scenario: The text-encoded variant is translated incrementally

- **WHEN** a translated exchange uses the text-encoded variant of the framing and carries a body many times larger than the exchange's configured buffered-octet bound
- **THEN** each frame is delivered as it arrives rather than after the body ends
- **AND** the memory held for the exchange never exceeds that bound
- **AND** the exchange completes rather than being refused for its size

### Requirement: Translation failures reset the exchange rather than degrade it

Where the sidecar cannot complete a translation it SHALL reset the exchange with an enumerated reason and SHALL NOT deliver a partial or invented result. The enumerated reasons SHALL distinguish at minimum: a malformed frame in the carried body; a frame declaring a length beyond the configured bound; a section exceeding its configured maximum; a trailer field the target framing cannot express; and a backend that ended without the trailer section the framing requires. Each SHALL be a published code of the wire contract's own enumeration for a translation failure, not a vocabulary of this capability's, so that the proxy can attribute a translation failure without interpreting a description.

The sidecar SHALL NOT fabricate a success status for a call whose status it did not receive, SHALL NOT merge trailer fields into a header section, and SHALL NOT drop a trailer section it could not express. A failure to translate SHALL be attributable to the translation rather than reported as a backend failure or a transport failure.

#### Scenario: A malformed frame is reset, not repaired

- **WHEN** a carried body contains a frame whose length prefix does not match its contents
- **THEN** the exchange is reset with the enumerated reason for a malformed frame
- **AND** no partially translated body reaches the other side

#### Scenario: A missing status is never invented

- **WHEN** a backend ends a translated call without returning a status
- **THEN** the exchange is reset with the reason naming the absent trailer section
- **AND** no success status is conveyed to the client

#### Scenario: An oversized section is refused

- **WHEN** a trailer section exceeds its configured maximum
- **THEN** the exchange is reset with the reason naming that bound
- **AND** the section is not truncated to fit

#### Scenario: An inexpressible field is not silently dropped

- **WHEN** a backend returns a trailer field the target framing cannot express
- **THEN** the exchange is reset with the reason naming that condition
- **AND** the field is neither dropped nor moved into the header section

#### Scenario: A translation failure is attributable to translation

- **WHEN** any translation failure occurs
- **THEN** the recorded and conveyed reason names the translation
- **AND** it is distinguishable from a backend connection failure and from a tunnel failure

### Requirement: The credential store is one configured location, exclusively held, with three distinguishable states

That a persisted credential is held under authenticated encryption keyed from operator-supplied material, that each record is encrypted independently so a copied record is not portable, and that wrong key material or a tampered record fails closed and reports distinguishably from having no credential, are the sidecar-credentials capability's rules and hold here as given. What this capability adds is where the store lives, who may hold it, and what its states are.

The store SHALL be at the location the schema's store item names and at no other. The sidecar SHALL persist a credential nowhere else, and SHALL NOT persist the key material protecting it at all, in that store or anywhere. The store SHALL be created with access restricted to the identity the sidecar runs as, and a store found with wider access SHALL be reported as a degraded condition naming it.

A store the sidecar cannot read at all, a store whose record it cannot authenticate, and a store containing no record SHALL be three distinguishable conditions. Only the third SHALL be treated as having no credential; the first two are the fatal conditions this capability enumerates.

Where a store location is already held by another running instance, the sidecar SHALL detect that and SHALL refuse to start with a failure naming the shared location rather than writing into it, because two writers would corrupt records neither instance could then read.

#### Scenario: The three store states are distinguishable

- **WHEN** a sidecar is started in turn against a store it cannot read, a store whose record does not authenticate, and a store containing no record
- **THEN** the three reported conditions carry different enumerated reasons
- **AND** only the third proceeds as having no persisted credential

#### Scenario: No credential is written outside the configured store

- **WHEN** a sidecar obtains, stores, uses, and renews a credential
- **THEN** the only location it wrote credential material to is the configured store

#### Scenario: A store with wider access is reported

- **WHEN** a sidecar finds its configured store accessible beyond the identity it runs as
- **THEN** the condition appears as a degraded condition naming that store
- **AND** it is observable for as long as it holds

#### Scenario: Key material is not persisted

- **WHEN** a sidecar has run, stored, used, and renewed a credential
- **THEN** the supplied key material appears in no location the sidecar wrote

#### Scenario: The store is not world-readable

- **WHEN** a sidecar creates its credential store
- **THEN** access to it is restricted to the identity the sidecar runs as

#### Scenario: A concurrently held store is refused

- **WHEN** a second instance is started against a store location a running instance holds
- **THEN** it refuses to start with a failure naming the shared store
- **AND** the records in the store remain readable by the holding instance

#### Scenario: An empty store is not a failure

- **WHEN** a sidecar starts with a configured store containing no record and a credential supplied by configuration
- **THEN** it starts and establishes a tunnel
- **AND** the empty store is reported distinguishably from an unreadable one

### Requirement: No output at any verbosity carries credential or key material

That a credential secret and its protection material appear in no log line, metric, telemetry payload, error message, diagnostic dump, retained state, or request target is the sidecar-credentials capability's rule and holds here as given. What this capability adds are the outputs only a program running on somebody else's machine produces, and the verbosity dimension.

The credential, the key material protecting it, and every configured secret SHALL additionally appear in no crash record, no support bundle, no configuration report, and no process argument list. This SHALL hold at every verbosity the sidecar can be configured with, including its highest, and throughout acquisition, use, renewal, failure, and shutdown alike. Raising verbosity SHALL widen what is disclosed about conditions and never what is disclosed about secrets.

No partial form SHALL be emitted either: no prefix, no suffix, no length, and no digest. Where a credential must be referred to, the sidecar SHALL refer to it by its non-secret identifier, which is what correlates it with the proxy's own records.

#### Scenario: Nothing leaks at maximum verbosity

- **WHEN** a sidecar is run at its highest verbosity through acquisition, use, renewal failure, and shutdown
- **AND** every output it produced is searched for the credential and the key material
- **THEN** neither appears in any form
- **AND** no prefix, length, or digest of either appears
- **AND** the set of secrets disclosed is the same as at its lowest verbosity, namely none

#### Scenario: An error rendering does not include the value

- **WHEN** an error occurs while using or renewing the credential
- **THEN** the rendered error names the condition and the credential's non-secret identifier
- **AND** it contains no part of the secret

#### Scenario: A crash report is redacted

- **WHEN** the process fails and produces a crash record
- **THEN** that record contains no credential material, key material, or configured secret

#### Scenario: A support bundle is redacted

- **WHEN** an operator collects the diagnostics the sidecar offers for support
- **THEN** the collected material contains no secret value
- **AND** it does contain the credential's non-secret identifier and its expiry

### Requirement: An operator inside the tenant's infrastructure can diagnose without proxy access

The sidecar SHALL answer, from its own local surface, without proxy reachability and without a restart: whether a tunnel is established and for how long; the negotiated contract version; the capability set each side declared; the mount it is admitted for; its build provenance; the configuration in force with secrets redacted; the credential's non-secret identifier, its expiry, and its renewal state; the state of its backend connections; the last establishment attempt with its outcome and, on failure, the enumerated reason; and the inventory of degraded conditions it is currently in, each with the time it began.

For work in flight it SHALL report each exchange's correlation identifier, its age, its phase, the condition it is waiting on, its octets transferred in each direction, and its octets currently buffered. Waiting conditions SHALL be drawn from the same published enumeration the proxy-side diagnostic uses, so that an operator and a tenant describing the same stuck exchange use the same words.

These answers SHALL be produced while every exchange is blocked and while the tunnel is unresponsive, and SHALL NOT require the cooperation of the proxy, the backend, or any blocked exchange. That the response is bounded rather than growing with the number of exchanges in flight is the observability capability's rule for the equivalent proxy-side diagnostic and holds here as given.

The diagnostic SHALL describe carried traffic and SHALL NOT reproduce it: no header field value, no target, no body octet, and no trailer field of any exchange SHALL appear in it. Counts, ages, phases, waiting conditions, and correlation identifiers describe an exchange without disclosing what it carried, and the machine this surface answers on belongs to the tenant but the traffic on it belongs to the tenant's own users.

#### Scenario: A stuck sidecar is diagnosable locally

- **WHEN** every exchange on a sidecar is blocked and the proxy is unreachable from it
- **THEN** the local diagnostic is answered within its configured bound
- **AND** it reports the oldest in-flight exchange with its age, correlation identifier, phase, and waiting condition

#### Scenario: The vocabulary matches the proxy's

- **WHEN** one exchange is awaiting flow-control credit and another is awaiting the backend's first response octet
- **THEN** the two are reported with different enumerated waiting conditions
- **AND** those values are the same published identifiers the proxy-side diagnostic reports

#### Scenario: A failed establishment is explained locally

- **WHEN** a sidecar has never established a tunnel
- **THEN** the diagnostic reports the last attempt, its outcome, and the enumerated reason it failed
- **AND** an unreachable endpoint, a refused credential, and a version incompatibility are distinguishable

#### Scenario: The diagnostic describes traffic without reproducing it

- **WHEN** exchanges carrying distinctive header field values, targets, bodies, and trailer fields are in flight and the diagnostic is collected
- **THEN** none of those values appears anywhere in it
- **AND** each exchange is nonetheless reported with its correlation identifier, age, phase, waiting condition, and octet counts

#### Scenario: Diagnosis requires no restart or verbosity change

- **WHEN** an operator diagnoses a stuck tunnel
- **THEN** everything named in this requirement is available at the verbosity the sidecar is already running at
- **AND** no restart is required, so the state being diagnosed is not destroyed in order to see it

### Requirement: The sidecar bounds its own footprint on every dimension it can grow on

The sidecar SHALL enforce a configured bound on each dimension of its own resource use: concurrent exchanges it will carry; octets buffered per exchange in each direction; octets buffered in total across all exchanges; frames buffered for a bidirectional stream before its far hop is joined; connections held to the backend; and the working memory any translation it performs may occupy. It SHALL declare over the tunnel the same concurrency and frame-size bounds it enforces locally, so that what it advertises and what it does cannot disagree.

Reaching a bound SHALL refuse or reset the work concerned with an enumerated reason naming that bound, and SHALL NOT be resolved by growing beyond it. Reaching a bound on one exchange SHALL NOT disturb the others or the tunnel.

These bounds exist because the sidecar shares a machine with the backend it serves. Exhausting that machine takes down the tenant's own application, which is a worse outcome than refusing the work. They are the sidecar's own footprint bounds and are not a second set of per-tenant bounds; the per-tenant dimensions are enumerated and owned by the tenant-isolation capability.

#### Scenario: The concurrency bound refuses rather than grows

- **WHEN** more exchanges are dispatched to a sidecar than its configured concurrency bound
- **THEN** the excess is refused with a reason naming that bound
- **AND** the number it carries concurrently does not exceed the bound
- **AND** the exchanges already in flight are undisturbed

#### Scenario: Declared and enforced bounds are the same values

- **WHEN** a sidecar establishes a tunnel
- **THEN** the concurrency and frame-size it declares are the values it enforces
- **AND** a frame within its declared bound is accepted and one beyond it is refused

#### Scenario: A slow reader does not grow the buffer

- **WHEN** a backend produces octets faster than the tunnel will accept them
- **THEN** the octets buffered for that exchange do not exceed its configured bound
- **AND** the sidecar stops reading from the backend rather than buffering further

#### Scenario: A slow backend does not grow the buffer

- **WHEN** the proxy delivers request octets faster than the backend will accept them
- **THEN** the octets buffered for that exchange do not exceed its configured bound
- **AND** the sidecar withholds credit rather than buffering further

#### Scenario: One exchange at its bound does not affect the others

- **WHEN** one exchange reaches its buffered-octet bound
- **THEN** it alone is throttled or reset
- **AND** the other exchanges on the tunnel and the tunnel itself continue

#### Scenario: The total bound holds across many exchanges

- **WHEN** a great many exchanges each buffer octets below their per-exchange bound
- **THEN** the total octets buffered by the sidecar does not exceed the configured total
- **AND** further buffering is refused or throttled rather than granted

### Requirement: Every buffer and queue is bounded on both a count and an octet axis

Each place the sidecar holds work SHALL be bounded both by the number of items it holds and by the octets those items occupy, and exceeding either SHALL end the work concerned with a reason that identifies which axis was exceeded. A bound on one axis alone is not sufficient: many small items and one large item are different failures with the same cause.

No queue, buffer, index, or other collection the sidecar maintains SHALL be able to grow without a stated bound. Where a bounded structure holds entries on behalf of work that has ended, those entries SHALL be removed when the work ends, by whatever means it ended, including a reset, a lost tunnel, a lost backend connection, and a shutdown.

#### Scenario: Count and octet overflow are distinguishable

- **WHEN** a buffer is overflowed once by the number of items and once by their total size
- **THEN** the two outcomes name different exceeded axes
- **AND** each identifies the buffer concerned

#### Scenario: Pre-join frame buffering is bounded on both axes

- **WHEN** frames arrive for a bidirectional stream before its far hop is joined, exceeding first the count bound and then the octet bound
- **THEN** each case ends the stream with the reason for that axis
- **AND** neither is resolved by buffering further

#### Scenario: Entries for ended work are removed

- **WHEN** exchanges end by completion, by reset, by a lost tunnel, and by a lost backend connection
- **THEN** no entry for any of them remains in any structure the sidecar holds

#### Scenario: Every holding place refuses rather than grows

- **WHEN** each place the sidecar holds work is driven past its count bound and separately past its octet bound
- **THEN** in every case the work concerned is ended with a reason naming the exceeded axis
- **AND** in no case does the structure grow beyond the bound it stated

### Requirement: Resource use returns to its resting level and does not grow with work served

The sidecar's memory, connection count, and internal entry counts SHALL return to their resting levels once work has ended, and SHALL NOT grow with the number of exchanges it has served over its lifetime. This SHALL hold for exchanges that completed, that were reset, that failed at the backend, that were abandoned by a lost tunnel, and that were left in flight by repeated reconnections.

A sidecar is expected to run for months inside a tenant's infrastructure without being restarted, on a machine whose other occupant is the tenant's own application. Growth proportional to work served is therefore an outage with a delay, not an inefficiency.

#### Scenario: Footprint returns to resting after many exchanges

- **WHEN** two runs carry a very large number of exchanges and a number an order of magnitude smaller, and all of them have ended
- **THEN** the sidecar's connection count and internal entry counts are at their resting levels in both runs
- **AND** the memory held after the larger run does not exceed that held after the smaller by an amount that grows with the number carried

#### Scenario: Failed exchanges leave nothing behind

- **WHEN** a very large number of exchanges are reset, fail at the backend, or are abandoned by a lost tunnel
- **THEN** no entry, buffer, or connection attributable to them remains

#### Scenario: Repeated reconnection does not accumulate

- **WHEN** the tunnel is lost and re-established a great many times, each time with exchanges in flight
- **THEN** the sidecar's resting footprint is unchanged
- **AND** no entry from a superseded tunnel remains

#### Scenario: A late arrival for an ended exchange is discarded

- **WHEN** a frame arrives for an exchange that has already ended
- **THEN** it is discarded with the condition recorded
- **AND** it is not retained, and it does not reach any other exchange
