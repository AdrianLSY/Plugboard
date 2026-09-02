## Purpose

Defines what an operator can see and do while the system is running: which signals are produced and where they are actually delivered, how one exchange is followed across the client edge, the tunnel and the backend, what must be measurable without unbounded cost, how liveness and readiness differ, and the diagnostics that answer "a tenant says their tunnel is stuck" without shell access, a code change, or a restart.

The proxy is a multi-instance installation, so every obligation stated here is stated for the installation and not for whichever instance a query happened to reach. A sidecar's tunnel is held by one instance while a client's request arrives at whatever instance the load balancer chose, which means the question this capability exists to answer — is a sidecar connected for this mount, what is in flight on it, and what is the oldest exchange waiting on — cannot be answered from the state of a single instance. Two rules run through everything below. An answer covering less than the whole installation is labelled as such and never presented as complete, because an unlabelled partial answer during a partition is precisely when an operator draws the wrong conclusion. And every record, measurement, and diagnostic value identifies the instance it came from, so that a fault on one instance can be told apart from a fault everywhere.

That the registry converges after a partition, with no operator action and no sidecar reconnection, and that a sidecar connected to one instance is selectable from any instance, are `tunnel/sidecar-registry`'s obligations and are taken as given here. What this capability owns is what an operator can see — including while that convergence has not yet happened.

## ADDED Requirements

### Requirement: Signals are delivered, not merely emitted

Every class of signal the system produces — records of events, measurements, and diagnostic state — SHALL be delivered to a destination the operator has configured. The system SHALL treat a signal class with no configured destination as a configuration error and SHALL refuse to start, naming every such class in one refusal rather than one per restart. An operator MAY configure a destination that explicitly discards a signal class; that configuration SHALL be reported at startup, so that discarding a class is a stated intent and never a default.

The system SHALL maintain an inventory of the signals it is capable of producing, and delivery SHALL be demonstrable: for each inventoried signal, exercising the condition that produces it SHALL result in an observable record at a configured, available destination. Emitting a signal that no configured destination receives SHALL NOT satisfy any requirement in this capability; an obligation stated here is met only by what arrives at a destination.

#### Scenario: Missing destination refuses startup

- **WHEN** a component is started with no destination configured for a signal class it produces
- **THEN** it refuses to start
- **AND** the refusal names every signal class that lacks a destination, not only the first

#### Scenario: Discarding is configurable but never silent

- **WHEN** a component is started with a signal class configured to be discarded
- **THEN** it starts
- **AND** it produces a startup record naming that class as discarded by configuration

#### Scenario: Exercising a condition yields a record at the destination

- **WHEN** a condition that produces a signal is exercised against a running component with a destination configured
- **THEN** a corresponding record is observable at that destination
- **AND** the record is observable without inspecting the component's internal state

#### Scenario: Every inventoried signal is proven to arrive

- **WHEN** each signal in the inventory is exercised in turn
- **THEN** each produces an observable record at a configured destination
- **AND** any inventoried signal that produces no such record is reported as a failure

#### Scenario: An unreachable inventory entry is a defect

- **WHEN** the inventory names a signal that no reachable condition can produce
- **THEN** the delivery report marks that entry as unproven
- **AND** it is not counted toward the proportion of the inventory demonstrated to arrive

### Requirement: Observability failure never becomes a traffic failure

When a signal destination is unavailable, slow, or rejecting, the component SHALL continue to serve traffic. Signals awaiting delivery SHALL be held within a configured bound on both count and total octets; beyond that bound signals SHALL be discarded rather than accumulated.

Discarded signals SHALL be counted, and the count SHALL be recoverable once delivery resumes. Delivery SHALL resume without a restart when the destination becomes available.

Assembling an answer that spans instances SHALL NOT be on the path of any exchange. An instance that cannot reach another instance SHALL continue to serve traffic and SHALL continue to deliver its own signals to its configured destinations; it SHALL NOT hold or discard a signal of its own because another instance is unreachable, and it SHALL NOT depend on another instance in order to deliver one.

#### Scenario: Destination outage does not stall requests

- **WHEN** a configured destination stops accepting signals
- **THEN** requests continue to be served at their normal outcomes
- **AND** no exchange is delayed waiting for a signal to be delivered

#### Scenario: Pending signals are bounded

- **WHEN** a destination is unavailable for an extended period under load
- **THEN** the memory held for undelivered signals remains within the configured bound

#### Scenario: Discards are counted and later reported

- **WHEN** signals are discarded because the bound was reached
- **AND** the destination later becomes available
- **THEN** the number discarded during the outage is reported
- **AND** delivery resumes without a restart

#### Scenario: A slow destination does not become a slow request

- **WHEN** a configured destination continues to accept signals but responds arbitrarily slowly
- **THEN** the latency of exchanges served during that period is unchanged
- **AND** signals beyond the configured bound are discarded rather than made to wait behind the destination

#### Scenario: An unreachable instance does not slow traffic or lose local signals

- **WHEN** one instance cannot reach the rest of the installation for an extended period under load
- **THEN** the exchanges it serves are served at their normal outcomes and their latency is unchanged
- **AND** its own records and measurements continue to arrive at its configured destinations
- **AND** an installation-wide diagnostic answered during that period is incomplete rather than slow

### Requirement: Every exchange produces exactly one outcome record

Every exchange that is admitted at the edge SHALL produce exactly one outcome record when it ends, whatever the manner of its ending. For this requirement an exchange is any unit of work the tunnel carries on one stream, and an established bidirectional stream session SHALL therefore produce exactly one outcome record when the session ends, not one per frame and not none. A session's outcome SHALL name the cause that ended it, drawn from the same enumeration, and SHALL be distinguishable from the outcome of a request/response exchange.

The record SHALL state an outcome drawn from a stable enumerated set, which SHALL distinguish at minimum: completion, refusal before the exchange reached a sidecar, no sidecar available, refusal for an undeclared capability, cancellation by the client, cancellation by the backend, each class of exceeded time bound, each class of exceeded resource bound, each cause for which a bidirectional stream is closed by the proxy, failure of the tunnel while the exchange was in flight, and loss of the instance holding the tunnel while the exchange was in flight.

No admitted exchange SHALL end without an outcome record, including one ended by drain, by shutdown, or by operator action. An exchange whose ending is provoked by more than one condition at once SHALL still produce exactly one record, naming the condition that ended it.

An outcome record SHALL NOT be sampled away, suppressed as a repeat, or replaced by an aggregate. Where an outcome record cannot be delivered because its destination is unavailable, it SHALL be counted among the discards rather than treated as never produced.

The one record is one record for the installation, not one per instance that took part. Where an exchange is admitted at one instance and dispatched to a tunnel held by another, exactly one outcome record SHALL exist for it; the other instance's signals about that exchange SHALL be joinable to it by the correlation identifier and SHALL NOT constitute a second outcome. An outcome record SHALL still be produced when the instance holding the tunnel becomes unreachable while the exchange is in flight.

#### Scenario: A completed exchange is recorded once

- **WHEN** an exchange completes normally
- **THEN** exactly one outcome record exists for it
- **AND** its outcome names completion

#### Scenario: A vanished client is recorded

- **WHEN** a client disconnects mid-response
- **THEN** an outcome record exists naming cancellation by the client
- **AND** it is distinguishable from a backend failure and from an exceeded time bound

#### Scenario: A refused exchange is recorded

- **WHEN** an exchange is refused because no sidecar is available for the mount
- **THEN** an outcome record exists naming that condition
- **AND** it is distinguishable from a refusal for an undeclared capability

#### Scenario: Abandonment at shutdown is recorded

- **WHEN** exchanges are still in flight when a component completes shutdown
- **THEN** each produces an outcome record naming abandonment at shutdown
- **AND** the count of such records equals the number that were in flight

#### Scenario: Two ending conditions still yield one record

- **WHEN** a client disconnects and the backend fails on the same exchange at the same moment
- **THEN** exactly one outcome record exists for that exchange
- **AND** it names one of the two conditions rather than both or neither

#### Scenario: A bidirectional stream session is recorded once

- **WHEN** a bidirectional stream is established, carries many frames over a long period, and is then closed
- **THEN** exactly one outcome record exists for that session
- **AND** its outcome names the cause that closed it
- **AND** no record is produced per frame

#### Scenario: A cross-instance exchange still produces exactly one outcome record

- **WHEN** an exchange is admitted at one instance and served over a tunnel held by another
- **THEN** exactly one outcome record exists for it across the installation
- **AND** the signals the other instance produced about it are joinable to that record by the correlation identifier
- **AND** those signals are not counted as outcomes

#### Scenario: Losing the instance holding the tunnel produces an outcome

- **WHEN** the instance holding the tunnel for an in-flight exchange becomes unreachable from the instance that admitted it
- **THEN** the exchange produces exactly one outcome record naming that condition
- **AND** it is distinguishable from a tunnel that failed while its instance was reachable
- **AND** it is distinguishable from cancellation by the client

### Requirement: Error paths produce structured records with a fixed minimum field set

Every path that ends an exchange other than successfully, and every failure of an internal or dependency operation, SHALL produce a record carrying at minimum: a stable event identifier, the identity of the instance that produced it, the correlation identifier for the exchange where one exists, the tenancy and mount concerned where they are known, an enumerated reason, and the outcome. Where a field is not applicable, its absence SHALL be explicit rather than represented by an empty or placeholder value.

Records SHALL be machine-parsable as structured fields without requiring a consumer to parse prose. A reason SHALL be an enumerated value; a record SHALL NOT convey a reason as a rendering of an internal host-language value. Where the condition is one the wire contract already enumerates, the record SHALL carry that contract code rather than a separately invented equivalent.

A value carried into a record from client-supplied input SHALL NOT be able to alter the record's structure, terminate it early, or cause an additional record to be produced.

#### Scenario: A failure record carries the minimum fields

- **WHEN** a sidecar cannot reach its backend and the exchange fails
- **THEN** a record exists carrying an event identifier, the identity of the instance that produced it, the correlation identifier, the tenancy, the mount, an enumerated reason, and the outcome

#### Scenario: Records are parsed as fields, not text

- **WHEN** a consumer reads the records produced by a run
- **THEN** each field is retrievable by name
- **AND** no field must be recovered by matching against a human-readable message

#### Scenario: Reasons are enumerated

- **WHEN** an internal operation fails with an unexpected condition
- **THEN** the record names an enumerated reason covering that category
- **AND** the record does not contain a rendering of an internal value as the reason

#### Scenario: No error path is silent

- **WHEN** each enumerated failure outcome is provoked in turn
- **THEN** each produces a record at a configured destination

#### Scenario: Client input cannot forge a record

- **WHEN** a client supplies a value containing the delimiters, escape sequences, and line breaks of the record format, and that value is carried into a record
- **THEN** it appears as a single field value of one record
- **AND** no additional record is produced
- **AND** no other field of that record is altered

#### Scenario: A failure on one instance is not read as a failure everywhere

- **WHEN** one instance of an installation begins failing an internal operation while the other instances do not
- **THEN** every record of that failure names the instance that produced it
- **AND** an operator can determine that the failures came from one instance rather than from the installation

### Requirement: Every signal identifies the instance that produced it

Every signal the system produces SHALL identify the component instance that produced it — every record, every measured value, every entry in the degraded-state inventory, every startup, drain, and operator-action record, and every value in a diagnostic response. For an instance of the proxy installation that identity is its instance identity, and no signal an instance produces is exempt from carrying it. The instance identity SHALL be drawn from a bounded set of stable identifiers, SHALL be the same identity for an instance before and after a restart, and SHALL NOT be an internal network address of that instance.

A sidecar and a component terminating client-facing protocols each identify their own deployed instance on the same terms. Neither is required to carry a proxy instance identity: their signals join the proxy's by the correlation identifier, and requiring them to know which instance held their tunnel would make the join depend on the topology rather than on the identifier.

For the error and outcome records above this identity is one of the minimum fields the fixed field set already requires; what this requirement adds is that no other class of signal is exempt from carrying it, and that an operator can therefore always tell a fault on one instance from the same fault everywhere.

A signal describing work that spanned more than one instance SHALL identify each instance's part: for an exchange, the instance that admitted it and the instance holding the tunnel it was dispatched to, and where the edge is a separate component, the terminating instance that held the client connection. Where a value is an aggregate over instances rather than one instance's own observation, it SHALL be identified as an aggregate rather than carrying a single instance's identity.

#### Scenario: No signal class is exempt

- **WHEN** each class of signal in the inventory is exercised on a named instance
- **THEN** the resulting record, measured value, inventory entry, or diagnostic value identifies that instance
- **AND** no class is produced without it

#### Scenario: A single-instance fault is distinguishable from an installation-wide one

- **WHEN** one instance cannot reach the credential store while the other instances can
- **THEN** the signals reporting the condition name the affected instance
- **AND** an operator can tell that apart from the same condition holding on every instance

#### Scenario: Instance identity survives a restart

- **WHEN** an instance is restarted with the same configuration
- **THEN** the signals it produces after the restart carry the identity they carried before it
- **AND** its measurements continue the series they were part of rather than beginning a new one

#### Scenario: Instance identity discloses no internal address

- **WHEN** a signal or a diagnostic response carrying an instance identity is read
- **THEN** the identity is not an internal network address of that instance
- **AND** it is not a form from which such an address can be recovered

#### Scenario: An exchange that crossed instances names both parts

- **WHEN** an exchange is admitted at one instance and dispatched to a tunnel held by another
- **THEN** its outcome record names both the admitting instance and the instance holding the tunnel
- **AND** where the two are the same instance, that is stated rather than left absent

### Requirement: An answer that spans the installation states which instances it covers

An operator's question is about the installation, not about the instance their query reached. Any answer required by this capability that draws on state held by more than one instance — a diagnostic response, an aggregate measurement, the degraded-state inventory, the installation's membership, the fleet's build provenance — SHALL state which instances contributed to it and SHALL name every instance that was expected to contribute and did not.

An answer missing a contribution SHALL be marked incomplete in a form a consumer can detect without prior knowledge of the installation's topology, SHALL NOT be returned in the same shape as a complete answer, and SHALL NOT be presented as the state of the installation. The distinction SHALL be as available to a machine reading the answer as to a person.

This obligation is referred to below as the coverage rule. Such an answer SHALL be produced within its configured bound whether or not every instance contributes: an unreachable instance SHALL make the answer incomplete rather than make it late, and SHALL never make it absent. A missing contribution SHALL be reported as unknown for the named instance, and SHALL NOT be reported as a zero, an empty set, or any negative finding about that instance's subjects.

#### Scenario: A complete answer says so

- **WHEN** an installation-wide answer is obtained while every instance is reachable
- **THEN** it states that every instance of the installation contributed
- **AND** it names no instance as missing

#### Scenario: A partial answer is detectably partial

- **WHEN** one instance cannot be reached and an installation-wide answer is obtained from another instance
- **THEN** the answer is marked incomplete
- **AND** it names the instance whose contribution is missing
- **AND** a consumer reading only the answer can determine that it does not cover the whole installation

#### Scenario: Missing is not zero

- **WHEN** the instance holding a mount's tunnels cannot be reached and an installation-wide answer about that mount is obtained
- **THEN** the answer does not report that mount as having no sidecar
- **AND** it reports the unreachable instance's contribution as unknown

#### Scenario: An unreachable instance does not delay the answer

- **WHEN** an instance stops responding to requests for its contribution
- **THEN** an installation-wide answer is still returned within its configured bound
- **AND** it is marked incomplete naming that instance

#### Scenario: A partial answer cannot be mistaken for a complete one

- **WHEN** an answer obtained during a partition is compared with an answer obtained while every instance was reachable
- **THEN** the two differ in a stated coverage field, not only in the subjects they enumerate
- **AND** the partial answer is not indistinguishable from a complete answer for a smaller installation

### Requirement: Every enumerated cause in the system maps to exactly one outcome value

Several capabilities each define their own enumerated vocabulary — the causes that end an exchange at the client edge, the reasons an edge rejection carries, the reasons a registry entry becomes ineligible, the codes and reasons a bidirectional stream is closed with, the error codes the wire contract conveys, and the reasons an authentication attempt fails. Left unrelated, the same real failure appears under a different name depending on which component observed it, and an operator cannot count it once.

The system SHALL maintain one published registry that maps every such enumerated value to exactly one outcome value in the enumeration this capability defines. Every value in every one of those vocabularies SHALL appear in the registry, no value SHALL map to two outcomes, and an outcome SHALL be reachable from at least one cause. A value present in such a vocabulary but absent from the registry SHALL be reported as a defect rather than recorded under a general outcome.

The registry covers the vocabularies that describe the fate of traffic. Two other kinds of vocabulary SHALL NOT be mapped into the outcome enumeration, because neither describes an exchange and forcing either into it would make an outcome count meaningless. The first is the enumerated refusal codes of control-plane operations — a rejected routing change, a rejected hostname claim, a failed certificate issuance, a refused migration, a refused use of custody-managed material. The second is the **connection-level** vocabularies: the causes a connection is refused at an accept path before any exchange exists, the phases a connection occupies while it is open, and the causes a connection ends in; a connection that never authenticates produces no exchange, so it has no outcome to map to.

Both kinds SHALL nevertheless be published, SHALL be bound by the stable-identifier obligation this capability places on every enumerated value, and SHALL be separately countable by cause. The registry SHALL state which vocabularies it covers and, for each it does not, which of the two unmapped kinds it belongs to, so that a vocabulary is never left uncovered by both rules and no capability is left to infer which rule applies to its own. Where one condition appears in both a connection-level vocabulary and a traffic vocabulary — a tunnel ending while exchanges were in flight — the connection-level value SHALL describe the connection and the mapped outcome SHALL describe each affected exchange, and the two SHALL NOT be conflated into one count.

Where one real failure is observed by more than one component — the proxy, the sidecar, and the registry each seeing the same tunnel loss — the records they produce SHALL carry the same outcome value for it, so the event counts once. Where a component observes a failure whose cause is not established, it SHALL record the outcome for an unattributed failure of that class rather than the nearest specific one.

A single failure observed by more than one instance SHALL be counted once in an installation aggregate. Where the instance that admitted an exchange and the instance holding its tunnel both produce signals for the same failure, both SHALL name the same outcome value, both SHALL be joinable by the correlation identifier, and the failure SHALL NOT be counted once per observing instance.

#### Scenario: Every vocabulary value is mapped

- **WHEN** the enumerated values defined by each capability are enumerated in turn
- **THEN** each appears exactly once in the published registry with the outcome value it maps to
- **AND** an unmapped value is reported as a defect

#### Scenario: A control-plane refusal code is published but not mapped to an outcome

- **WHEN** a control-plane operation is refused with its own enumerated code
- **THEN** that code is published and covered by the stable-identifier obligation
- **AND** it is not mapped into the outcome enumeration
- **AND** the registry states that its vocabulary is one it does not cover

#### Scenario: A connection refused before any exchange has no outcome value

- **WHEN** a connection is refused at an accept path before it authenticated, and separately a connection is held in each of its open phases
- **THEN** each cause and each phase is published, stable, and countable by cause
- **AND** none of them is mapped into the outcome enumeration
- **AND** the registry states that those vocabularies are connection-level ones it does not cover

#### Scenario: Every vocabulary falls under exactly one rule

- **WHEN** every enumerated vocabulary any capability defines is listed against the registry
- **THEN** each is either mapped to an outcome or stated to be a control-plane or a connection-level vocabulary
- **AND** none is covered by both rules and none by neither

#### Scenario: A connection ending and its exchanges are counted separately

- **WHEN** a tunnel ends while exchanges were in flight on it
- **THEN** the connection's ending carries its connection-level cause
- **AND** each affected exchange carries the mapped outcome for an exchange abandoned by the tunnel ending
- **AND** counting one does not count the other

#### Scenario: A cross-instance failure is counted once

- **WHEN** an exchange admitted at one instance fails on a tunnel held by another and both instances produce signals for it
- **THEN** the installation aggregate counts that failure once
- **AND** the signals the two instances produced name the same outcome value
- **AND** they are joinable by the correlation identifier

#### Scenario: One failure counts once across components

- **WHEN** a tunnel is lost while an exchange is in flight and the proxy, the registry, and the sidecar each record it
- **THEN** the records carry the same outcome value
- **AND** counting that outcome yields one occurrence for the exchange, not three

#### Scenario: An edge cause and a contract code do not diverge

- **WHEN** a request is refused for an undeclared capability
- **THEN** the cause the client's response carries, the reason recorded at the edge, and the contract code conveyed over the tunnel all map to the same outcome value

#### Scenario: An unattributed failure is not misattributed

- **WHEN** a component observes a failure whose specific cause it cannot establish
- **THEN** it records the outcome for an unattributed failure of that class
- **AND** it does not record the nearest specific outcome

### Requirement: Severity reflects required action, not internal surprise

The severity of a record SHALL describe whether an operator must act. A condition caused by a client or a tenant configuration and handled as designed — a malformed request, a refusal, a bounded resource rejection, a capability refusal — SHALL NOT be recorded at a severity that indicates operator action is required. A condition indicating that the component or a dependency is not functioning SHALL be. An instance losing contact with part of its own installation, and an instance serving routing decisions from installation-wide state it can no longer refresh, are conditions of that second kind and SHALL be recorded at a severity indicating operator action is required — the loss of one instance from an otherwise healthy installation no less than a loss that spans it, since an instance that has fallen out silently is exactly the fault an operator is not looking for.

Repeated occurrences of one condition SHALL NOT produce an unbounded volume of records: repeats SHALL be summarised, and the number suppressed SHALL be stated in the summary. Summarisation SHALL apply to diagnostic and error records only; it SHALL NOT be applied to the per-exchange outcome record and SHALL NOT reduce the accuracy of any measurement.

#### Scenario: Client-caused refusal is not an operator alert

- **WHEN** a client sends a malformed request that the edge rejects
- **THEN** a record is produced
- **AND** its severity does not indicate that operator action is required

#### Scenario: Dependency failure is an operator alert

- **WHEN** the durable store required to refresh routing state becomes unreachable
- **THEN** a record is produced at a severity indicating operator action is required

#### Scenario: Losing contact with an instance is an operator alert

- **WHEN** one instance of an otherwise healthy installation stops being reachable from the others
- **THEN** each instance that lost contact with it produces a record at a severity indicating operator action is required
- **AND** the record names the instance it lost contact with and the instance that produced it
- **AND** the severity is the same whether one instance or several became unreachable

#### Scenario: A flood is summarised

- **WHEN** one condition recurs many times in a short interval
- **THEN** the records produced for it are summarised
- **AND** the summary states how many occurrences were suppressed
- **AND** the count of occurrences remains accurate in the measurements
- **AND** the outcome record for each affected exchange is still produced individually

### Requirement: Secrets never appear in an emitted signal

No credential, token, key, signature, cookie value, authorization field value, or certificate private key SHALL appear in any record, measurement, label, diagnostic surface, or response body produced by the system. This SHALL hold for secrets carried inside a request target, including in a query component, and for secrets carried inside a field value.

Redaction SHALL be applied where signals are produced, such that a newly added call site cannot bypass it. A signal that cannot be produced without a secret SHALL NOT be produced.

#### Scenario: A credential in a request target is not recorded

- **WHEN** a component records or reports a target that carries a credential in its query component
- **THEN** the recorded target does not contain the credential value
- **AND** the presence of a redacted component is evident

#### Scenario: Authorization field values are absent

- **WHEN** an exchange carrying an authorization field fails and is recorded
- **THEN** no record, measurement, or diagnostic surface contains that field's value

#### Scenario: An error returned to a client carries no secret

- **WHEN** an edge-generated error response is returned for an exchange that carried credentials
- **THEN** the response body and its fields contain no credential value

#### Scenario: Sentinel secrets are absent from every signal

- **WHEN** the system is exercised across its signal-producing conditions with credentials set to distinctive sentinel values
- **THEN** no sentinel value appears in any record, measurement, label, or diagnostic response collected during the run

### Requirement: Tenant payload content is not carried in signals

Request and response body octets, bidirectional stream frame payloads, and datagram payloads SHALL NOT be emitted in any record, measurement, or diagnostic surface. Signals SHALL describe payloads by size, count, and state only.

Field values that may carry tenant or end-user data SHALL be emitted only where an operator has explicitly enabled it for a named subset, and enabling it SHALL be recorded.

#### Scenario: Body octets are never recorded

- **WHEN** an exchange carrying a body fails at any hop
- **THEN** the records produced describe the body by octet count and transfer state
- **AND** they contain none of the body's octets

#### Scenario: Frame payloads are never recorded

- **WHEN** a bidirectional stream is closed after an error
- **THEN** the records produced name the close code, the reason code, and frame counts
- **AND** they contain no frame payload octets

#### Scenario: Enabling field capture is deliberate and recorded

- **WHEN** an operator enables emission of a named set of field values
- **THEN** only fields in that named set are emitted
- **AND** the fact that capture is enabled, and for which fields, is itself observable

### Requirement: One correlation identifier spans the whole exchange

The proxy SHALL assign a correlation identifier to every exchange it admits, unique for the lifetime over which records are retained. The identifier SHALL be carried over the tunnel with the exchange, SHALL appear in every signal any component produces about that exchange, SHALL be available to the sidecar for propagation to the backend, and SHALL appear in any edge-generated error response returned to the client.

The correlation identifier SHALL be distinct from the stream identifier the tunnel assigns, so that it remains unique across tunnels, survives a reconnection, and can be quoted by a client after the exchange has ended.

The identifier SHALL be assigned once, by the instance that admits the exchange, and SHALL be unique across the installation rather than only within the instance that assigned it. Where the admitting instance and the instance holding the tunnel the exchange is dispatched to differ, the identifier SHALL be carried to that instance and SHALL appear unchanged in every signal it and the sidecar produce about the exchange.

Where the edge is a separate component, the instance that terminates the client connection is the instance that admits the exchange: it assigns the identifier under the same rule, and no proxy instance the exchange is dispatched to SHALL replace, re-derive, or supplement it with a second identifier of its own. Identifiers assigned concurrently at different terminating instances SHALL be distinct, including while a terminating instance cannot reach the rest of the installation. A request the terminating instance refuses before any proxy instance is involved SHALL be assigned one nonetheless, SHALL carry it in the response returned to the client, and its records SHALL be retrievable by it from any instance's diagnostic surface.

Following one exchange SHALL NOT require the operator to know that it crossed instances. Retrieving every record for an exchange by its identifier alone SHALL succeed from any instance's diagnostic surface, whichever instance admitted it and whichever instance held its tunnel, and SHALL NOT require the operator to name an instance, to know how many instances the installation has, or to repeat the query against each instance in turn. Which instances took part SHALL be visible in the records retrieved; it SHALL NOT be a precondition of retrieving them.

A correlation value supplied by a client SHALL NOT be adopted as the identifier. It MAY be recorded as a separate attribute after validation against a bounded format; a value failing that validation SHALL be dropped rather than recorded or truncated into a different value.

Where a connected sidecar produces no signals carrying the correlation identifier, the proxy SHALL still produce a complete set of records for the exchange and SHALL make the absence of the sidecar's half observable, rather than refusing the exchange.

#### Scenario: One identifier joins all three hops

- **WHEN** an exchange is served through the proxy, a sidecar, and a backend
- **THEN** the records produced by the proxy and by the sidecar for that exchange carry the same correlation identifier
- **AND** an operator can retrieve every record for the exchange by that identifier alone

#### Scenario: A failing exchange gives the client something to quote

- **WHEN** an edge-generated error response is returned
- **THEN** it carries the correlation identifier for that exchange
- **AND** presenting that identifier retrieves the records for that exchange

#### Scenario: A client cannot choose the identifier

- **WHEN** a client supplies a correlation value of its own
- **THEN** the assigned identifier is not the client-supplied value
- **AND** two exchanges supplying the same client value still receive distinct identifiers

#### Scenario: Concurrent exchanges on one tunnel are distinguishable

- **WHEN** many exchanges are in flight concurrently over a single tunnel
- **THEN** each has a distinct correlation identifier
- **AND** records for one exchange are retrievable without returning records for another

#### Scenario: An oversized client value is dropped, not truncated

- **WHEN** a client supplies a correlation value exceeding the bounded format
- **THEN** no attribute carrying that value or a truncation of it is recorded
- **AND** the assigned identifier is unaffected

#### Scenario: A sidecar that reports no correlation identifier

- **WHEN** a sidecar of an older build produces no signals carrying the correlation identifier
- **THEN** the exchange is served rather than refused
- **AND** the proxy's own records for it remain complete and retrievable by that identifier
- **AND** the absence of records from that sidecar for the exchange is itself observable

#### Scenario: One identifier joins the hops across two instances

- **WHEN** an exchange is admitted at one instance and dispatched to a tunnel held by another
- **THEN** the records produced by both instances and by the sidecar carry the same correlation identifier
- **AND** the operator retrieves all of them with that identifier alone

#### Scenario: Following an exchange does not require knowing it crossed instances

- **WHEN** an operator supplies a correlation identifier to an instance that neither admitted the exchange nor held its tunnel
- **THEN** the records for that exchange are returned
- **AND** the operator was not required to name an instance or to query instances one at a time
- **AND** the records state which instances took part

#### Scenario: The terminating component's identifier is not replaced downstream

- **WHEN** an exchange is admitted by a separate terminating instance and dispatched by a proxy instance
- **THEN** every signal either instance and the sidecar produce about it carries the identifier the terminating instance assigned
- **AND** no second identifier is assigned for the same exchange

#### Scenario: A request refused at the edge is still retrievable

- **WHEN** a separate terminating instance refuses a request before any proxy instance is involved
- **THEN** the response carries a correlation identifier
- **AND** presenting that identifier retrieves the records for that request from any instance's diagnostic surface

#### Scenario: Two instances do not assign the same identifier

- **WHEN** exchanges are admitted concurrently at every instance of an installation
- **THEN** no two exchanges share a correlation identifier
- **AND** this holds for exchanges admitted at different instances while those instances are partitioned from each other

#### Scenario: A retrieval that cannot cover every instance says so

- **WHEN** an operator supplies a correlation identifier and the instance holding that exchange's tunnel cannot be reached
- **THEN** whatever records are available are returned marked incomplete, naming the unreachable instance
- **AND** the answer does not report that no such exchange exists

### Requirement: Elapsed time is attributed to enumerated phases

The outcome record for an exchange SHALL attribute its elapsed time to an enumerated set of phases covering at minimum: edge admission, route selection, sidecar selection, dispatch to the instance holding the selected tunnel, transfer to the sidecar, time awaiting the backend's first response octet, body transfer, and delivery to the client. The attributed phases SHALL account for the exchange's total elapsed time.

An exchange that ends before reaching a phase SHALL report that phase as not entered rather than as zero elapsed.

Where the instance that admitted the exchange also holds the selected tunnel, the dispatch phase SHALL be reported as not entered rather than as zero elapsed, so that a slow hop between instances is never invisible and a same-instance exchange is never reported as having taken one.

#### Scenario: A slow backend is attributable

- **WHEN** a backend delays before emitting its response head and then responds quickly
- **THEN** the outcome record attributes the elapsed time to the phase awaiting the backend's first response octet
- **AND** it does not attribute that time to delivery to the client

#### Scenario: A slow client is attributable

- **WHEN** a client reads a large response slowly
- **THEN** the outcome record attributes the elapsed time to delivery to the client
- **AND** it does not attribute that time to the backend

#### Scenario: Phases account for the total

- **WHEN** an exchange completes
- **THEN** the sum of attributed phase durations accounts for the exchange's total elapsed time within a stated tolerance

#### Scenario: Unentered phases are distinguishable from instant ones

- **WHEN** an exchange is refused before a sidecar is selected
- **THEN** the phases after sidecar selection are reported as not entered
- **AND** they are not reported as having elapsed no time

#### Scenario: A slow hop between instances is attributable

- **WHEN** an exchange is admitted at one instance and dispatched to a tunnel held by another instance that is slow to accept it
- **THEN** the outcome record attributes the elapsed time to the phase for dispatch to the instance holding the tunnel
- **AND** it does not attribute that time to sidecar selection or to awaiting the backend's first response octet

#### Scenario: A same-instance exchange enters no dispatch phase

- **WHEN** an exchange is admitted at the instance that holds the selected tunnel
- **THEN** the dispatch phase is reported as not entered
- **AND** it is not reported as having elapsed no time
- **AND** the attributed phases still account for the exchange's total elapsed time

### Requirement: The measurable quantities are enumerated

The system SHALL make the following measurable, attributable to a tenancy and to a mount: the count of exchanges by outcome; the distribution of exchange latency in a form from which tail quantiles can be derived; the count of exchanges and of streams currently in flight; the octets currently buffered awaiting transfer; the count of connected tunnels and the age of each; the outcomes of credential authentication attempts by result; the freshness of each projection that serves a routing decision; the count of rejections attributable to each configured bound; the count of requests refused for an undeclared capability, attributable to the capability named; the distribution of negotiated contract versions across connected tunnels; the number of instances the reporting instance currently counts as part of the installation and the number of those it cannot reach; the age of the installation-wide state the reporting instance is serving routing decisions from; and the count of exchanges dispatched to a tunnel held by another instance, by result.

The count of refusals for an undeclared capability and the distribution of negotiated contract versions exist because the operator cannot upgrade the sidecar fleet: the cost of the version spread SHALL be quantifiable from the operator's own signals, without contacting a tenant.

A measurement of latency SHALL NOT be exposed only as an average or a total. Counts that represent work currently in progress SHALL return to their resting value when that work has finished.

Every quantity in that enumeration SHALL be available both as the value one instance observes and as an aggregate over the installation, and any exposed value SHALL state unambiguously which of the two it is. A per-instance value SHALL NOT be exposed in a form that can be read as an installation total, and an aggregate SHALL NOT be exposed in a form that hides which instances it covers: an aggregate SHALL obey the coverage rule stated above. Reading a per-instance value as an installation total is a silent measurement error, and reading an aggregate as a per-instance value hides a single bad instance; the exposed form SHALL make both mistakes impossible rather than merely documented.

Quantities that are properties of one instance — the state it has not been able to refresh, the peers it cannot reach, its own in-flight counts — SHALL remain retrievable per instance while an aggregate is also available, so that one bad instance is not averaged away.

Aggregating a measurement across instances is a property of what an operator can read, not of how a bound is enforced. Where a bound is deliberately accounted per accepting instance rather than installation-wide — as `tunnel/listener` requires of the pre-authentication connection bound, for the reason stated there — its measurements SHALL be exposed per instance, and any aggregate over them SHALL be labelled a sum of per-instance observations rather than the utilisation of an installation-wide ceiling. No obligation in this capability SHALL require an instance to consult another instance in order to admit or refuse a connection or to produce a measurement of its own.

#### Scenario: Tail latency is derivable

- **WHEN** an operator asks for the latency of exchanges on a mount above a high quantile
- **THEN** the answer is derivable from the exposed measurements
- **AND** it is not approximated from an average

#### Scenario: Outcomes are attributable to a mount

- **WHEN** two mounts serve traffic with different outcomes
- **THEN** the counts by outcome are separately retrievable for each mount
- **AND** each is attributable to its tenancy

#### Scenario: In-flight counts return to rest

- **WHEN** a period of load ends and every exchange has produced an outcome record
- **THEN** the in-flight exchange count, the in-flight stream count, and the buffered-octet measurement return to the values they held before the load began

#### Scenario: Authentication outcomes are separable

- **WHEN** sidecars attempt to establish tunnels with valid, expired, revoked, and unknown credentials
- **THEN** the counts of each outcome are separately retrievable
- **AND** an expired credential is distinguishable from a revoked one in the measurements

#### Scenario: The cost of the old sidecar fleet is quantifiable

- **WHEN** a mount is served by sidecars of differing contract versions and some requests are refused for capabilities the selected sidecar has not declared
- **THEN** the count of those refusals is retrievable per missing capability name
- **AND** the distribution of negotiated contract versions across connected tunnels is retrievable
- **AND** both are obtainable from the operator's own signals without contacting a tenant

#### Scenario: A per-instance value is not readable as an installation total

- **WHEN** an operator reads a measured quantity from one instance of a multi-instance installation
- **THEN** the value states that it is that instance's own observation
- **AND** the installation aggregate for the same quantity is separately obtainable and states that it is an aggregate
- **AND** neither can be read as the other

#### Scenario: One bad instance is visible behind a healthy aggregate

- **WHEN** one instance is refusing exchanges while the other instances serve normally
- **THEN** the per-instance values expose the refusals on that instance
- **AND** the aggregate does not make them indistinguishable from a low installation-wide rate

#### Scenario: An aggregate names what it covers

- **WHEN** an installation aggregate is read while one instance is unreachable
- **THEN** the value is marked incomplete naming that instance
- **AND** it is not presented as the installation total

#### Scenario: Unrefreshed installation-wide state is measurable

- **WHEN** an instance has been unable to refresh the installation-wide state its routing decisions draw on
- **THEN** the age of the state it is serving from is retrievable as that instance's own value
- **AND** the number of instances it cannot reach is retrievable
- **AND** both are attributed to that instance rather than to the installation

#### Scenario: An aggregate does not turn a per-instance bound into an installation-wide one

- **WHEN** the pre-authentication connection bound is reached on one instance and an operator reads both the per-instance value and the installation aggregate
- **THEN** the per-instance value shows that instance at its own ceiling
- **AND** the aggregate is labelled a sum of per-instance observations rather than the utilisation of an installation-wide ceiling
- **AND** each instance continues to admit and refuse connections while every other instance is unreachable

### Requirement: Measurement labels are bounded in cardinality

Every label attached to a measurement SHALL draw its values from a bounded set. A value derived from request content — a request target, a query component, a field value, a client-supplied identifier, a hostname with no verified claim, or a free-text reason — SHALL NOT be used as a label value.

Values that do not correspond to a registered entity SHALL be collapsed into a single reserved value. The system SHALL enforce a configured ceiling on distinct label combinations; reaching the ceiling SHALL be recorded and SHALL cause further combinations to be collapsed rather than admitted.

Instance identity is one such bounded label. The set of instance identities SHALL be bounded by the instances configured for the installation, and an instance identity SHALL NOT be derived from a value a client, a sidecar, or a peer instance can choose. Attaching instance identity SHALL NOT cause the number of distinct label combinations to grow without bound as instances restart, are replaced, or are added and removed over time: the series an instance held SHALL be retired within a configured period after that instance leaves the installation, and an instance that rejoins SHALL resume its own series rather than create a further one. The configured ceiling and every other obligation of this requirement continue to hold with instance identity among the labels.

#### Scenario: Request paths do not create series

- **WHEN** a client issues many requests with distinct paths under one mount
- **THEN** the number of distinct label combinations does not grow with the number of distinct paths
- **AND** measurements remain attributed to the mount

#### Scenario: Unmatched input collapses to one value

- **WHEN** requests arrive for hostnames with no verified claim
- **THEN** they are counted under a single reserved label value
- **AND** no label value derived from the requested hostname is created

#### Scenario: The ceiling is enforced and recorded

- **WHEN** the number of distinct label combinations reaches the configured ceiling
- **THEN** further combinations are collapsed into the reserved value
- **AND** the condition is recorded and observable
- **AND** the memory held for measurements remains bounded

#### Scenario: One tenant cannot grow another's cost

- **WHEN** one tenancy drives label combinations to the ceiling
- **THEN** measurements for other tenancies remain attributable and correct

#### Scenario: Instance churn does not grow series without bound

- **WHEN** instances are repeatedly replaced over a long period, each new instance taking the place of one that left
- **THEN** the number of distinct label combinations does not grow with the number of replacements
- **AND** the series held by instances that have left are retired within the configured period
- **AND** an instance that rejoins resumes its own series

#### Scenario: The ceiling holds with instance identity included

- **WHEN** the number of distinct label combinations, counting instance identity among the labels, reaches the configured ceiling
- **THEN** further combinations are collapsed into the reserved value
- **AND** the condition is recorded and observable
- **AND** the memory held for measurements remains bounded on every instance

#### Scenario: A peer cannot choose an instance identity

- **WHEN** a connecting sidecar or a peer instance supplies a value purporting to be an instance identity
- **THEN** no label value is created from it
- **AND** the identity attached to that instance's measurements is the one it was configured with

### Requirement: Liveness answers only whether a restart would help

The liveness signal SHALL report failure only when the component cannot recover by continuing to run and a restart is the appropriate remedy. It SHALL NOT report failure because a dependency is unavailable, because a projection is stale, because no sidecar is connected, or because the component is draining. It SHALL NOT report failure because another instance of the installation is unreachable, because installation-wide state has not converged, or because the instance is partitioned from the rest of the installation: a partition SHALL NOT be able to make an installation restart itself.

The liveness signal SHALL be answerable while the component is saturated with traffic, and SHALL NOT depend on the availability of any subsystem serving tenant traffic.

#### Scenario: A dependency outage does not restart the process

- **WHEN** the durable store is unreachable
- **THEN** the liveness signal continues to report success
- **AND** the readiness signal reports failure

#### Scenario: Unrecoverable internal state fails liveness

- **WHEN** a component reaches a state in which it can no longer accept or process work and cannot recover
- **THEN** the liveness signal reports failure

#### Scenario: Liveness answers under saturation

- **WHEN** the component is saturated with in-flight exchanges
- **THEN** the liveness signal is answered within its configured bound

#### Scenario: A partition does not restart the installation

- **WHEN** an instance is partitioned from every other instance of the installation
- **THEN** its liveness signal continues to report success
- **AND** its readiness signal reports failure
- **AND** the instances on the other side of the partition also continue to report liveness success

### Requirement: Readiness reflects dependency state and drain

The readiness signal SHALL be distinct from the liveness signal and SHALL report whether the component should currently receive new traffic. It SHALL be derived from the actual state of the dependencies required to serve, and SHALL NOT be a constant. Every separately deployed component in the enumeration `operability/packaging` owns SHALL answer it, and the minimum dependencies it is derived from SHALL be stated for each: for the proxy, the ability to serve routing decisions from a projection within its freshness bound and the ability to accept new exchanges; for a sidecar, an established tunnel and a reachable backend; for a component that terminates client-facing protocols, an established contract connection to at least one instance of the component holding the origin-facing tunnel and the ability to accept new client connections. Because the terminating component is an independently scaled tier as `proxy/edge-hygiene` states, losing the connection to one such instance while another it can reach is able to serve SHALL NOT withdraw its readiness; holding no such connection at all SHALL. A component whose readiness is not derived from the state of any dependency SHALL be reported as not satisfying this requirement.

Readiness SHALL report failure for the whole period a component is draining, beginning before it stops accepting new exchanges. Readiness SHALL return to success without a restart once the conditions that withdrew it are satisfied.

Readiness is answered per instance and SHALL describe only the instance answering it. An instance SHALL NOT report ready on the ground that another instance is ready, and SHALL NOT withhold readiness on the ground that another instance is not; no instance's readiness answer SHALL be derived from another instance's. The readiness of the installation as a whole is not this signal, and the state of the other instances is obtained through the installation's membership instead.

For a proxy instance, the installation-wide state it needs in order to select tunnels held by other instances is one of the dependencies its readiness is derived from. An instance that cannot obtain that state within its configured freshness bound SHALL report not ready; it SHALL continue to report live, SHALL continue to serve exchanges already in flight, and SHALL continue to serve what it can still serve from what it can reach rather than failing those exchanges on account of its readiness state. Readiness SHALL return to success within a bounded time once that state is again within its freshness bound, without a restart and without operator action.

#### Scenario: Readiness and liveness disagree

- **WHEN** a required dependency is unavailable
- **THEN** at that same instant the readiness signal reports failure and the liveness signal reports success

#### Scenario: Drain withdraws readiness first

- **WHEN** a drain begins
- **THEN** the readiness signal reports failure
- **AND** it does so before the component stops accepting new exchanges
- **AND** in-flight exchanges continue to be served

#### Scenario: Readiness recovers without a restart

- **WHEN** the condition that withdrew readiness is resolved
- **THEN** the readiness signal reports success again
- **AND** no restart was required

#### Scenario: Readiness is not a constant

- **WHEN** the component is deliberately placed in a state in which it cannot serve
- **THEN** the readiness signal reports failure
- **AND** the same signal reports success again once the component is returned to a serving state

#### Scenario: A sidecar without a tunnel is not ready

- **WHEN** a sidecar is running but has no established tunnel
- **THEN** its readiness signal reports failure
- **AND** its liveness signal reports success

#### Scenario: A terminator without its counterpart is not ready

- **WHEN** a component that terminates client-facing protocols is running but holds no established contract connection to any instance of the component holding the origin-facing tunnel
- **THEN** its readiness signal reports failure
- **AND** its liveness signal reports success
- **AND** requests in the protocols it terminates are refused rather than served by a path that omits the edge obligations

#### Scenario: Readiness is not satisfied by another instance being ready

- **WHEN** one instance of an installation cannot accept new exchanges while the others can
- **THEN** that instance's readiness signal reports failure
- **AND** the other instances' readiness signals continue to report success
- **AND** no instance's readiness answer reflects another instance's state

#### Scenario: An instance cut off from installation-wide state is not ready

- **WHEN** a proxy instance cannot obtain the state it needs to select tunnels held by other instances for longer than its configured freshness bound
- **THEN** its readiness signal reports failure
- **AND** its liveness signal reports success
- **AND** exchanges already in flight on it continue to be served
- **AND** exchanges it can still serve from what it can reach are not failed on account of the readiness state

#### Scenario: Readiness recovers when a partition heals

- **WHEN** the partition that withdrew an instance's readiness heals
- **THEN** that instance's readiness signal reports success again within a bounded time
- **AND** no restart and no operator action were required

### Requirement: The installation's membership and each instance's state are visible from any instance

An operator SHALL be able to obtain, from any instance's operational surface, the instances the installation currently comprises and, for each: its build provenance, its readiness as last observed, how long ago it was last reachable from the answering instance, and whether it is draining or withdrawing. The answer SHALL identify the instance that answered and SHALL obey the coverage rule stated above.

An instance that was part of the installation and has fallen out SHALL be reported as such together with the time it was last reachable, rather than disappearing from the answer with no trace. An instance deliberately withdrawn SHALL be distinguishable from one that stopped being reachable without a withdrawal, and both SHALL be distinguishable from an instance that was never part of the installation.

This answer SHALL require authorization. No surface answered without authorization SHALL disclose the number or the identity of the instances, and no part of this answer SHALL disclose an internal network address, a tenancy, or a mount.

#### Scenario: Membership is answerable from any instance

- **WHEN** an operator queries any instance of a multi-instance installation
- **THEN** the instances the installation comprises are reported, each with its readiness as last observed and its build provenance
- **AND** the answer identifies the instance that answered

#### Scenario: An instance that fell out is reported, not forgotten

- **WHEN** an instance stops being reachable without having been withdrawn
- **THEN** the answer reports it together with the time it was last reachable
- **AND** it is distinguishable from an instance that was deliberately withdrawn
- **AND** it is distinguishable from an instance that was never part of the installation

#### Scenario: Disagreement between instances is visible

- **WHEN** two instances are both reachable from an operator but not from each other
- **THEN** the answer each gives names the instance it cannot reach
- **AND** neither answer claims to cover the whole installation

#### Scenario: Membership is not available without authorization

- **WHEN** an unauthenticated request is made for the installation's membership
- **THEN** it is refused
- **AND** no surface answered without authorization discloses the number or the identity of the instances

#### Scenario: Membership discloses no addresses

- **WHEN** an authorized membership answer is read
- **THEN** it carries instance identities and instance state only
- **AND** it discloses no internal network address, tenancy, or mount

### Requirement: Operational surfaces are separated from tenant traffic and disclose nothing sensitive

Probe and diagnostic surfaces SHALL be reachable independently of the surfaces that serve tenant traffic, and SHALL NOT be reachable through any mount. Where such a surface is exposed on a hostname that also serves tenant traffic, its path SHALL be contributed to the single reserved-path enumeration the mount-point capability owns rather than protected by a check of this capability's own, so that no mount can occupy, shadow, or intercept it.

A probe response SHALL contain state only, and SHALL NOT disclose tenant identities, mount names, counts of tenants or mounts, credential state, or internal addresses. A diagnostic surface carrying tenant-attributable detail SHALL require authorization and SHALL be scoped to what the requesting principal is entitled to see.

Where answering a diagnostic draws on state held by another instance, the entitlement of the requesting principal SHALL be applied to every part of the answer whichever instance contributed it: a principal SHALL NOT obtain through an installation-wide answer any detail they would be refused on the instance that holds it. A probe answered without authorization SHALL disclose nothing about the installation's shape, and any enumerated reason it carries SHALL name no instance other than the one answering.

#### Scenario: A probe discloses no tenant information

- **WHEN** an unauthenticated probe is answered
- **THEN** its response states only readiness or liveness and, at most, an enumerated reason
- **AND** it names no tenancy, mount, or hostname

#### Scenario: A mount cannot shadow a probe

- **WHEN** a tenant registers a mount whose path would collide with an operational surface
- **THEN** the operational surface continues to be answered by the component
- **AND** requests to it are not forwarded to any sidecar

#### Scenario: Detailed diagnostics require authorization

- **WHEN** an unauthorized request is made for a diagnostic surface carrying tenant-attributable detail
- **THEN** it is refused
- **AND** the refusal for a tenancy or mount that exists is indistinguishable from the refusal for one that does not

#### Scenario: A diagnostic is scoped to the requesting principal

- **WHEN** a principal entitled to one tenancy requests diagnostics for a mount belonging to another
- **THEN** no detail of the other tenancy's mounts, sidecars, or exchanges is returned
- **AND** the response is indistinguishable from the response for a mount that does not exist

#### Scenario: Entitlement is applied to every instance's contribution

- **WHEN** a principal entitled to one tenancy obtains an installation-wide diagnostic while another tenancy's exchanges are in flight on a different instance
- **THEN** no detail of the other tenancy's mounts, sidecars, or exchanges is returned from any instance
- **AND** the answer is indistinguishable from the answer given when that other tenancy has no traffic

#### Scenario: A probe discloses nothing about the installation's shape

- **WHEN** an unauthenticated probe is answered
- **THEN** it discloses neither the number of instances in the installation nor any instance's address
- **AND** any enumerated reason it carries names no instance other than the one answering

### Requirement: A stuck exchange can be diagnosed from one place while it is stuck

For any mount, an operator SHALL be able to obtain, from the product's own operational surface and without shell access, a code change, or a restart: whether any sidecar is currently serving that mount and for how long each has been connected, the exchanges currently in flight on each, the age of the oldest in-flight exchange, and, for each in-flight exchange, the phase it is currently in and the condition it is waiting on.

This answer is for the installation, not for the instance that received the query. The operator SHALL obtain it from any instance's operational surface, whichever instance holds the mount's tunnels and whichever instance admitted each in-flight exchange, without knowing the installation's topology, without naming an instance, and without repeating the query against each instance in turn. Every reported sidecar SHALL identify the instance holding its tunnel, and every reported in-flight exchange SHALL identify both that instance and the instance that admitted it.

The answer SHALL obey the coverage rule stated above: it SHALL name the instances that contributed and every instance that did not, and an answer missing an instance's contribution SHALL be marked incomplete rather than returned as the state of the installation. A mount whose tunnels are held by an instance that could not be reached SHALL NOT be reported as having no sidecar. Three conditions SHALL be distinguishable from one another: a mount with no sidecar anywhere in the installation, a mount whose sidecars are connected but stalled, and a mount whose sidecars are held by an instance the answering instance cannot reach. That the registry itself converges once the partition heals is `tunnel/sidecar-registry`'s obligation and is taken as given; what is required here is that while it has not, the operator can see exactly which part of the installation the answer is missing.

The waiting condition SHALL be drawn from a stable enumerated set that distinguishes at minimum: awaiting sidecar selection, awaiting flow-control credit, awaiting the backend's first response octet, transferring a body, and awaiting the client to consume. For each in-flight exchange the operator SHALL also be able to obtain its correlation identifier, its octets transferred in each direction, and its octets currently buffered.

This diagnostic SHALL remain answerable while every exchange on the mount is blocked, and answering it SHALL NOT require the cooperation of the sidecar, the backend, any blocked exchange, or every instance being reachable.

The response SHALL be bounded: where the number of in-flight exchanges exceeds a configured bound, the response SHALL carry a subset ordered oldest first together with the total count, rather than an enumeration that grows with the number in flight. That bound SHALL apply to the installation-wide response as a whole rather than once per instance, the subset SHALL be ordered oldest first across every contributing instance, and the stated total SHALL be the installation total — marked incomplete where an instance did not contribute. The response size SHALL NOT grow with the number of instances. The work each instance performs to contribute SHALL be bounded, so that repeated installation-wide queries cannot themselves degrade serving.

#### Scenario: The oldest stuck exchange is identified

- **WHEN** an operator inspects a mount whose exchanges are not completing
- **THEN** the oldest in-flight exchange is reported with its age, its correlation identifier, and its current phase
- **AND** the sidecar serving it is identified
- **AND** the instance holding that sidecar's tunnel and the instance that admitted the exchange are identified

#### Scenario: Waiting conditions are distinguishable

- **WHEN** one exchange is blocked awaiting flow-control credit and another is blocked awaiting the backend's first response octet
- **THEN** the two are reported with different enumerated waiting conditions

#### Scenario: No sidecar is distinguishable from a stalled sidecar

- **WHEN** a mount has no sidecar serving it
- **THEN** the diagnostic reports that condition explicitly
- **AND** it is distinguishable from a mount with a connected sidecar whose exchanges are stalled
- **AND** it is distinguishable from a mount whose sidecars are held by an instance the answering instance cannot reach

#### Scenario: The diagnostic answers while the mount is blocked

- **WHEN** every exchange on a mount is blocked and no exchange is progressing
- **THEN** the diagnostic is still answered within its configured bound
- **AND** the answer reflects the blocked state rather than timing out

#### Scenario: One exchange is retrievable by its correlation identifier

- **WHEN** an operator supplies the correlation identifier a client reported
- **THEN** that exchange's mount, serving sidecar, phase, waiting condition, age, and transferred octets are returned
- **AND** the answer is the same whichever instance the operator supplied it to

#### Scenario: The diagnostic is bounded on a busy mount

- **WHEN** a mount has more exchanges in flight than the configured response bound
- **THEN** the response enumerates at most that bound, oldest first
- **AND** it states the total number in flight
- **AND** the size of the response does not grow with the number in flight

#### Scenario: An unresponsive sidecar does not block the diagnostic

- **WHEN** a sidecar has stopped responding on an established tunnel
- **THEN** the diagnostic for its mount is still answered within its configured bound
- **AND** it reports the sidecar as unresponsive rather than omitting it

#### Scenario: The answer covers the installation whichever instance is asked

- **WHEN** a mount's only sidecar holds its tunnel to one instance
- **AND** an operator asks a different instance about that mount
- **THEN** the sidecar is reported as connected, with how long it has been connected, its in-flight exchanges, and the instance holding its tunnel
- **AND** the operator neither named an instance nor queried the instances one at a time

#### Scenario: An exchange admitted elsewhere is reported with the tunnel it is stuck on

- **WHEN** an exchange admitted at one instance is stuck on a tunnel held by another
- **THEN** the diagnostic reports it with its age, its current phase, its waiting condition, its correlation identifier, the instance that admitted it, and the instance holding the tunnel
- **AND** it is reported whichever of the two instances the operator asked

#### Scenario: An unreachable instance is not reported as an empty mount

- **WHEN** the instance holding a mount's only tunnel cannot be reached from the instance answering the query
- **THEN** the answer is marked incomplete, naming that instance
- **AND** it does not report the mount as having no sidecar
- **AND** the operator can tell that the missing part of the answer is the part that would have held the mount's tunnels

#### Scenario: The installation-wide response is bounded once

- **WHEN** the exchanges in flight for one mount across every instance exceed the configured response bound
- **THEN** the response enumerates at most that bound, ordered oldest first across every contributing instance
- **AND** it states the installation total in flight
- **AND** the size of the response grows neither with the number in flight nor with the number of instances

#### Scenario: Repeated installation-wide queries do not degrade serving

- **WHEN** an installation-wide diagnostic is requested repeatedly at a high rate
- **THEN** the latency and the outcomes of exchanges served during that period are unchanged
- **AND** the work each instance performs to contribute remains within its configured bound

### Requirement: An operator can act on a stuck exchange or tunnel

An operator SHALL be able to terminate a single in-flight exchange, and separately to drain or disconnect a single sidecar tunnel, from the product's own operational surface. Terminating an exchange SHALL end it with an outcome distinguishable from every other outcome, SHALL release the resources it held, and SHALL NOT affect other exchanges.

Every such action SHALL be attributable to the operator who performed it and SHALL produce a record naming the action, its subject, and its result. An action SHALL be refused when the requesting principal is not entitled to its subject, and a refused attempt SHALL be recorded with the same attribution as a performed one.

An action naming an exchange or a tunnel that has already ended SHALL report that as its result without altering the record the subject already produced and without affecting any other exchange.

An action SHALL take effect whichever instance of the installation the operator directs it to: an exchange in flight on a tunnel held by another instance, and a tunnel held by another instance, SHALL be terminable or drainable through any instance's surface, without the operator establishing which instance holds the subject. Where the instance holding the subject cannot be reached, the action SHALL be reported as not performed, naming that instance; it SHALL NOT be reported as performed, SHALL NOT be reported as naming a subject that does not exist, and SHALL NOT be left in a state in which the operator cannot tell whether it took effect. The record of every action SHALL name the instance that received it and the instance holding its subject.

#### Scenario: One exchange is terminated

- **WHEN** an operator terminates a single in-flight exchange
- **THEN** that exchange ends with an outcome naming operator termination
- **AND** its client and its backend observe a defined error rather than continuing to wait
- **AND** other in-flight exchanges on the same tunnel continue

#### Scenario: Resources are released on termination

- **WHEN** an operator terminates an in-flight exchange
- **THEN** the in-flight count and buffered octets attributed to it return to their resting values

#### Scenario: An operator action is attributable

- **WHEN** an operator drains a sidecar tunnel
- **THEN** a record exists naming the acting operator, the action, the tunnel, and the result

#### Scenario: Terminating an exchange that has already ended

- **WHEN** an operator terminates an exchange that has already produced an outcome record
- **THEN** the action reports that the exchange had already ended
- **AND** the existing outcome record is unchanged
- **AND** no second outcome record is produced for it

#### Scenario: An unentitled principal cannot act

- **WHEN** a principal not entitled to a tenancy attempts to terminate one of its exchanges
- **THEN** the action is refused
- **AND** the exchange continues to be served
- **AND** the refused attempt is recorded with the principal that attempted it

#### Scenario: An exchange on another instance is terminated through any instance

- **WHEN** an operator terminates an exchange whose tunnel is held by an instance other than the one receiving the action
- **THEN** that exchange ends with an outcome naming operator termination
- **AND** the operator did not establish which instance held it
- **AND** other in-flight exchanges on that tunnel continue

#### Scenario: An action against an unreachable instance is not reported as done

- **WHEN** an operator directs an action at a subject held by an instance that cannot be reached
- **THEN** the action is reported as not performed, naming that instance
- **AND** it is not reported as performed
- **AND** it is not reported as naming a subject that does not exist

#### Scenario: An action record names both instances

- **WHEN** an operator drains a sidecar tunnel held by an instance other than the one receiving the action
- **THEN** a record exists naming the acting operator, the action, the tunnel, the result, the instance that received the action, and the instance holding the tunnel

### Requirement: Configuration is validated in one pass before anything accepts a connection

Several capabilities require the component to refuse to start on a bad or missing configuration value. Those checks SHALL be one validation pass, performed before any listener, tunnel endpoint, or probe surface accepts a connection, and a single refusal SHALL name every failing item across every capability together with what was wrong with each. A component SHALL NOT refuse on the first failing item and leave the operator to discover the next by restarting.

Every value the component's behaviour depends on SHALL be explicitly configured. A missing value SHALL be a validation failure; it SHALL NOT be filled in with an implicit default, and no capability SHALL exempt a value of its own from this. Where a value has a defensible default, that default SHALL be supplied by the configuration the component ships with rather than by the code that reads it, so that what is in force is always readable from the configuration.

The validation SHALL report, and the component SHALL record at startup, the complete set of configured values in force with any secret redacted, so that an operator can tell what the running component is actually using.

This requirement owns the pass the running component performs and what it records. What the artifact declares about its own configuration, that the declaration and the shipped example are generated from the same schema this pass reads, and that the schema is retrievable from the artifact while stopped, are `operability/packaging`'s obligations and are not restated here; the schema this pass validates against SHALL be that same schema, so that a value the artifact ships and a value this pass demands cannot disagree.

#### Scenario: Every failing item is named in one refusal

- **WHEN** a component is started with several required configuration items missing, invalid, or out of range across different capabilities
- **THEN** it refuses to start
- **AND** the refusal names every failing item and what was wrong with each
- **AND** a subsequent start with one of them corrected names the ones still outstanding

#### Scenario: Refusal precedes accepting anything

- **WHEN** a component refuses to start on configuration validation
- **THEN** no listener, tunnel endpoint, or probe surface accepted a connection at any point
- **AND** no signal destination received traffic-derived records

#### Scenario: A missing value is a failure, not a default

- **WHEN** a component is started with a required value absent
- **THEN** it refuses to start naming that value
- **AND** it does not start with an implicit value substituted for it

#### Scenario: The configuration in force is recorded

- **WHEN** a component starts successfully
- **THEN** it records the complete set of configured values in force
- **AND** every secret among them is redacted
- **AND** the recorded set matches the values the component actually applies

### Requirement: Every component reports its build provenance

Every component SHALL report an identifier of the exact build it is running — at minimum a version, the source revision it was built from, and whether the source tree was modified — both in a record produced at startup and on demand from its operational surface. This SHALL apply to every separately deployed component in the enumeration `operability/packaging` owns, which includes the proxy, the sidecar, and the component that terminates client-facing protocols, and SHALL NOT be stated of only some of them.

This requirement owns what a running component reports. That the value it reports was fixed when its artifact was produced, that no configuration item, environment property or peer value can restate it, and that it is also retrievable from the stopped artifact, are `operability/packaging`'s obligations and are not restated here.

A sidecar SHALL report its build provenance when establishing a tunnel, and the proxy SHALL make the provenance of every connected sidecar observable per mount. A build whose provenance is unknown SHALL report it as unknown explicitly, rather than reporting a value that resembles a version.

An operator SHALL be able to obtain the build provenance of every instance of the installation from any instance, so that a period in which more than one build is serving at once is visible rather than inferred. That answer SHALL obey the coverage rule stated above, and an instance whose provenance could not be obtained SHALL be named rather than omitted.

A sidecar that reports no provenance at all SHALL NOT be refused a tunnel on that ground; the proxy SHALL record its provenance as unreported and SHALL keep that distinguishable from a provenance the sidecar itself reported as unknown.

#### Scenario: Startup states the build

- **WHEN** a component starts
- **THEN** it produces a record naming its version, its source revision, and whether its source tree was modified

#### Scenario: No deployable is exempt from reporting it

- **WHEN** each separately deployed component of an installation is started in turn, including the component that terminates client-facing protocols
- **THEN** each produces the startup record and answers on demand
- **AND** a component that does neither is reported as not satisfying this requirement rather than as one to which it does not apply

#### Scenario: Build identity is retrievable at runtime

- **WHEN** an operator queries a running component
- **THEN** the same build identity reported at startup is returned

#### Scenario: The sidecar fleet's versions are visible to the operator

- **WHEN** several sidecars built from different revisions are connected
- **THEN** an operator can retrieve, per mount, the build provenance each connected sidecar reported
- **AND** the spread of versions serving one mount is observable without contacting the tenant

#### Scenario: Unknown provenance is explicit

- **WHEN** a component is built without provenance information
- **THEN** it reports its provenance as unknown
- **AND** it does not report a placeholder that could be mistaken for a released version

#### Scenario: A sidecar reporting no provenance is still served

- **WHEN** a sidecar of a build predating provenance reporting establishes a tunnel
- **THEN** the tunnel is established and its mount continues to be served
- **AND** the proxy records that sidecar's provenance as unreported
- **AND** that is distinguishable from a sidecar that reported its own provenance as unknown

#### Scenario: More than one build serving at once is visible

- **WHEN** some instances of an installation have been upgraded and others have not
- **THEN** an operator querying any instance obtains the build provenance of every instance
- **AND** the answer makes it apparent that more than one build is serving
- **AND** an instance whose provenance could not be obtained is named rather than omitted

### Requirement: Degraded operation is announced for as long as it persists

The system SHALL maintain an enumerable inventory of the conditions under which it is operating in a degraded state — at minimum: serving from a projection it cannot refresh, a durable store it cannot reach, a credential store it cannot reach, a certificate it cannot renew, a signal destination it cannot deliver to, an instance of the installation it cannot reach, and installation-wide state it has not been able to refresh within its freshness bound. Each entry SHALL state the condition, the time it began, and its effect on serving.

A degraded condition SHALL be observable continuously for as long as it holds, not only as a record at the moment of transition. Recovery SHALL clear the entry and SHALL itself be recorded.

Each entry SHALL state whether the condition is local to the instance reporting it or is reported by every instance, so that one instance's fault is never read as the installation's. An operator querying any instance SHALL obtain both the conditions that instance holds and the conditions the other instances report, each labelled with the instance reporting it, under the coverage rule stated above; an instance whose conditions could not be obtained SHALL be named rather than treated as holding none.

An instance serving routing decisions from installation-wide state it has not been able to refresh SHALL announce that condition for the whole period it holds, and the entry SHALL state how long the state it is serving from has been unrefreshed. Announcing it SHALL NOT depend on another instance being the one that notices, and SHALL NOT be satisfied by a record produced at the moment refreshing first failed: serving stale routes with no continuously observable signal is the failure this requirement exists to prevent, and a partition makes it both likelier and harder to see.

#### Scenario: A degraded condition is enumerable while it holds

- **WHEN** a component has been serving from a projection it cannot refresh for some time
- **THEN** an operator inspecting the component finds that condition listed with the time it began
- **AND** finding it does not require locating the record emitted when it began

#### Scenario: All current degradations are visible in one place

- **WHEN** two independent dependencies are unavailable at once
- **THEN** both conditions appear in the inventory
- **AND** each states its own onset time and effect

#### Scenario: Recovery clears the entry and is recorded

- **WHEN** a degraded condition is resolved
- **THEN** the entry is removed from the inventory
- **AND** a record of the recovery is produced

#### Scenario: Degradation is never silent

- **WHEN** a component continues to serve traffic while a dependency it needs is unavailable
- **THEN** the condition is observable for the whole period
- **AND** the component does not report itself as fully healthy during it

#### Scenario: A partition is announced, not silent

- **WHEN** an instance cannot reach part of the installation
- **THEN** the condition appears in that instance's degraded inventory for as long as it holds, naming the instances it cannot reach
- **AND** the entry states the time the condition began and its effect on serving
- **AND** the instance does not report itself as fully healthy during it

#### Scenario: Serving from unrefreshed installation-wide state is continuously visible

- **WHEN** an instance has been serving routing decisions from installation-wide state it cannot refresh for an extended period
- **THEN** an operator inspecting that instance finds the condition listed with how long the state has been unrefreshed
- **AND** finding it does not require locating the record emitted when refreshing first failed
- **AND** finding it does not require asking another instance

#### Scenario: A local condition is distinguishable from an installation-wide one

- **WHEN** one instance cannot reach the durable store while the others can
- **THEN** the entry states that the condition is local to that instance
- **AND** it is distinguishable from the same condition being reported by every instance

#### Scenario: Conditions on an unreachable instance are named, not assumed absent

- **WHEN** an operator inspects degraded conditions from an instance that cannot reach one of its peers
- **THEN** the answer is marked incomplete, naming that peer
- **AND** it does not report that peer as holding no degraded conditions

#### Scenario: State that has not converged is visible

- **WHEN** every instance is reachable again but one instance's installation-wide state is still older than its configured freshness bound
- **THEN** the condition appears in that instance's degraded inventory
- **AND** it is distinguishable from a partition that is still in progress
- **AND** the entry clears when the state is again within its freshness bound

### Requirement: Drain and shutdown are observable throughout

From the moment a drain begins until the component exits, an operator SHALL be able to observe that a drain is in progress, when it began, how long it has been running, and how many exchanges and bidirectional streams remain. These SHALL be observable continuously, not only at the start and end.

A drain that reaches its configured deadline with work remaining SHALL record what remained, including for each remaining exchange its age, its mount, and the condition it was waiting on. The transition into and out of drain SHALL be recorded with the reason the drain began.

Every drain observation SHALL identify the instance draining, and an operator SHALL be able to determine from any instance which instances of the installation are currently draining or withdrawing, under the coverage rule stated above. That an instance's withdrawal is one ordered lifecycle rather than several independent drains is `tunnel/sidecar-registry`'s obligation; what is required here is that each phase of it is observable while it is happening and attributable to the instance performing it.

#### Scenario: Remaining work is observable during drain

- **WHEN** a component is draining with exchanges still in flight
- **THEN** an operator can observe the drain's start time, its elapsed duration, and the number of exchanges and streams remaining
- **AND** the remaining count decreases as exchanges complete

#### Scenario: A drain deadline reports what it abandoned

- **WHEN** a drain reaches its deadline with exchanges still in flight
- **THEN** a record states how many remained
- **AND** for each, its age, its mount, and the condition it was waiting on

#### Scenario: Drain onset carries its reason

- **WHEN** a drain begins
- **THEN** a record names the reason it began
- **AND** the reason distinguishes an operator action, a planned withdrawal, and a received termination signal

#### Scenario: A draining instance is visible from another instance

- **WHEN** one instance of an installation is draining with exchanges still in flight
- **THEN** an operator querying a different instance can determine that it is draining, when its drain began, and how much work remains on it
- **AND** the observation identifies the draining instance
- **AND** the instances that are not draining are not reported as draining

#### Scenario: Each phase of an instance's withdrawal is observable while it happens

- **WHEN** an instance is withdrawn while it holds tunnels and exchanges
- **THEN** an operator can observe which phase of the withdrawal it is in for the whole time it is in that phase
- **AND** each observation is attributable to that instance

### Requirement: Signal identifiers are a stable interface

Event identifiers, enumerated reason values, enumerated outcome values, and measurement names SHALL be treated as an interface that operators build alerts and dashboards against. Adding one SHALL be permitted at any time. Removing or renaming one SHALL require a documented deprecation stated in the release that deprecates it, and the prior identifier SHALL continue to be produced for a documented period.

The full set of identifiers a release produces SHALL be published with that release, for every separately deployed component in the enumeration `operability/packaging` owns. This SHALL apply to signals produced by the sidecar and by the component that terminates client-facing protocols on the same terms as those produced by the proxy — for the sidecar because its versions in production are not under the operator's control, and for the others because an alert an operator built against one of them is no less an interface for being deployed by the operator themselves.

#### Scenario: An addition removes nothing

- **WHEN** a release introduces a new event identifier and a new enumerated reason
- **THEN** every identifier published for the prior release is still produced by this release
- **AND** the new identifiers appear in this release's published set
- **AND** no prior identifier changes its meaning

#### Scenario: Removal is announced and delayed

- **WHEN** a release deprecates an event identifier
- **THEN** the deprecation is stated in that release's documentation
- **AND** the identifier continues to be produced for the documented period
- **AND** the earliest release that may stop producing it is stated

#### Scenario: The identifier set is published

- **WHEN** a release is published
- **THEN** the complete set of event identifiers, enumerated reasons, enumerated outcomes, and measurement names it produces is published with it
- **AND** the published set matches what the release actually produces

#### Scenario: Sidecar signals are covered by the same rule

- **WHEN** a sidecar release changes the signals it produces
- **THEN** the same addition, deprecation, and publication rules apply
- **AND** an operator can determine which identifiers a given connected sidecar build produces

#### Scenario: Instances on different builds do not break an alert

- **WHEN** an installation is midway through an upgrade and its instances run two builds that both produce a given measurement
- **THEN** both instances produce it under the same identifier
- **AND** an installation aggregate over that measurement covers both instances
- **AND** the aggregate states that every instance contributed
