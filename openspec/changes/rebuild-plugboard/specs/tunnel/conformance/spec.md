## Purpose

Defines the executable conformance suite that is the authority on the wire contract: what it contains, who can run it and against what, how a run is scoped to a contract version and a declared capability set, and what a passing result entitles an implementation to claim. The suite is what makes "write a sidecar in any language" a real offer rather than an aspiration, and it is the only mechanism by which the contract is enforced against implementations the operator does not control.

## ADDED Requirements

### Requirement: The suite is an independently executable artifact

The conformance suite SHALL be distributed as an artifact a third party can obtain and execute against an implementation they wrote themselves. Running it SHALL NOT require access to, or the presence of, any first-party implementation of either role.

The suite SHALL be executable without network access to any host other than the implementation under test, and SHALL NOT retrieve fixtures, schemas, or expected results at run time from anywhere outside the artifact.

#### Scenario: Third party runs the suite against their own implementation

- **WHEN** a party who has never had access to the first-party proxy or sidecar obtains the suite and points it at their own implementation
- **THEN** the run executes to completion
- **AND** the result states which contract requirements that implementation meets and which it does not

#### Scenario: No reference implementation is required

- **WHEN** the suite is run on a host where no first-party implementation is installed or reachable
- **THEN** every case still executes
- **AND** no case is reported as unresolved for want of a counterpart

#### Scenario: The suite runs offline

- **WHEN** the suite is run on a host with no route to any network other than the one carrying the implementation under test
- **THEN** the run produces the same verdicts as a run on a connected host

#### Scenario: A case that reaches outside the artifact is not admitted

- **WHEN** a case obtains a fixture, a schema, or an expected observation from a source outside the artifact
- **THEN** the admission check rejects that case
- **AND** the case does not contribute a verdict

### Requirement: Both roles are exercised

The suite SHALL be able to place either of the contract's two roles under test. In origin-facing-under-test mode — the case of a sidecar — the suite SHALL act as the client-facing tunnel peer. In client-facing-under-test mode — the case of a proxy, or of a separate component terminating a client protocol on its behalf — the suite SHALL act as the origin-facing tunnel peer. The modes SHALL be named for the roles the contract defines rather than for the components that conventionally hold them, so that substituting a component at either end does not leave a mode without a subject.

Each normative requirement that binds both roles SHALL be exercised in both modes. A requirement that binds only one role SHALL declare which, and SHALL be exercised in that mode.

#### Scenario: The origin-facing role under test

- **WHEN** the suite is run in origin-facing-under-test mode against an implementation that speaks only that role
- **THEN** the suite establishes a tunnel as the client-facing peer
- **AND** it reports that implementation's conformance without a proxy being present

#### Scenario: The client-facing role under test

- **WHEN** the suite is run in client-facing-under-test mode against an implementation that speaks only that role
- **THEN** the suite establishes a tunnel as the origin-facing peer
- **AND** it reports that implementation's conformance without a sidecar being present

#### Scenario: A substituted component does not leave a mode without a subject

- **WHEN** the client-facing role is held by a component that terminates a client protocol and does not match mounts
- **THEN** it is a valid subject of client-facing-under-test mode
- **AND** no mode is left with no implementation it can evaluate

#### Scenario: A two-sided requirement is checked twice

- **WHEN** a requirement obliges both peers to preserve some property
- **THEN** the coverage report shows a case for that requirement in each mode
- **AND** an implementation that satisfies the property in one direction only fails the run

### Requirement: The suite supplies every party except the subject

The suite SHALL supply every participant in an exchange other than the implementation under test, including the client that originates traffic at the edge and the origin backend that answers it. An implementation under test SHALL be the only component of a run whose behaviour is not controlled by the suite.

The suite SHALL NOT require an externally provisioned service, a fixed port allocation, a preinstalled dependency, or a manually started process in order for any case to execute.

#### Scenario: Origin behaviour is supplied by the suite

- **WHEN** a case requires a backend that emits a response head and then withholds its body
- **THEN** the suite provides that backend
- **AND** the implementer does not have to write or run one

#### Scenario: No environment is a precondition for a case

- **WHEN** the suite is run on a clean machine with only the implementation under test available
- **THEN** every case executes
- **AND** no case is omitted because a supporting service was absent

#### Scenario: Concurrent runs do not collide

- **WHEN** two runs of the suite execute at the same time on one host
- **THEN** neither run affects the verdicts of the other

#### Scenario: A case requiring an implementer-supplied participant is not admitted

- **WHEN** a case relies on a client, an origin, or a counterpart peer that the implementer must provide
- **THEN** the admission check rejects that case
- **AND** the report distinguishes this from an implementation failure

### Requirement: Every normative requirement is covered

Every normative requirement of the wire contract at a given version SHALL be referenced by at least one case in the suite for that version. The suite SHALL perform its own coverage check and SHALL report any requirement that no case references.

The suite's required coverage reaches beyond the contract in one direction only: several of its cases observe behaviour a proxy owes at the client edge — framing that is refused rather than reconciled, a response defined to carry no body, a trailer section emitted to a client — which the contract does not itself oblige. Such cases SHALL name the edge requirement they exercise, SHALL be admitted, and SHALL be reported under a heading separate from the contract requirements. They SHALL be evaluated only where the subject holds the contract's client-facing role, SHALL NOT contribute to the contract coverage check, and SHALL NOT change the verdict for a contract version.

Because the client-facing role may be held by a component separate from the one that matches mounts, the subject of a run SHALL be identified by the role it holds rather than by which component it is, and a run SHALL state which. A subject holding the client-facing role SHALL be evaluated against every contract requirement binding that role whether or not it also matches mounts, and an edge-attributed case whose behaviour that subject does not itself own SHALL be reported as not applicable to it rather than as failed.

A run in which one or more normative requirements of the contract are unreferenced SHALL NOT report the implementation as conformant, regardless of how many assertions passed.

#### Scenario: Uncovered requirement is named

- **WHEN** the contract contains a normative requirement that no case references
- **THEN** the coverage check fails
- **AND** the report names that requirement as uncovered

#### Scenario: Coverage is by requirement, not by count

- **WHEN** one requirement has many cases and another has none
- **THEN** the coverage check still fails
- **AND** the total number of cases is not offered as evidence of coverage

#### Scenario: Coverage check runs on every invocation

- **WHEN** the suite is invoked to evaluate an implementation
- **THEN** the coverage check runs as part of that invocation
- **AND** its outcome is included in the result

#### Scenario: The subject is identified by its role

- **WHEN** one run evaluates a subject that holds the client-facing role and matches mounts, and another evaluates a subject that holds the client-facing role and does not
- **THEN** each run states the role the subject held
- **AND** both are evaluated against every contract requirement binding that role
- **AND** an edge-attributed case whose behaviour the first subject does not own is reported as not applicable rather than failed

#### Scenario: An edge-attributed case is reported apart from the contract

- **WHEN** a case exercises a behaviour a proxy owes at the client edge rather than one the contract obliges
- **THEN** it names the edge requirement it exercises and is reported under a separate heading
- **AND** it does not contribute to the contract coverage check
- **AND** failing it does not change the verdict for the contract version

### Requirement: Cases exist before the behaviour they cover

The suite for a contract version SHALL be complete and executable before any implementation claiming that version is released, and before the behaviour it covers is implemented. A change that introduces a frame kind, a field, a capability name, or an error code SHALL carry its cases in the same change that defines it.

A contract version whose suite is incomplete SHALL NOT be releasable, and an implementation SHALL NOT claim a version whose suite is incomplete.

#### Scenario: An incomplete suite blocks the release

- **WHEN** a normative requirement is added to the contract and no corresponding case is added in the same change
- **THEN** that change is rejected
- **AND** the contract version does not become releasable

#### Scenario: A capability name gains cases with its definition

- **WHEN** a new capability name is defined in the contract
- **THEN** the suite contains a case for the behaviour available when it is declared
- **AND** a case for the refusal that occurs when it is not declared

#### Scenario: Fixtures precede the implementation

- **WHEN** a contract version is frozen and no implementation of it exists yet
- **THEN** the suite for that version is already complete and executable
- **AND** running it against an empty or stub implementation reports every requirement as unmet

### Requirement: Results are reported against requirements, not assertions

A run SHALL report, for each normative requirement, whether that requirement was met, not met, or not applicable to the declaration under test. A failure SHALL be attributed to the requirement it violates.

Reporting only which assertions failed SHALL NOT satisfy this requirement. Where one failing case bears on more than one requirement, the report SHALL name each.

#### Scenario: A failure names the requirement

- **WHEN** an implementation collapses repeated header fields
- **THEN** the report states that the requirement obliging ordered repeated header pairs is not met
- **AND** it does so without the reader having to interpret an assertion message

#### Scenario: Every requirement has a stated outcome

- **WHEN** a run completes
- **THEN** the report contains an entry for every normative requirement at that version
- **AND** no requirement is absent from the report

#### Scenario: One defect maps to several requirements

- **WHEN** a single defect violates more than one requirement
- **THEN** each violated requirement is reported as unmet
- **AND** the report links them to the same observed behaviour

### Requirement: Required coverage — octet fidelity

The suite SHALL contain cases that a naive implementation fails on the handling of arbitrary octets. At minimum it SHALL include: a body containing a lone octet that is not valid on its own in any multi-octet character encoding; a body containing every possible octet value; a multi-octet character sequence deliberately straddling a frame boundary; and a body carried in frames whose boundaries fall at positions chosen to be hostile to reassembly.

Each such case SHALL assert byte equality between what was sent and what was delivered beyond the implementation under test, in both directions.

#### Scenario: Lone invalid octet survives

- **WHEN** the case sending a body containing a lone invalid octet is run
- **THEN** an implementation that transcodes, validates, or substitutes a replacement character fails
- **AND** the report names the opaque-body requirement as unmet

#### Scenario: Character straddling a frame boundary

- **WHEN** a multi-octet character sequence is deliberately split across two body frames
- **THEN** an implementation that decodes each frame independently fails
- **AND** an implementation that reassembles octets without interpretation passes

#### Scenario: Both directions are covered

- **WHEN** the octet-fidelity cases are run
- **THEN** each is present for a request body and for a response body
- **AND** an implementation correct in one direction only fails

### Requirement: Required coverage — field, method and target fidelity

The suite SHALL contain cases covering the message-shape hazards that a mapping-based or allowlist-based implementation fails. At minimum it SHALL include: a response bearing two fields of the same name whose values cannot legitimately be combined; repeated request fields; a field name received in mixed case; a message arriving with both a content-length field and a chunked transfer-coding field; a percent-encoded path separator inside a single path segment; a collection target ending in a trailing slash; a response to a HEAD request declaring a non-zero body length while carrying no body octets; a method token registered outside the core method set; a method token the contract has never seen; a response whose outcome is reported only in a trailer section; and a request that expects confirmation before its body, in both the confirming and the rejecting case.

#### Scenario: Two same-named response fields

- **WHEN** the case emitting two cookie-setting fields is run
- **THEN** an implementation representing header fields as a mapping from name to one value fails
- **AND** the report names the ordered-header-pairs requirement as unmet

#### Scenario: Conflicting framing fields are refused, not reconciled

- **WHEN** a message arrives declaring both a content length and a chunked transfer-coding
- **THEN** the case asserts that the message is refused
- **AND** an implementation that reconciles the two and forwards the message fails
- **AND** an implementation that carries either framing field over the tunnel fails

#### Scenario: Encoded separator is not normalised

- **WHEN** the case requesting a path with a percent-encoded separator inside a segment is run
- **THEN** the origin supplied by the suite asserts it received that segment with the encoded octets intact
- **AND** an implementation that decodes or splits the segment fails

#### Scenario: HEAD with a declared non-zero length

- **WHEN** the case issuing a HEAD whose response declares a non-zero body length is run
- **THEN** the exchange completes
- **AND** no body octets are delivered to the client
- **AND** an implementation that waits for octets that will never arrive fails on the exchange never completing

#### Scenario: Extension methods pass through

- **WHEN** the cases issuing an out-of-core method token and an entirely unknown method token are run
- **THEN** the origin asserts it received each token byte-identically
- **AND** an implementation with a method allowlist fails both

#### Scenario: Outcome carried only in a trailer section

- **WHEN** the case whose origin reports the outcome of a call exclusively in a trailer field is run
- **THEN** the client supplied by the suite asserts it received that field as a trailer
- **AND** an implementation that merges the trailer into the header section fails
- **AND** an implementation that discards the trailer fails even though the response status was successful

#### Scenario: Body withheld until confirmation

- **WHEN** the case in which a client expects confirmation before sending its body is run and the origin rejects the request
- **THEN** the client receives the rejection
- **AND** the origin supplied by the suite asserts it received no request body octets
- **AND** an implementation that forwards the head only after the body is complete fails

### Requirement: Required coverage — duration, exhaustion, interleaving and abandonment

The suite SHALL contain cases that a buffering, aggregating, wall-clock-bounded, or serialising implementation fails. At minimum it SHALL include: a response that emits its head and then withholds its body for longer than any bound the implementation applies to a whole request; a response whose body does not end; a response body larger than the memory available to the implementation under test; a request body larger than that memory; a client that vanishes part-way through receiving a response; a large transfer and a short exchange in flight on one tunnel at the same time; and a tunnel saturated with body frames while a keepalive exchange is outstanding.

#### Scenario: Head then a stall beyond any total bound

- **WHEN** the case emitting a response head and withholding the body beyond the configured total-duration bound is run
- **THEN** the client supplied by the suite observes the response head during the stall
- **AND** the exchange is not terminated for elapsed total time
- **AND** an implementation with a single total-duration cap fails

#### Scenario: Body larger than memory

- **WHEN** the case transferring a body larger than the memory available to the implementation under test is run
- **THEN** the body is delivered in full
- **AND** an implementation that accumulates the body before emitting it fails by exhausting memory or by never emitting

#### Scenario: Client vanishes mid-exchange

- **WHEN** the client supplied by the suite disappears while a response is in transfer
- **THEN** the origin supplied by the suite asserts that its request was cancelled
- **AND** an implementation that leaves the origin producing into nothing fails

#### Scenario: Slow consumer bounds buffered octets

- **WHEN** the client supplied by the suite consumes a large response slowly against an implementation that declared the flow-control capability
- **THEN** the octets held by the implementation under test remain within the bound it declared
- **AND** an implementation that declares the capability and then does not withhold credit fails by exceeding that bound
- **AND** the case is skipped by declaration, not failed, against an implementation that did not declare it

#### Scenario: Credit accounting is checked whatever was declared

- **WHEN** the suite emits body octets beyond the window in force against an implementation that declared no flow-control capability
- **THEN** the implementation reports a flow-control violation
- **AND** the case is not skipped by declaration

#### Scenario: A small exchange overtakes a large one

- **WHEN** a short exchange is issued while a transfer far larger than the maximum frame size is in flight on the same tunnel
- **THEN** the short exchange completes before the large transfer does
- **AND** an implementation that carries one exchange to completion before starting another fails

#### Scenario: Keepalive under saturation

- **WHEN** the tunnel is saturated with body frames and a keepalive exchange is outstanding
- **THEN** the keepalive completes and the tunnel is not torn down
- **AND** an implementation whose keepalive is queued behind body frames fails

### Requirement: Required coverage — bidirectional streams and refusal

The suite SHALL contain cases covering bidirectional stream fidelity and capability refusal. At minimum it SHALL include: a message fragmented across an initial frame and continuation frames; a close carrying a code in the application-defined range with a reason; a non-accepting handshake response from the origin; an ordering case in which the first message after establishment is mandatory; and a request requiring a capability the implementation under test has not declared.

#### Scenario: Fragmented message stays fragmented

- **WHEN** the case sending a message split across an initial frame and continuation frames is run
- **THEN** the origin supplied by the suite asserts it received the same sequence of frames with the same finality indicators
- **AND** an implementation built on a message-level abstraction fails by delivering one coalesced message

#### Scenario: Application-range close code survives

- **WHEN** the case closing with a code in the application-defined range and a reason is run
- **THEN** the peer supplied by the suite asserts it received that same code and reason
- **AND** an implementation that maps it onto a protocol-level code fails

#### Scenario: A non-accepting handshake is relayed, not replaced

- **WHEN** the origin supplied by the suite refuses to establish a bidirectional stream and answers with a challenge status and header fields
- **THEN** the client supplied by the suite receives that status and those fields
- **AND** the origin asserts it observed exactly one establishment attempt
- **AND** an implementation that substitutes a generic gateway error, or that opens a preliminary probe connection, fails

#### Scenario: Ordering after establishment

- **WHEN** several messages are sent in immediate succession after establishment
- **THEN** the origin asserts it received them in the order sent
- **AND** an implementation that dispatches each message concurrently fails

#### Scenario: Capability-absent request is refused

- **WHEN** a request requiring a capability the implementation under test did not declare is issued
- **THEN** the client receives a refusal naming the missing capability
- **AND** the origin supplied by the suite asserts it never received the request
- **AND** an implementation that serves the request at reduced fidelity fails

### Requirement: Assertions are made on the wire

Every case SHALL assert against the octets actually transferred and the octets actually delivered to the party beyond the implementation under test. A case SHALL NOT assert against a value produced by the implementation's own encoding or decoding code, nor against any representation substituted by a harness in place of the real encoding.

The suite SHALL encode and decode independently, from the normative encoding specification alone.

#### Scenario: The subject's own codec is not trusted

- **WHEN** an implementation's internal representation of a message differs from what it puts on the wire
- **THEN** the verdict follows what was on the wire
- **AND** an implementation whose internal representation is correct while its wire output is not fails

#### Scenario: A bypassed encoder is detected rather than accommodated

- **WHEN** an implementation is offered to the suite through a harness that passes internal values to the counterpart without encoding them
- **THEN** the suite declines that harness and exchanges encoded octets over the transport instead
- **AND** an implementation whose only conforming path is the bypassed one is reported as non-conformant

#### Scenario: Field names and values are asserted at the octet level

- **WHEN** a case asserts that a field crossed the tunnel
- **THEN** the assertion is on the name and value octets present on the wire
- **AND** an implementation whose encoded form differs from its decoded form fails

#### Scenario: Delivery is asserted at the far party

- **WHEN** a case checks that a field, a body, or a method survived
- **THEN** the assertion is made by the origin or client supplied by the suite
- **AND** not by inspecting state inside the implementation under test

### Requirement: A case never repairs what it waits for

No case, and no helper the suite provides, SHALL take an action that causes the condition it is waiting for to become true. A case SHALL NOT retry an operation until it succeeds, trigger a reload, flush a buffer, or otherwise nudge the implementation under test while waiting for an outcome it is asserting.

A case that times out waiting for an expected outcome SHALL report that requirement as unmet. It SHALL NOT report success by any other route.

#### Scenario: A waiting helper does not act

- **WHEN** a case waits for an implementation to propagate a change
- **AND** the propagation never occurs
- **THEN** the case reports the requirement as unmet
- **AND** no fallback action is taken that would make the assertion pass

#### Scenario: No retry-until-pass

- **WHEN** an operation under assertion fails on its first attempt
- **THEN** the case reports the failure
- **AND** the outcome is not re-evaluated after a repeated attempt

#### Scenario: Waiting is bounded and reported

- **WHEN** a case waits for an outcome that does not arrive within its declared bound
- **THEN** the run completes rather than hanging
- **AND** the report distinguishes a timed-out expectation from an incorrect observed value

### Requirement: Runs are deterministic and cases are independent

Repeated runs of the suite against an unchanged implementation SHALL produce identical verdicts. Verdicts SHALL NOT depend on wall-clock date or time, on host processor speed, on unseeded randomness, or on the presence of other work on the host.

Any case SHALL be executable alone, in any subset, in any order, and concurrently with other cases, with unchanged verdicts. No case SHALL depend on state left behind by another.

#### Scenario: Repeated runs agree

- **WHEN** the suite is run repeatedly against an unchanged implementation
- **THEN** every run yields the same set of met and unmet requirements

#### Scenario: A single case can be run alone

- **WHEN** one case is selected and run by itself
- **THEN** it produces the same verdict as it does within a full run

#### Scenario: Order does not matter

- **WHEN** the cases are run in a different order, or concurrently
- **THEN** the verdicts are unchanged

#### Scenario: Randomness is seeded and reported

- **WHEN** a case uses generated input
- **THEN** the seed is recorded in the result
- **AND** re-running with that seed reproduces the same input and the same verdict

#### Scenario: An intermittent verdict is not a pass

- **WHEN** a case yields different outcomes across repeated runs against one unchanged build
- **THEN** that case is reported as unresolved rather than met
- **AND** the run does not report the implementation as conformant

### Requirement: Timing is expressed against declared bounds

A case whose subject is a duration SHALL be expressed relative to a bound the implementation under test declares or is configured with, not against an absolute elapsed time chosen by the suite. The suite SHALL configure or read that bound and SHALL assert relative to it.

A verdict SHALL NOT change because the host was slower or faster, within a stated tolerance the suite documents and reports.

#### Scenario: Stall case is relative to the configured bound

- **WHEN** the case that stalls a response is run against an implementation configured with a shorter total-duration bound
- **THEN** the stall is extended to exceed that bound
- **AND** the verdict is the same as against an implementation with a longer bound

#### Scenario: A constrained host does not change the verdict

- **WHEN** the suite is run with the processor and input/output available to it reduced to a fraction of what the authoring host had
- **THEN** the set of met and unmet requirements is unchanged
- **AND** no case is reported as unmet solely because an observation arrived later than on the authoring host

#### Scenario: Timing tolerance is stated

- **WHEN** a case asserts on elapsed behaviour
- **THEN** the tolerance it allows is recorded in the result
- **AND** a result near that tolerance is reported as such rather than silently passed

### Requirement: A full run completes within a declared bound

The suite SHALL declare a bound on the duration of a full run and SHALL report the elapsed duration of the run and of each case. A run that exceeds the declared bound SHALL be reported as having exceeded it rather than passing without comment.

A case SHALL reach a long duration by configuring the bound of the implementation under test rather than by waiting a fixed period. A case that waits a fixed period where the subject exposes a configurable bound SHALL be rejected by the admission check. Meeting the duration bound SHALL NOT be achievable by omitting cases.

#### Scenario: Duration is reported against the bound

- **WHEN** a full run completes
- **THEN** the result records the elapsed duration of the run and of each case
- **AND** a run that exceeded the declared bound is reported as having exceeded it

#### Scenario: A fixed wait is not admitted

- **WHEN** a case waits a fixed period in order to exceed a bound the implementation under test exposes as configurable
- **THEN** the admission check rejects the case
- **AND** the requirement it claimed to cover is reported as uncovered

#### Scenario: A faster run is not a smaller run

- **WHEN** the set of cases is reduced so that a run finishes within the bound
- **THEN** the coverage check fails for every requirement left unreferenced
- **AND** the run is not reported as conformant

### Requirement: A run is scoped to one contract version

Each run SHALL be scoped to a single contract version, and the resulting verdict SHALL apply to that version alone. The suite SHALL retain the cases for every version it has published, so that an implementation of an older version can still be evaluated.

An implementation SHALL be reported as conformant for a version only when every requirement of that version is met. Conformance for one version SHALL NOT imply conformance for any other.

#### Scenario: Older version still evaluable

- **WHEN** an implementation targets a contract version older than the newest published one
- **THEN** the suite for that older version runs
- **AND** it reports a verdict for that version without reference to newer requirements

#### Scenario: Newer requirements do not fail an older claim

- **WHEN** a requirement is added at a newer contract version
- **THEN** an implementation evaluated against the older version is not marked unmet for it

#### Scenario: Verdicts are per version

- **WHEN** an implementation is evaluated against two contract versions
- **THEN** two separate verdicts are produced
- **AND** neither is inferred from the other

### Requirement: A verdict does not depend on the subject's instance topology

The contract is spoken between one sidecar and the proxy instance holding its tunnel, and carries no identifier of an instance. Cases SHALL therefore assert nothing about which instance of a subject served an exchange, SHALL NOT require the instance holding the suite's sidecar tunnel to be the instance the case's client traffic reaches, and SHALL NOT require the subject to be deployed as a single instance.

Where a subject is deployed as more than one instance, a run SHALL produce the same verdict, and the same per-requirement results, as a run against a single instance — including a run in which every case's client traffic is directed at an instance other than the one holding the suite's sidecar tunnel. A case that passes only when those are the same instance SHALL be a defect of the case, reported as such rather than as a failure of the subject.

A verdict SHALL NOT be presented as evidence for behaviour that spans instances. Selection of a tunnel held by another instance, convergence of the registry after a partition, and accounting of a bound across instances are specified by the capabilities that own them; a run SHALL state the topology it was conducted against, and a result SHALL NOT claim coverage of any of those behaviours.

#### Scenario: The same verdict in both topologies

- **WHEN** the suite is run against a subject deployed as one instance and against the same build deployed as more than one, with every case's client traffic directed at an instance other than the one holding the suite's sidecar tunnel
- **THEN** the two runs produce the same verdict
- **AND** the per-requirement results are the same in both

#### Scenario: No case asserts which instance served

- **WHEN** the published cases for a version are examined
- **THEN** none asserts the identity of the instance that served an exchange
- **AND** none requires the tunnel-holding instance and the instance receiving client traffic to be the same

#### Scenario: A co-location assumption is a defect of the case

- **WHEN** a case passes against a single-instance subject and fails against a multi-instance one for no reason the contract states
- **THEN** it is reported as a defect of the case
- **AND** it is not reported as a failure of the subject

#### Scenario: A result states its topology and claims no more

- **WHEN** a result produced against a single-instance subject is read
- **THEN** it states the topology the run was conducted against
- **AND** it claims no coverage of cross-instance selection, of registry convergence after a partition, or of bound accounting across instances

### Requirement: Mixed-version pairings are exercised

An implementation SHALL be evaluated against counterparts that are not of its own version. At each contract version, the suite SHALL pair the implementation under test with a counterpart declaring the oldest version that version is obliged to serve, with a counterpart declaring a newer version, and with a counterpart whose declared range does not overlap at all.

The suite SHALL also present inputs an implementation is not expected to understand: an unrecognised field, an unrecognised capability name, an unrecognised error code, and a frame kind reserved at that version but unimplemented by the subject. For each, the suite SHALL assert that the exchange proceeds as it would without the unrecognised input, or that only the stream concerned is reset, and that the tunnel survives.

An implementation that terminates a tunnel, abandons an unrelated exchange, or changes an otherwise observable behaviour when given input it does not recognise SHALL be reported as non-conformant.

#### Scenario: An older counterpart is still served

- **WHEN** the implementation under test is paired with a counterpart declaring the oldest version it is obliged to serve
- **THEN** the tunnel is established at that older version
- **AND** the requirements of that older version are evaluated against the implementation
- **AND** no case requires the counterpart to understand anything introduced after that version

#### Scenario: Unrecognised field, capability and error code are tolerated

- **WHEN** the suite sends a field, a capability name, and an error code the implementation under test does not recognise
- **THEN** the exchange produces the same observable outcome as the equivalent exchange without them
- **AND** the tunnel is not terminated
- **AND** an implementation that refuses the exchange or closes the tunnel is reported as non-conformant

#### Scenario: A reserved but unimplemented frame kind resets one stream

- **WHEN** the suite sends a frame kind reserved at the version under evaluation that the implementation under test does not implement
- **THEN** the implementation resets that stream with an error naming the unimplemented kind
- **AND** exchanges in flight on other streams complete
- **AND** an implementation that terminates the tunnel fails

#### Scenario: A non-overlapping range is refused, not degraded

- **WHEN** the suite offers only a version range the implementation under test does not support
- **THEN** the implementation refuses the tunnel with an error distinguishable from an authentication failure
- **AND** an implementation that establishes the tunnel and serves traffic anyway fails

### Requirement: Published cases are frozen

Once the suite for a contract version is published, the input a case supplies and the observation it requires SHALL NOT change in place. A defect in a case SHALL be corrected by publishing a new suite revision for that version, and correcting it SHALL NOT silently alter the meaning of results already issued.

The suite SHALL carry a revision identifier per published version, every result SHALL record the revision that produced it, and any change to a case's input or expected observation SHALL change that identifier.

#### Scenario: An edited case changes the revision

- **WHEN** the input or the expected observation of a case in a published version is changed
- **THEN** the suite revision identifier changes
- **AND** results issued under the previous revision remain distinguishable from results issued under the new one

#### Scenario: Weakening an expectation is a recorded correction

- **WHEN** the expected observation of a published case is weakened so that a previously failing implementation passes
- **THEN** the change is published as a new revision naming the requirement whose reading changed
- **AND** a change made without a new revision is rejected

#### Scenario: A result of unknown provenance is not evidence

- **WHEN** a result names a suite revision the suite does not recognise
- **THEN** it is not accepted as evidence of conformance

### Requirement: Declaration-based skips are distinct from failures, and are the only skips

A case exercising a capability the implementation under test has not declared SHALL be reported as skipped-by-declaration, naming the capability. Skipped-by-declaration SHALL be a distinct outcome from met and from unmet, and SHALL NOT be counted as either.

No other form of skip SHALL exist. A case that cannot be executed for any reason other than an undeclared capability SHALL be reported as unresolved, and a run containing an unresolved case SHALL NOT report the implementation as conformant. A run in which no case executed SHALL be reported as a failure, never as a pass.

#### Scenario: Undeclared capability yields a distinct outcome

- **WHEN** an implementation does not declare datagram support and the datagram cases run
- **THEN** those cases are reported as skipped-by-declaration naming that capability
- **AND** they are not reported as met
- **AND** they are not reported as unmet

#### Scenario: Declared capability must then be met

- **WHEN** an implementation declares a capability
- **THEN** the cases for that capability execute
- **AND** failing any of them makes the run non-conformant

#### Scenario: An unrunnable case is not a skip

- **WHEN** a case cannot execute because of an environmental fault
- **THEN** it is reported as unresolved
- **AND** the run does not report the implementation as conformant

#### Scenario: An empty run is a failure

- **WHEN** the suite is invoked and zero cases execute
- **THEN** the run is reported as failed
- **AND** the report states that no case executed

### Requirement: A minimal declaration is not a route to conformance

The suite SHALL define, for each contract version, the set of requirements that no capability declaration exempts an implementation from, covering at minimum octet-faithful bodies, ordered repeated header fields, unmodified method tokens, raw request targets, framed exchange with stream identifiers, per-stream ordering, credit accounting, cancellation, enumerated errors, and version negotiation. This set SHALL be exactly the contract's baseline at that version: a requirement the contract marks as scoped to an optional capability SHALL NOT appear in it, and a requirement the contract marks baseline SHALL NOT be omitted from it. Those cases SHALL execute against every implementation whatever it declares, and SHALL never be reported as skipped-by-declaration.

The capability set a run is scoped to SHALL be the set the implementation declared on the tunnel during that run, not a set supplied to the suite alongside it. A run in which no case reached a verdict of met SHALL NOT be reported as conformant.

#### Scenario: The baseline set tracks the contract's own marking

- **WHEN** the contract marks a requirement as scoped to an optional capability
- **THEN** that requirement is absent from the set no declaration exempts an implementation from
- **AND** a requirement the contract marks baseline is present in it

#### Scenario: Declaring the minimum does not skip the baseline

- **WHEN** an implementation declares the smallest capability set the contract permits
- **THEN** the baseline cases execute
- **AND** none of them is reported as skipped-by-declaration
- **AND** failing any of them makes the run non-conformant

#### Scenario: The declaration is taken from the tunnel

- **WHEN** the capability set an implementer supplies to the suite differs from the one the implementation sends when the tunnel is established
- **THEN** the run is scoped to the set sent on the tunnel
- **AND** the discrepancy is reported

#### Scenario: An all-skipped run is not conformant

- **WHEN** every case that would otherwise execute is skipped by declaration
- **THEN** the run is not reported as conformant
- **AND** the report states that no requirement was demonstrated

### Requirement: The suite is proven against deliberately broken implementations

The suite SHALL ship with a catalogue of deliberately defective counterparts, each defective in one specific, named way, and each paired with the requirement its defect violates. Running the suite against each defective counterpart SHALL produce a non-conformant verdict naming that requirement.

The catalogue SHALL include, at minimum, a counterpart that collapses repeated header fields, one that transcodes bodies, one that restricts methods to an allowlist, one that normalises path segments, one that aggregates a response before emitting it, one that applies a single total-duration bound, one that coalesces fragmented bidirectional messages, one that ignores a capability declaration, one that terminates the tunnel on an unrecognised field or frame kind, and one that declares no optional capability in order to have its cases skipped.

#### Scenario: Each defect is detected

- **WHEN** the suite is run against a defective counterpart from the catalogue
- **THEN** the verdict is non-conformant
- **AND** the requirement corresponding to that defect is reported as unmet

#### Scenario: A defect is detected by an identified case

- **WHEN** a defective counterpart is rejected
- **THEN** the report names at least one case that rejected it
- **AND** that case is the one recorded in the catalogue as covering the defect

#### Scenario: A correct counterpart is not rejected

- **WHEN** the suite is run against a counterpart with the defect removed and nothing else changed
- **THEN** the verdict is conformant for the version under evaluation

#### Scenario: A new requirement gains a defect

- **WHEN** a normative requirement is added to the contract
- **THEN** the catalogue gains a counterpart that violates it
- **AND** the suite demonstrates that it rejects that counterpart

### Requirement: The gate that runs the suite fails its caller on a non-conformant verdict

That a gate invocation which executes nothing, cannot find what it was meant to run, or is misconfigured is a failed gate rather than a clean result; that each invocation of one obligation is verified independently where the obligation is enforced in more than one place; and that a gate's own verification recurs on a declared interval as well as on change, are `operability/packaging`'s rules for every gate a release or a merge depends on, and hold here as given for this one. What this capability adds is the part specific to the suite: the verdict the gate must act on.

The invocation that runs the suite as a release or merge gate SHALL be verified to execute the suite against the subject named to it and to fail its caller on a non-conformant verdict, and that verification SHALL be executed automatically rather than asserted by inspection. A verdict of non-conformant SHALL fail the caller whatever the count of failing cases, and a run that produced no verdict SHALL fail it as well; a gate SHALL NOT pass on a run that executed cases without reaching a verdict, and SHALL NOT convert a non-conformant verdict into a warning.

The gate SHALL act on the verdict the run emitted and SHALL NOT recompute, reinterpret, or override it. A gate that derives its own outcome from case counts, from the machine-readable result's individual fields, or from any evidence other than the verdict SHALL NOT be considered to satisfy this requirement, because the verdict is where this capability's rules about skips, unresolved cases and baseline coverage have already been applied.

#### Scenario: A non-conformant verdict fails the caller

- **WHEN** the gate runs the suite against a defective counterpart
- **THEN** the invoking process observes a failure outcome
- **AND** the change or release the gate protects does not proceed

#### Scenario: One failing case is enough

- **WHEN** a run produces a non-conformant verdict on a single case with every other case passing
- **THEN** the gate fails its caller
- **AND** the verdict is not reported as a warning or as a partial pass

#### Scenario: A run with no verdict is not a pass

- **WHEN** the gate's invocation executes cases but the run ends without producing a verdict
- **THEN** the gate fails its caller
- **AND** the outcome is distinguishable from a run whose verdict was conformant

#### Scenario: A gate that reinterprets the verdict does not satisfy this

- **WHEN** a gate derives its outcome from the count of failing cases, or from any field of the result other than the verdict, and admits a run the verdict reported as non-conformant
- **THEN** it is reported as not satisfying this requirement
- **AND** the release or merge does not proceed on its evidence

### Requirement: Results are machine-readable

A run SHALL emit a machine-readable result with a stable, versioned shape, containing at minimum: the contract version evaluated, the suite revision that produced it, the declared capability set of the implementation under test, an identifier for the build evaluated, the configuration in effect, the outcome for every normative requirement, the outcome for every case with its requirement references, any seeds and tolerances used, the elapsed duration of the run, and the overall verdict.

The shape of the result SHALL be versioned independently of the contract, and a consumer encountering an unrecognised field SHALL ignore it and continue. A run that terminates before every case has executed SHALL still emit a result.

#### Scenario: A tool can compare two runs

- **WHEN** two machine-readable results for the same contract version are compared
- **THEN** the requirements whose outcomes differ can be identified without parsing prose

#### Scenario: The result records what was evaluated

- **WHEN** a result is read after the fact
- **THEN** it states the contract version, the suite revision, the declared capability set, the configuration, and the build identifier it applies to

#### Scenario: Result shape evolves additively

- **WHEN** a field is added to the result shape
- **THEN** an existing consumer continues to read the result
- **AND** it ignores the field it does not recognise

#### Scenario: An aborted run still produces a result

- **WHEN** a run terminates before every case has executed
- **THEN** a machine-readable result is still emitted
- **AND** it marks the run incomplete and names the cases that did not execute
- **AND** the overall verdict is not conformant

### Requirement: The human-readable summary names the violated requirement

A run SHALL also emit a human-readable summary. For every unmet requirement, the summary SHALL name the requirement, state what was expected and what was observed, and give enough detail to reproduce the case in isolation.

The summary SHALL NOT report a failure solely as an assertion mismatch, a stack trace, or a rendering of an internal value.

#### Scenario: An implementer can act on the summary alone

- **WHEN** an implementation fails a case
- **THEN** the summary names the violated requirement, the input that triggered it, the expected observation, and the actual observation
- **AND** an implementer can reproduce the case from the summary without reading the suite's source

#### Scenario: A conformant run says so plainly

- **WHEN** every requirement is met
- **THEN** the summary states the contract version passed and the capability set it was evaluated against
- **AND** it lists the requirements reported as skipped-by-declaration

#### Scenario: Failure output is not an internal rendering

- **WHEN** a case fails
- **THEN** the summary contains no rendering of a host-language value in place of an explanation

### Requirement: Cases derive only from normative requirements

Every case SHALL name the normative requirement or requirements it exercises — of the wire contract, or of the client-edge capabilities where the case is edge-attributed — and SHALL assert only behaviour those requirements oblige. The suite SHALL reject a case that names no requirement or that asserts behaviour no requirement mandates.

Where an implementation fails a case for behaviour the contract does not in fact require, the outcome SHALL be treated as a defect in the contract or in the case, not as a conformance violation.

#### Scenario: An unattributed case is not admitted

- **WHEN** a case is added without naming a requirement
- **THEN** the suite's admission check fails
- **AND** the case does not run

#### Scenario: Behaviour beyond the contract is not asserted

- **WHEN** a case asserts an outcome that no normative requirement obliges
- **THEN** the admission check fails
- **AND** the report distinguishes this from an implementation failure

#### Scenario: A contract defect is not an implementation failure

- **WHEN** a case is found to assert an outcome its named requirement does not oblige, because two conforming readings of that requirement produce different observable behaviour
- **THEN** the outcome is reported as a contract or case defect, an outcome distinct from unmet
- **AND** the implementation is not reported as non-conformant on the strength of that case

### Requirement: A conformance result is bound to what it evaluated

A passing result SHALL be bound to the contract version evaluated, the suite revision that produced it, the capability set the implementation declared during the run, an identifier for the build evaluated, and the configuration in effect during the run. A result SHALL NOT be presented as evidence for a different version, revision, declaration, build, or configuration.

An implementation that changes its declared capability set SHALL require a new run before that declaration is treated as conformance-backed. Where the implementation was evaluated with any bound, limit, or protective behaviour set differently from the value it ships with, the result SHALL record that difference.

#### Scenario: A widened declaration invalidates the result

- **WHEN** an implementation declares a capability it did not declare during its passing run
- **THEN** the stored result does not cover the new declaration
- **AND** a new run is required before that capability is treated as conformance-backed

#### Scenario: A result does not transfer between builds

- **WHEN** an implementation is rebuilt with a change to its tunnel handling
- **THEN** the prior result no longer applies to the new build

#### Scenario: A relaxed configuration is recorded and does not carry

- **WHEN** an implementation is evaluated with a bound, limit, or protective behaviour set differently from the value it ships with
- **THEN** the result records the configuration that was in effect
- **AND** the result is not presented as evidence for the shipped configuration

#### Scenario: A release states the evidence it carries

- **WHEN** a release declares support for a contract version
- **THEN** a passing result for that version, that declaration, and that build is retrievable
- **AND** an operator can determine which versions a deployed build was proven against
