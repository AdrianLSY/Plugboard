## Purpose

Defines which sidecars are eligible to serve a mount at any instant, how one is chosen for a given request, and what is observed when sidecars appear, vanish, drain, disagree about what they can do, or become unreachable from the proxy instance handling the request. The registry is the component that turns "a tunnel exists somewhere in the installation" into a deterministic, tenant-scoped answer to "who serves this request, and if nobody, why not". It is also the only place that knows which contract versions and capabilities are actually deployed across a fleet the operator does not upgrade.

## ADDED Requirements

### Requirement: Eligibility begins and ends with the tunnel

A sidecar SHALL become eligible to serve a mount only after its tunnel has been established, authenticated, and negotiated, and SHALL cease to be eligible when that tunnel ends. Eligibility SHALL NOT outlive the tunnel under any termination path, including abnormal termination in which no closing exchange is ever sent, the disappearance of the sidecar's host, and abrupt failure of the proxy-side endpoint of the tunnel without any shutdown path running.

Removal SHALL NOT depend on the departing party sending anything, on a subsequent request discovering the failure, or on an operator intervening.

#### Scenario: Eligibility follows a completed handshake

- **WHEN** a tunnel is established, authenticated, and negotiated for a mount that had no eligible entry
- **THEN** the sidecar becomes eligible to serve that mount
- **AND** the next request matching that mount is selected to it

#### Scenario: Refused tunnel never becomes eligible

- **WHEN** a tunnel is refused because no contract version overlaps, or because authentication fails
- **THEN** no eligibility is recorded for that sidecar
- **AND** the count of eligible entries for the mount is unchanged

#### Scenario: Abnormal termination removes eligibility

- **WHEN** the proxy-side endpoint of an established tunnel fails abruptly without any shutdown path running
- **THEN** the sidecar ceases to be eligible within a configured bound
- **AND** no request is subsequently selected to it
- **AND** removal occurs without an operator action

#### Scenario: Graceful close removes eligibility without waiting for a bound

- **WHEN** a sidecar closes its tunnel cleanly
- **THEN** it is ineligible from the moment the close is observed
- **AND** no request is selected to it thereafter
- **AND** its removal does not wait for any liveness bound to elapse

### Requirement: Registration is authorised against a live mount of the credential's tenant

A tunnel SHALL be admitted to serve a mount only when that mount currently exists, is a mount point rather than an intermediate path in the hierarchy, and belongs to the tenant of the credential that established the tunnel. An attempt to register for a path that does not exist, for a path that is not a mount point, for a deleted mount, or for a mount of another tenant SHALL be refused, SHALL create no entry, and SHALL carry a reason distinguishing each of those cases from an authentication failure.

A tunnel SHALL be admitted for exactly one mount, the one its credential is scoped to. An entry SHALL be selectable only for that mount, and SHALL NOT acquire a second mount by any means. A sidecar deployment serving several mounts SHALL hold one tunnel, and therefore one entry, per mount.

When the mount an entry serves ceases to exist, the entry SHALL cease to be eligible without requiring the sidecar to reconnect, and its tunnel SHALL be ended with the reason the credentials capability requires for a credential whose mount has been removed. Other entries of the same sidecar deployment, belonging to other tunnels and other mounts, SHALL be unaffected.

#### Scenario: Registration for a path that is not a mount point is refused

- **WHEN** an authenticated sidecar attempts to register for an existing path that is not a mount point
- **THEN** the registration is refused
- **AND** no entry is created
- **AND** the reason distinguishes a non-mount target from an authentication failure

#### Scenario: Registration for a deleted mount is refused

- **WHEN** an authenticated sidecar attempts to register for a mount that has been deleted
- **THEN** the registration is refused
- **AND** the reason distinguishes a deleted target from a target that never existed

#### Scenario: A mount deleted under a live tunnel stops being served

- **WHEN** the mount served by an established tunnel is deleted
- **THEN** the entry ceases to be eligible without the sidecar reconnecting
- **AND** requests that previously matched the mount no longer reach that sidecar
- **AND** entries belonging to that sidecar deployment's other tunnels remain eligible for their own mounts

#### Scenario: An entry does not serve a mount it was not admitted for

- **WHEN** a request matches a mount of the same tenant other than the one an eligible entry was admitted for
- **THEN** that entry is not selected
- **AND** the request reports no sidecar available if no entry admitted for that mount is eligible

#### Scenario: One deployment, several mounts, several tunnels

- **WHEN** one sidecar deployment serves three mounts of one tenant
- **THEN** it holds three tunnels and yields three entries
- **AND** each entry is selectable only for its own mount

### Requirement: A registry entry describes one tunnel

The registry SHALL hold one entry per established tunnel, not one per sidecar deployment, per host, or per mount. Each entry SHALL record at minimum the tenant it belongs to, the single mount it was admitted to serve, the negotiated contract version, the declared capability set, an identifier distinguishing it from every other concurrent entry, and the proxy instance holding the tunnel.

The distinguishing identifier SHALL be assigned by the proxy. A value supplied by the sidecar SHALL NOT become the identifier and SHALL NOT cause an existing entry to be replaced, altered, or made ineligible.

A sidecar holding more than one concurrent tunnel SHALL yield more than one entry, and the ending of one of its tunnels SHALL NOT remove the entries of the others.

#### Scenario: Two tunnels from one sidecar are two entries

- **WHEN** one sidecar establishes two concurrent tunnels for the same mount
- **THEN** the mount reports two eligible entries
- **AND** ending one tunnel leaves the other eligible

#### Scenario: Entry describes what the tunnel negotiated

- **WHEN** a sidecar establishes a tunnel declaring a particular contract version and capability set
- **THEN** its entry reports that version and that capability set
- **AND** the entry reports the proxy instance holding the tunnel

#### Scenario: Two sidecars on one mount are distinguishable

- **WHEN** two separate sidecars serve the same mount
- **THEN** each has a distinct entry identifier
- **AND** an operator can tell which entry served a given exchange

#### Scenario: A sidecar cannot claim another entry's identifier

- **WHEN** a sidecar establishes a tunnel asserting an identifier equal to that of an existing eligible entry
- **THEN** the new entry receives a different identifier
- **AND** the existing entry remains eligible and unaltered

### Requirement: A superseded incarnation never removes its successor

When a sidecar reconnects, the entry for the new tunnel SHALL be independent of the entry for any previous tunnel of the same sidecar. Detecting the end of an earlier tunnel, however late that detection arrives, SHALL NOT remove, alter, or make ineligible an entry belonging to a later tunnel.

An entry belonging to a tunnel that has ended SHALL NOT be selectable regardless of whether a replacement tunnel exists.

#### Scenario: Reconnect before the old tunnel's death is detected

- **WHEN** a sidecar's process is destroyed without notice and the sidecar reconnects before the loss is detected
- **AND** the loss of the earlier tunnel is then detected
- **THEN** the entry for the new tunnel remains eligible
- **AND** requests continue to be served over the new tunnel

#### Scenario: Stale entry is not selectable

- **WHEN** an entry's tunnel has ended and a replacement tunnel from the same sidecar exists
- **THEN** selection returns the replacement and never the ended tunnel

#### Scenario: Repeated removal is harmless

- **WHEN** removal of an already-removed entry is attempted
- **THEN** the registry state is unchanged
- **AND** no other entry for that mount is affected

### Requirement: Selection is total, deterministic in outcome, and never unreachable

For a request matched to a mount, the registry SHALL return exactly one of: a single eligible entry, or an explicit statement that no eligible entry exists. It SHALL NOT return an entry whose tunnel has ended, an entry the selecting instance cannot deliver to, or an entry that has been marked draining.

Where no entry is returned, the statement SHALL distinguish two conditions with separate enumerated reasons: that no eligible entry exists anywhere in the installation for that mount, and that eligible entries exist but none of them is reachable from the selecting instance. The second SHALL NOT be reported, recorded, or measured as the first. A tenant that has deployed no sidecar and a tenant whose sidecar is connected to an instance this one cannot reach demand different responses from an operator, and collapsing them is how a partition is mistaken for a tenant misconfiguration. What the client observes MAY be identical in the two cases; what is recorded for the exchange and what an operator retrieves SHALL NOT be.

Two requests with identical properties arriving at the same mount SHALL receive the same class of outcome — served, refused for a missing capability, or no sidecar available — even when they are selected to different entries and even when they arrive at different proxy instances. This SHALL hold whenever every instance can reach the same set of entries. Where instances cannot, two instances MAY differ in outcome for identical requests, and that divergence SHALL be confined to the reachability condition above: it SHALL be recorded with the reachability reason at the instance that refused, and SHALL NOT appear as a capability refusal, as a missing mount, or as a different fidelity for the same request.

#### Scenario: Ended tunnel is never returned

- **WHEN** a mount's only sidecar tunnel has ended
- **AND** a request for that mount is matched
- **THEN** selection reports that no eligible sidecar exists
- **AND** no attempt is made to transmit over the ended tunnel

#### Scenario: Unreachable entry is not selected

- **WHEN** a proxy instance cannot deliver to a sidecar whose entry it can see
- **THEN** that instance does not select that entry
- **AND** it reports no sidecar available if no other entry is eligible

#### Scenario: Unreachable is not reported as absent

- **WHEN** a request for a mount arrives at an instance that can see the mount's only eligible entry but cannot deliver to it, and separately at an instance for a mount with no eligible entry anywhere
- **THEN** the two refusals carry different enumerated reasons
- **AND** the record for the first names the entry as existing but unreachable
- **AND** neither is recorded or counted as the other

#### Scenario: Divergence between instances is confined to reachability

- **WHEN** identical requests for one mount arrive at an instance that can reach its only entry and at an instance that cannot
- **THEN** the first is served and the second is refused with the reachability reason
- **AND** the second is not refused for a missing capability, for a missing mount, or served at reduced fidelity

#### Scenario: Identical requests agree on outcome

- **WHEN** two identical requests arrive at one mount served by several entries
- **THEN** both are served, or both are refused for the same reason
- **AND** the outcome does not depend on which entry each was selected to

#### Scenario: Outcome agrees across instances

- **WHEN** two identical requests for one mount arrive at two different proxy instances
- **THEN** both receive the same class of outcome

### Requirement: Selection spreads load across eligible entries

When more than one entry is eligible for a mount and no affinity binding applies, selection SHALL distribute requests across the eligible entries rather than repeatedly returning one of them. A newly eligible entry SHALL be selectable for the next matching request without waiting for any existing entry to become ineligible.

Removal of an entry SHALL NOT cause requests to concentrate on a single remaining entry when several remain eligible.

#### Scenario: Requests reach every eligible entry

- **WHEN** a number of requests without affinity keys several times larger than the number of eligible entries arrives at one mount
- **THEN** every eligible entry receives at least one of them

#### Scenario: A new sidecar receives work without a departure

- **WHEN** a further sidecar becomes eligible for a mount that is already serving requests
- **THEN** it receives a request before any existing entry becomes ineligible

#### Scenario: Departure does not concentrate load

- **WHEN** one of several eligible entries becomes ineligible
- **AND** further requests without affinity keys arrive
- **THEN** every remaining eligible entry receives at least one of them

### Requirement: Eligibility is filtered by capability before selection, not after

The registry SHALL restrict selection for a request to those eligible entries that declare every capability the request requires. The restriction SHALL be a property of the whole eligible set: the entry returned SHALL NOT depend on the order in which entries are examined, on the order in which they became eligible, or on which entry a prior request was selected to.

A request SHALL be refused for a missing capability only when no eligible entry for that mount declares it. An entry that does declare the required capabilities SHALL NOT be passed over in favour of refusal.

#### Scenario: A capable entry is preferred over refusal

- **WHEN** a mount has two eligible entries and only one declares the capability a request requires
- **THEN** the request is selected to the entry that declares it
- **AND** the request is not refused

#### Scenario: No capable entry yields a stable refusal

- **WHEN** no eligible entry for a mount declares a capability a request requires
- **THEN** the request is refused
- **AND** an identical request arriving immediately afterwards is refused for the same reason
- **AND** the refusal names the missing capability rather than reporting no sidecar available

#### Scenario: Capability answer is order-independent

- **WHEN** two mounts hold eligible entries with identical capability sets that became eligible in opposite orders
- **AND** an identical request requiring a capability only one entry declares is matched to each
- **THEN** both requests are selected to an entry declaring that capability

#### Scenario: A withdrawn capability changes the answer at the reconnect boundary

- **WHEN** the only entry declaring a capability is replaced by a reconnection declaring fewer capabilities
- **THEN** requests admitted after the replacement are refused for the missing capability
- **AND** exchanges already in flight over the earlier tunnel are unaffected by the change

### Requirement: Affinity bindings are registry state with a bounded lifetime

Where the contract carries an affinity key on a request, the registry SHALL hold the binding from that key to the entry serving it. A binding SHALL be scoped to one tenant and one mount, SHALL be honoured from every proxy instance, SHALL be released when its entry becomes ineligible, and SHALL expire after a configured period without use.

An affinity key SHALL NOT permit a client to name a particular entry: the entry a new key binds to SHALL be chosen by the registry, and a binding SHALL NOT override capability filtering. The registry SHALL NOT establish a new binding against an entry marked draining.

#### Scenario: Binding is honoured from another instance

- **WHEN** a keyed request establishes a binding through one proxy instance
- **AND** a later request bearing the same key arrives at a different proxy instance
- **THEN** it is selected to the same entry

#### Scenario: Binding does not outlive its entry

- **WHEN** the entry holding a binding becomes ineligible
- **THEN** the binding is released
- **AND** no subsequent request is selected to the ineligible entry on the strength of that key

#### Scenario: Idle bindings expire

- **WHEN** no request bearing a key arrives for longer than the configured period
- **THEN** the binding is released
- **AND** the number of retained bindings returns to the number in active use

#### Scenario: Bindings cannot cross a tenant boundary

- **WHEN** a request for one tenant's mount bears an affinity key identical to one in use by another tenant
- **THEN** it is not selected to the other tenant's entry
- **AND** the two bindings are independent

#### Scenario: No new binding against a draining entry

- **WHEN** a keyed request with no existing binding arrives at a mount with one draining entry and one that is not draining
- **THEN** the binding is established against the entry that is not draining
- **AND** no binding is created against the draining entry

#### Scenario: A key cannot pin a chosen entry

- **WHEN** two distinct affinity keys are presented in turn to a mount with several eligible entries
- **THEN** the entry each binds to is chosen by the registry
- **AND** no value carried on the request determines which entry is chosen

#### Scenario: Affinity does not override capability filtering

- **WHEN** a request requiring a capability bears an affinity key already bound to an entry that does not declare it
- **THEN** the request is refused for the missing capability
- **AND** it is not served at reduced fidelity by the bound entry

### Requirement: An affinity binding whose entry is unreachable has a declared outcome

A binding is registry state honoured from every instance, so a keyed request may arrive at an instance that cannot reach the entry its key is bound to while that entry's tunnel is still established. That condition is distinct from the entry becoming ineligible and SHALL NOT be treated as it: a binding SHALL NOT be released because one instance cannot reach its entry, and an instance SHALL NOT record such a binding as expired or as released when what it observed was unreachability.

What happens to such a request SHALL be a declared property of the installation's configuration rather than whatever an implementation happens to do, and SHALL be exactly one of two. Under *refuse*, the request is refused with an enumerated reason naming an unreachable bound counterpart, distinguishable from no eligible entry existing for the mount and from a capability refusal, and no other entry is selected for it. Under *rebind*, the registry selects a reachable eligible entry, binds the key to it, and records the rebinding naming the key's previous entry, the new entry, and the instance that performed it. No third behaviour SHALL be available, the declared choice SHALL be retrievable by an operator alongside the registry's other configured bounds, and a rebinding SHALL NOT be silent — a session moved to a different counterpart without a record is the failure this requirement exists to prevent.

Under either declaration the entry a key binds to SHALL be chosen by the registry and not by anything the client supplies, capability filtering SHALL still apply, and no new binding SHALL be established against a draining entry.

When instances can reach one another again, exactly one binding SHALL survive for a given key, tenant and mount. Where both sides of a partition bound the same key while they could not reach one another, convergence SHALL leave one of them, without operator action and within a bounded time, and SHALL record which binding was discarded. No key SHALL remain bound to an entry whose tunnel has ended, and a binding SHALL survive the loss of any instance other than the one holding the entry it names.

#### Scenario: Unreachability is not treated as expiry

- **WHEN** a keyed request arrives at an instance partitioned from the instance holding the entry its key is bound to
- **AND** the entry's tunnel remains established throughout
- **THEN** the binding is not released
- **AND** no record states that it expired or that its entry became ineligible
- **AND** once the instances can reach one another again a keyed request at either instance is selected to that same entry

#### Scenario: The refuse declaration refuses rather than moves the session

- **WHEN** the refuse behaviour is declared and a keyed request reaches an instance that cannot reach its bound entry
- **THEN** the request is refused with an enumerated reason naming an unreachable bound counterpart
- **AND** that reason is distinguishable from no eligible entry existing and from a capability refusal
- **AND** the request is not selected to any other entry

#### Scenario: The rebind declaration records the move

- **WHEN** the rebind behaviour is declared and a keyed request reaches an instance that cannot reach its bound entry while another eligible entry is reachable
- **THEN** the request is selected to a reachable eligible entry
- **AND** a record names the previous entry, the new entry, and the instance that rebound the key
- **AND** the entry chosen is not determined by any value the request carried

#### Scenario: The declared behaviour is retrievable and is one of two

- **WHEN** an operator retrieves the registry's configured behaviour for a binding whose entry is unreachable
- **THEN** exactly one of refuse and rebind is reported
- **AND** no third behaviour can be configured

#### Scenario: Bindings converge to one after a partition

- **WHEN** the same key is bound on both sides of a partition and the partition then heals
- **THEN** exactly one binding for that key, tenant and mount remains within a bounded time and without operator action
- **AND** the discarded binding is recorded
- **AND** subsequent keyed requests at every instance are selected to the surviving entry

#### Scenario: A binding outlives an unrelated instance

- **WHEN** the instance through which a binding was established is lost while the instance holding its entry continues to serve
- **THEN** the binding remains
- **AND** a later request bearing the key arriving at any surviving instance is selected to the same entry

### Requirement: Liveness is proven end to end, not inferred from the transport

The registry SHALL determine that a tunnel is alive from the liveness exchange the wire contract defines, answered by the layer that implements the contract, and SHALL NOT define a second liveness mechanism of its own. It SHALL NOT treat the underlying connection being open, or a keepalive answered by a transport library or an intermediary below the sidecar's contract logic, as evidence of liveness.

An entry that fails to demonstrate liveness within a configured bound SHALL be made ineligible and removed. The bound SHALL be observable, and the removal SHALL be recorded with a reason distinguishing it from a clean close. Liveness SHALL be a property of the tunnel only; the registry SHALL NOT probe a tenant's backend to decide eligibility.

#### Scenario: Frozen sidecar with an open connection

- **WHEN** a sidecar's tunnel connection remains open but the sidecar stops processing tunnel work entirely
- **THEN** it fails to demonstrate liveness within the configured bound
- **AND** it becomes ineligible
- **AND** its removal is recorded as a liveness failure rather than a clean close

#### Scenario: Transport-level keepalive alone is not liveness

- **WHEN** an intermediary between the proxy and the sidecar answers transport keepalives on the sidecar's behalf
- **AND** the sidecar itself produces no liveness signal
- **THEN** the entry is treated as not alive
- **AND** it becomes ineligible within the configured bound

#### Scenario: Silently severed network path

- **WHEN** the network path to a sidecar is severed without either side observing a close
- **THEN** the entry becomes ineligible within the configured bound
- **AND** requests arriving after that point report no sidecar available rather than hanging

#### Scenario: A failing backend does not make a sidecar ineligible

- **WHEN** a sidecar proves liveness on its tunnel while every request it forwards fails at the tenant's backend
- **THEN** the entry remains eligible
- **AND** the failures are reported as backend errors rather than as sidecar unavailability

#### Scenario: Last proof of liveness is observable

- **WHEN** an operator inspects an eligible entry
- **THEN** the time since that entry last proved liveness is reported

### Requirement: Departure fails in-flight exchanges promptly and distinguishably

When an entry becomes ineligible for any reason other than a completed drain, every exchange in flight to that entry SHALL be failed promptly rather than left to reach a bound. This includes exchanges awaiting a response head, exchanges mid-body in either direction, and established bidirectional streams.

The failure SHALL carry a reason identifying sidecar unavailability, distinguishable from an inactivity bound being exceeded, from a backend error reported by the sidecar, and from a client-initiated cancellation. Fan-out SHALL occur on abrupt failure as well as on clean shutdown, and the number of exchanges and streams affected SHALL be recorded. No state retained for a failed exchange SHALL survive the fan-out.

#### Scenario: Waiting exchanges fail immediately

- **WHEN** a sidecar with exchanges awaiting responses becomes ineligible
- **THEN** every waiting exchange fails before any inactivity bound elapses
- **AND** each failure names sidecar unavailability as the reason

#### Scenario: Reason is distinguishable from a bound expiry

- **WHEN** an exchange fails because its sidecar departed
- **AND** another exchange fails because an inactivity bound was exceeded
- **THEN** the two failures carry different reasons
- **AND** an operator can count them separately

#### Scenario: Bidirectional streams are closed, not abandoned

- **WHEN** a sidecar carrying established bidirectional streams becomes ineligible
- **THEN** each stream is closed toward its client with a reason indicating sidecar unavailability
- **AND** no stream is left open awaiting frames that cannot arrive

#### Scenario: Fan-out survives abrupt failure

- **WHEN** the proxy-side endpoint of a tunnel fails without running any shutdown path
- **THEN** in-flight exchanges are still failed promptly
- **AND** the count of affected exchanges and streams is recorded

#### Scenario: Mid-body failure is not reported as success

- **WHEN** a sidecar departs after a response head has already reached the client
- **THEN** the response is terminated as incomplete
- **AND** the client is not led to believe the body ended normally

#### Scenario: A late frame for a failed exchange is discarded

- **WHEN** a frame arrives for an exchange that was already failed by a departure fan-out
- **THEN** it is discarded and recorded
- **AND** it is not delivered to any client
- **AND** the retained state for that mount does not grow as such frames accumulate

### Requirement: Reselection is bounded and never revisits an attempted entry

Where a selected entry becomes ineligible before any part of an exchange has been delivered to it, the registry SHALL permit selection of another eligible entry. Each reselection SHALL exclude every entry already attempted for that exchange, and the number of attempts for one exchange SHALL be bounded by configuration. On exhausting the bound the outcome SHALL be no sidecar available, produced without waiting for any timer.

Once any part of an exchange has been delivered to an entry, the registry SHALL NOT offer another entry for that exchange.

#### Scenario: Pre-delivery failure yields a different entry

- **WHEN** a selected entry becomes ineligible before any octet of the request has been delivered to it
- **AND** another entry is eligible
- **THEN** the exchange is delivered to that other entry
- **AND** exactly one sidecar receives the request

#### Scenario: An attempted entry is not offered twice

- **WHEN** reselection occurs for an exchange
- **THEN** no entry already attempted for that exchange is returned again

#### Scenario: Attempts are bounded

- **WHEN** eligible entries become ineligible before delivery more times than the configured attempt bound
- **THEN** the outcome is no sidecar available
- **AND** it is produced without waiting for any timer

#### Scenario: No entry is offered after delivery begins

- **WHEN** part of an exchange has been delivered to an entry and that entry becomes ineligible
- **THEN** the registry offers no further entry for that exchange
- **AND** the exchange fails

### Requirement: No sidecar available is its own outcome

When a request matches a mount for which no entry is eligible, the proxy SHALL produce an outcome distinguishable from an unmatched mount, from a refusal for a missing capability, from a sidecar-side backend failure, and from an exceeded inactivity bound. The outcome SHALL carry a machine-readable reason and SHALL be produced without waiting for any timer.

The registry SHALL make the count of mounts with no eligible entry observable, and SHALL make the reason no entry is eligible — never connected, all departed, or all draining — available for diagnosis.

#### Scenario: Known mount with no sidecar

- **WHEN** a request matches a configured mount and no entry is eligible
- **THEN** the response reason identifies the absence of an available sidecar
- **AND** it differs from the reason given for a path matching no mount
- **AND** it is produced without waiting for a timeout

#### Scenario: Distinguishable from a capability refusal

- **WHEN** one request is refused because no eligible entry declares a required capability
- **AND** another is refused because no entry is eligible at all
- **THEN** the two reasons differ

#### Scenario: All entries draining is diagnosable

- **WHEN** every entry for a mount is marked draining
- **THEN** requests report no sidecar available
- **AND** the diagnostic reason states that the eligible entries are draining

#### Scenario: Unserved mounts are countable

- **WHEN** an operator inspects the installation
- **THEN** the number of mounts with no eligible entry is reported
- **AND** it is reported per tenant

### Requirement: A sidecar connected to one instance serves requests arriving at any instance

An entry created by a tunnel terminated on one proxy instance SHALL be selectable for a matching request arriving at any other proxy instance, without redirecting the client, requiring the client to reconnect, or requiring the sidecar to hold a tunnel to every instance.

Adding or removing a proxy instance SHALL NOT require sidecars to reconnect in order to remain reachable from the surviving instances.

#### Scenario: Cross-instance request is served

- **WHEN** a sidecar holds its tunnel to one instance
- **AND** a matching request arrives at a different instance
- **THEN** the request is served over that sidecar's tunnel
- **AND** the client is not redirected

#### Scenario: A new instance sees existing sidecars

- **WHEN** a proxy instance joins the installation
- **THEN** it can select entries whose tunnels are held by other instances
- **AND** no sidecar reconnects in order to become visible to it

#### Scenario: Losing an instance removes only its entries

- **WHEN** a proxy instance is lost
- **THEN** entries whose tunnels it held become ineligible everywhere within a configured bound
- **AND** entries held by surviving instances remain eligible

### Requirement: The registry converges after a partition without intervention

While proxy instances are partitioned, an instance SHALL serve requests only from entries it can reach, and SHALL report no sidecar available rather than selecting an entry on the far side of the partition. When the partition heals, the registry SHALL converge, without operator action and within a bounded time, to exactly the set of entries whose tunnels are still established.

Convergence SHALL NOT produce a duplicate entry for a single tunnel, SHALL NOT retain an entry for a tunnel that ended during the partition, and SHALL NOT require any sidecar to reconnect.

#### Scenario: Partitioned instance does not select across the partition

- **WHEN** a proxy instance is partitioned from the instance holding a mount's only tunnel
- **AND** a request for that mount arrives at the partitioned instance
- **THEN** it reports no sidecar available
- **AND** it does not attempt to transmit to the unreachable entry

#### Scenario: Healing restores mutual visibility

- **WHEN** a partition heals and both tunnels remained established throughout
- **THEN** every instance reports both entries as eligible within a bounded time
- **AND** no operator action was required

#### Scenario: Entries for tunnels that ended during the partition do not return

- **WHEN** a tunnel ends on one side while the instances are partitioned
- **AND** the partition then heals
- **THEN** no instance reports that entry as eligible
- **AND** no request is selected to it

#### Scenario: Reconnection during a partition does not duplicate

- **WHEN** a sidecar's tunnel ends on one side of a partition and it reconnects to the other side
- **AND** the partition heals
- **THEN** exactly one entry exists for that sidecar's live tunnel
- **AND** the mount's eligible count reflects one tunnel, not two

### Requirement: A sidecar can drain without failing its in-flight work

A sidecar announces that it is draining by sending the **drain notice** the wire contract defines, carrying its enumerated reason and the highest stream identifier it will still serve; this capability defines no second mechanism and no second name for it. On receiving one the registry SHALL immediately stop selecting that entry for new exchanges while allowing its in-flight exchanges and established bidirectional streams to continue. Draining SHALL NOT require the sidecar to close its tunnel, and SHALL NOT itself fail any exchange. An exchange the sidecar opens above the identifier its notice stated SHALL be resolved as the contract requires rather than by the registry.

A drain notice SHALL affect only the entry of the tunnel it arrived on, and its effect SHALL NOT be reversible; a sidecar that wishes to serve again SHALL establish a new tunnel. A draining entry SHALL be ineligible for new exchanges even when it is the only entry for the mount. Drain state SHALL be visible from every proxy instance. The entry SHALL be removed when its last exchange completes, or when a configured drain deadline expires, at which point any remaining exchanges are failed as a departure.

#### Scenario: Draining stops new work only

- **WHEN** a sidecar declares that it is draining while exchanges are in flight
- **THEN** no further request is selected to it
- **AND** its in-flight exchanges complete normally
- **AND** its established bidirectional streams remain open

#### Scenario: Drain is visible installation-wide

- **WHEN** a sidecar declares that it is draining
- **AND** a request arrives at a proxy instance other than the one holding its tunnel
- **THEN** that instance does not select the draining entry

#### Scenario: Sole entry draining refuses new work

- **WHEN** the only entry for a mount is draining
- **AND** a new request for that mount arrives
- **THEN** it reports no sidecar available
- **AND** it is not selected to the draining entry

#### Scenario: A drain notice affects only its own entry

- **WHEN** one of several entries of the same tenant on the same mount declares that it is draining
- **THEN** only that entry is marked draining
- **AND** the other entries continue to receive requests

#### Scenario: Drain cannot be revoked on the same tunnel

- **WHEN** a draining sidecar declares that it is no longer draining on the same tunnel
- **THEN** the entry remains draining
- **AND** no request is selected to it

#### Scenario: Drain completes into removal

- **WHEN** the last exchange on a draining entry completes
- **THEN** the entry is removed
- **AND** no departure failure is reported for any exchange it completed

#### Scenario: Drain deadline bounds the wait

- **WHEN** exchanges remain in flight on a draining entry past the configured drain deadline
- **THEN** the remaining exchanges are failed with the sidecar-unavailability reason
- **AND** the entry is removed

### Requirement: A sidecar shutting down drains before it closes

A sidecar that is asked to terminate SHALL declare that it is draining before it closes its tunnel, SHALL allow its in-flight exchanges and established bidirectional streams a configured period to complete, SHALL end what remains spread across a configured window rather than at one instant, and SHALL only then close the tunnel with the reason naming planned withdrawal. A sidecar SHALL NOT close a tunnel carrying work as its first response to a termination signal.

This obligation exists because a tenant redeploys their own sidecars on their own schedule and far more often than the operator withdraws a proxy instance: without it, every ordinary tenant deployment ends every session it was carrying simultaneously, and the resulting reconnections arrive as one synchronised burst against the mount that just lost its capacity.

Where the sidecar is not given time to complete the drain by whatever terminated it, the tunnel SHALL end as an unannounced loss and be handled as a departure. A sidecar SHALL NOT extend its own shutdown beyond the configured deadline in order to finish draining.

#### Scenario: Termination drains rather than severs

- **WHEN** a sidecar carrying in-flight exchanges and established bidirectional streams is asked to terminate
- **THEN** it declares that it is draining before closing anything
- **AND** its in-flight work is given the configured period to complete
- **AND** its tunnel is closed with the reason naming planned withdrawal

#### Scenario: Remaining sessions are spread, not simultaneous

- **WHEN** a sidecar carrying many established bidirectional streams reaches the end of its drain period
- **THEN** the remaining streams are ended across the configured window
- **AND** they are not all ended within a single instant

#### Scenario: Drain is bounded by the shutdown deadline

- **WHEN** work remains in flight when a sidecar's configured shutdown deadline elapses
- **THEN** the sidecar ends the remaining work and closes
- **AND** it does not continue past the deadline in order to finish draining

#### Scenario: A killed sidecar is an unannounced loss

- **WHEN** a sidecar's process is destroyed with no opportunity to declare drain
- **THEN** the registry records an unannounced loss rather than a completed drain
- **AND** its in-flight exchanges are failed as a departure

### Requirement: Planned proxy withdrawal does not disconnect a fleet at once

Withdrawing a proxy instance SHALL be one ordered lifecycle, not several independent drains that each capability starts for itself. Its phases SHALL occur in this order, and each SHALL be complete before the next begins: the instance withdraws its readiness signal; it stops accepting new tunnels and stops admitting new exchanges and new bidirectional streams; it allows exchanges and streams already in flight a configured period to complete; it ends what remains, spread across a configured window rather than simultaneously; it exits.

One configured deadline SHALL govern the whole lifecycle. A capability that specifies the treatment of its own subject during withdrawal — request/response exchanges, bidirectional streams, or tunnels — SHALL do so within these phases and SHALL NOT introduce a second ordering or a second deadline.

Each ended tunnel SHALL carry a reason distinguishing planned withdrawal from failure, so a sidecar can distinguish an expected reconnection from an incident.

#### Scenario: New tunnels are refused before existing ones end

- **WHEN** a proxy instance begins withdrawal
- **THEN** it refuses new tunnel establishment
- **AND** existing tunnels remain established and continue to serve requests

#### Scenario: Tunnel endings are spread over a window

- **WHEN** a withdrawing instance holds many tunnels
- **THEN** the interval between the first ending and the last is no shorter than the configured window
- **AND** no more than a bounded fraction of them end within any one interval of that window

#### Scenario: Planned withdrawal is distinguishable from failure

- **WHEN** a tunnel is ended because its instance is being withdrawn
- **THEN** the reason conveyed identifies planned withdrawal
- **AND** it differs from the reason conveyed on a liveness failure

#### Scenario: In-flight exchanges are given time

- **WHEN** an instance is withdrawn while exchanges are in flight
- **THEN** those exchanges are given the configured period to complete
- **AND** only those still in flight after it are failed as a departure

#### Scenario: The phases occur in order

- **WHEN** an instance is withdrawn while it holds tunnels, request/response exchanges, and bidirectional streams
- **THEN** its readiness signal reports failure before it refuses the first new tunnel, exchange, or stream
- **AND** it refuses new work of all three kinds before it ends any tunnel, exchange, or stream
- **AND** it ends none of them before the configured completion period has elapsed

#### Scenario: One deadline governs every kind of work

- **WHEN** an instance is withdrawn holding both long-lived exchanges and bidirectional streams
- **THEN** both are ended under the same configured deadline
- **AND** neither kind is held past it because a separate deadline was applied to it

#### Scenario: Withdrawal completes early when nothing remains

- **WHEN** every exchange, stream, and tunnel has ended before the configured window elapses
- **THEN** the instance exits without waiting out the remainder of the window

### Requirement: A withdrawal is bounded and attributable for the client and the sidecar it interrupts

An installation is upgraded by withdrawing instances one at a time while the rest continue to serve, so what a client and a sidecar observe while one instance withdraws is owned here, alongside the withdrawal lifecycle itself, rather than left to whichever capability notices.

A request arriving at an instance after it has withdrawn its readiness signal and stopped admitting new exchanges SHALL be refused with an enumerated reason naming that instance's withdrawal. It SHALL NOT be held until the withdrawal deadline, SHALL NOT be dispatched to a sidecar, and SHALL be distinguishable by the client from no eligible sidecar existing and from a failure of the tenant's backend. Such arrivals are expected rather than exceptional: whatever directs traffic takes a finite time to stop offering it to an instance that has withdrawn readiness.

Withdrawing one instance SHALL NOT make a mount unserveable at another while an eligible entry for it remains. Entries held by other instances SHALL remain selectable throughout, and the withdrawing instance's own entries SHALL cease to be selectable from every instance as their tunnels end, within the bound that governs an ended tunnel — whether or not the withdrawing instance has completed its exit.

Other instances SHALL record the withdrawal as a planned withdrawal, distinguishable from the loss of an instance and from a liveness failure, and SHALL NOT report a withdrawing instance as having fallen out of the installation.

A sidecar whose tunnel is ended by withdrawal SHALL receive the reason naming planned withdrawal, and SHALL be able to re-establish at a surviving instance under the ordinary establishment path, subject to the backoff and spreading the requirement below states. It SHALL NOT be required to wait for the withdrawn instance to return, and the entry of its new tunnel SHALL be eligible without waiting for the entry of its ended tunnel to be reaped.

#### Scenario: A request arriving after readiness is withdrawn is refused, not held

- **WHEN** a request arrives at an instance that has withdrawn readiness and stopped admitting new exchanges
- **THEN** it is refused with an enumerated reason naming that instance's withdrawal
- **AND** it is not held until the withdrawal deadline and is not dispatched to a sidecar
- **AND** the reason is distinguishable from no eligible sidecar existing and from a backend failure

#### Scenario: Another instance keeps serving the mount

- **WHEN** a mount holds eligible entries on two instances and one of them is withdrawn
- **THEN** requests arriving at the surviving instance continue to be served throughout the withdrawal
- **AND** the withdrawn instance's entries cease to be selectable from every instance as their tunnels end

#### Scenario: A withdrawal is not recorded as a loss

- **WHEN** an instance is withdrawn in a planned manner
- **THEN** the other instances record a planned withdrawal
- **AND** it is distinguishable from an instance lost without a withdrawal and from a liveness failure

#### Scenario: The sidecar reconnects elsewhere without waiting

- **WHEN** a sidecar's tunnel is ended by the withdrawal of the instance holding it
- **THEN** the reason it receives names planned withdrawal
- **AND** it establishes a new tunnel at a surviving instance and its new entry is eligible
- **AND** it is not required to wait for the withdrawn instance to return or for its previous entry to be reaped

#### Scenario: A rolling withdrawal keeps the installation serving

- **WHEN** every instance of the installation is withdrawn and replaced in turn, one at a time, while a tenant's sidecars hold tunnels to more than one instance
- **THEN** at every point in the sequence a request for that tenant's mount is served or refused with an enumerated reason
- **AND** no request is left without an outcome
- **AND** no operator action and no sidecar configuration change is required for the mount to be served throughout

### Requirement: Registry state is usable by instances of both code versions during an upgrade

Because instances are replaced one at a time, instances of two code versions SHALL be expected to hold and read one registry state. An instance SHALL NOT make an entry ineligible, remove it, or decline to select it because the entry carries an attribute its own version does not define. It SHALL select such an entry for the mount the entry names on the strength of the attributes it does interpret, SHALL record the unrecognised attribute, and SHALL preserve it unchanged in any update it makes to that entry. An instance SHALL NOT treat an entry it cannot fully interpret as evidence that the entry's tunnel has ended.

An entry whose tenant, mount, negotiated contract version, capability set, or holding instance cannot be interpreted at all SHALL NOT be selected by that instance — refusal rather than a guess — and SHALL be surfaced as a distinct condition naming the entry and the instance that could not interpret it, rather than as no eligible entry existing for the mount.

An upgrade SHALL NOT require the registry to be emptied, and SHALL NOT require any sidecar to reconnect in order for its entry to be selectable by an instance of the newer version.

#### Scenario: An entry from a newer instance is selectable by an older one

- **WHEN** an entry is created by an instance of a newer code version carrying an attribute an older instance does not define
- **AND** a matching request arrives at the older instance
- **THEN** the entry is selected and the request is served
- **AND** the unrecognised attribute is recorded

#### Scenario: An update by an older instance preserves what it does not understand

- **WHEN** an instance of the older code version updates an entry carrying an attribute its version does not define
- **THEN** that attribute is unchanged afterwards
- **AND** an instance of the newer version reads the value it held before the update

#### Scenario: An uninterpretable entry is a named condition, not an absent sidecar

- **WHEN** an instance encounters an entry whose mount or tenant it cannot interpret
- **THEN** it does not select that entry
- **AND** the condition is surfaced naming the entry and that instance
- **AND** a request for that mount is not reported as having no eligible entry anywhere in the installation

#### Scenario: An upgrade needs no reconnection

- **WHEN** every instance is replaced in turn by one of a newer code version
- **THEN** entries established before the upgrade remain selectable throughout
- **AND** no sidecar is required to reconnect for its entry to be selectable

### Requirement: Re-establishment after a lost tunnel is backed off and spread

A sidecar whose tunnel has ended SHALL attempt to establish a new one, and SHALL space its attempts by an interval that increases with the number of consecutive failures up to a configured ceiling. The interval SHALL carry a randomised component drawn independently per sidecar, so that a population of sidecars that lost their tunnels at the same instant does not attempt re-establishment at the same instant. The interval SHALL NOT return to its initial value however long the failures continue, and SHALL NOT be derived from a value shared across a fleet.

A sidecar SHALL serialise its own re-establishment attempts, so that a single lost tunnel produces one sequence of attempts rather than one per detector of the loss. A sidecar SHALL distinguish an ending that named planned withdrawal from one that named a failure, and SHALL NOT treat an ending that named credential invalidity as a reason to retry with the same credential.

The proxy SHALL make the rate of tunnel-establishment attempts observable, separately from the rate of successful establishments, so that a re-establishment storm is diagnosable as such.

#### Scenario: A simultaneously disconnected fleet does not converge

- **WHEN** many sidecars lose their tunnels at the same instant
- **THEN** their first re-establishment attempts are spread across the randomisation interval
- **AND** no two derive their interval from a value shared across the fleet

#### Scenario: Backoff does not collapse over a long outage

- **WHEN** re-establishment fails continuously for a very large number of consecutive attempts
- **THEN** the interval between attempts remains at or below the configured ceiling
- **AND** it never returns to its initial value
- **AND** the attempt rate does not rise as the failure count grows

#### Scenario: One loss yields one sequence of attempts

- **WHEN** a sidecar detects the loss of one tunnel by more than one means at once
- **THEN** it makes one sequence of re-establishment attempts
- **AND** it does not open concurrent establishment attempts for that tunnel

#### Scenario: An invalidated credential is not retried

- **WHEN** a tunnel is ended with a reason naming the credential as no longer valid
- **THEN** the sidecar does not re-attempt establishment with that credential
- **AND** it reports the condition rather than entering a retry loop

#### Scenario: A storm is visible as a storm

- **WHEN** establishment attempts arrive far faster than they succeed
- **THEN** the attempt rate and the success rate are separately retrievable
- **AND** an operator can distinguish a re-establishment storm from ordinary connection churn

### Requirement: Registry contents are scoped to a tenant

Every entry SHALL belong to exactly one tenant, determined by the credential that established its tunnel and not by anything the sidecar asserts about itself. Lookup, selection, enumeration, counting, and diagnostics SHALL be tenant-scoped, such that no query performed on behalf of one tenant can observe, count, or reach another tenant's entries.

#### Scenario: Cross-tenant registration is refused

- **WHEN** a sidecar authenticated for one tenant attempts to register for a mount belonging to another
- **THEN** the registration is refused
- **AND** no entry is created
- **AND** the attempt is recorded for audit

#### Scenario: Selection never crosses tenants

- **WHEN** two tenants have mounts identified identically within their own scopes
- **AND** a request arrives for one tenant's mount
- **THEN** it is selected only from that tenant's entries
- **AND** the other tenant's sidecars are never considered

#### Scenario: Enumeration is scoped

- **WHEN** a tenant lists the sidecars serving their mounts
- **THEN** only their own entries are returned
- **AND** no identifier, instance, count, or capability of another tenant's entry is disclosed

#### Scenario: Tenant is taken from the credential

- **WHEN** a sidecar asserts a tenant other than the one its credential belongs to
- **THEN** the asserted value is ignored
- **AND** the entry is scoped to the credential's tenant

### Requirement: Registrations and bindings are bounded per tenant

The number of concurrently registered entries SHALL be bounded per mount and per tenant by configuration, and the number of concurrent affinity bindings SHALL be bounded per tenant. These are standing-resource dimensions this capability contributes to the single closed enumeration of per-tenant bound dimensions the tenancy capability owns, on that enumeration's terms — one configured value per tenant, accounted once wherever it is applied, with each tenant's consumption observable; this capability SHALL NOT hold a second value for either. A registration or binding that would exceed a bound SHALL be refused with a reason naming the exceeded bound, and SHALL NOT displace an existing entry or binding.

Because a tenant's sidecars may establish tunnels to different instances, both bounds SHALL be counted over the installation and not over the entries or bindings the admitting instance itself holds: a tenant SHALL NOT obtain more entries or more bindings than the configured value by distributing its tunnels or its keyed traffic across instances. Where the admitting instance cannot account the tenant's total across the installation, the discipline the tenancy capability requires the installation to declare governs whether the registration or binding is refused or admitted to a local share, and the refusal SHALL name that condition distinguishably from the tenant having reached the configured bound. Entries and bindings held by an instance that is lost SHALL cease to be counted against the tenant within a bounded time, so a lost instance does not permanently occupy a tenant's allowance.

Exhausting a bound for one tenant SHALL NOT affect the ability of any other tenant to register, select, or serve.

#### Scenario: Registration beyond the bound is refused

- **WHEN** a tenant already holds the configured maximum number of entries for a mount
- **AND** a further sidecar attempts to establish a tunnel for that mount
- **THEN** the registration is refused
- **AND** the reason names the exceeded bound
- **AND** every existing entry remains eligible

#### Scenario: Binding beyond the bound is refused, not evicted into

- **WHEN** a tenant already holds the configured maximum number of affinity bindings
- **AND** a request bearing an unbound key arrives
- **THEN** no new binding is established
- **AND** no existing binding is displaced
- **AND** the outcome names the exceeded bound

#### Scenario: Entries spread across instances count once

- **WHEN** a tenant's sidecars hold tunnels to several instances totalling the configured maximum entries for a mount
- **AND** a further tunnel for that mount is established at any instance, including one holding none of them
- **THEN** the registration is refused with the reason naming the exceeded bound
- **AND** the tenant's entries across the installation do not exceed the configured value

#### Scenario: A lost instance does not hold a tenant's allowance forever

- **WHEN** an instance holding entries and bindings for a tenant at its configured bound is lost
- **THEN** within a bounded time those entries and bindings cease to be counted against that tenant
- **AND** a new registration and a new binding for that tenant are admitted without operator action

#### Scenario: A degraded-accounting refusal names that condition

- **WHEN** a registration is refused because the admitting instance could not account the tenant's total across the installation
- **THEN** the reason distinguishes that condition from the tenant having reached the configured bound
- **AND** the condition is observable to an operator while it holds

#### Scenario: One tenant cannot exhaust another

- **WHEN** one tenant reaches its registration bound
- **THEN** another tenant can still register sidecars
- **AND** requests for the other tenant's mounts continue to be served

#### Scenario: Capacity is released on departure

- **WHEN** an entry counted against a bound becomes ineligible
- **THEN** the capacity it occupied is released
- **AND** a subsequent registration for that mount succeeds

### Requirement: The deployed contract-version and capability spread is observable

Because sidecars are upgraded by tenants rather than by the operator, the registry SHALL report the distribution of negotiated contract versions and of declared capabilities over all currently eligible entries, both installation-wide and per tenant. For any given contract version or capability, the registry SHALL identify the tenants and mounts whose eligible entries depend on it or lack it.

The report SHALL be derived from currently eligible entries only, and SHALL exclude entries that have become ineligible.

#### Scenario: Version spread is reported with its owners

- **WHEN** eligible entries of two tenants negotiated different contract versions
- **THEN** the report names both versions with a count for each
- **AND** it identifies which tenant holds entries at each version

#### Scenario: Retiring a version can be assessed before it is done

- **WHEN** an operator asks which eligible entries negotiated a given contract version
- **THEN** the entries and their tenants are reported
- **AND** when no eligible entry negotiated that version, the result is empty rather than absent

#### Scenario: Capability gaps name the entries that lack them

- **WHEN** an operator asks which eligible entries do not declare a given capability
- **THEN** those entries and their mounts are reported
- **AND** entries that do declare it are not reported

#### Scenario: Departed entries leave the spread

- **WHEN** the only eligible entry at a contract version becomes ineligible
- **THEN** the reported distribution no longer counts that version
- **AND** the count for the remaining versions is unchanged

### Requirement: The registry is inspectable while a tunnel is stuck

An operator SHALL be able to determine, for any mount, the entries currently eligible, the proxy instance holding each tunnel, each entry's negotiated contract version and declared capability set, the time since each last proved liveness, whether each is draining, and the number of exchanges currently in flight on each.

Every transition of an entry — becoming eligible, becoming ineligible, entering drain — SHALL be recorded with its reason. Reasons SHALL be drawn from a stable enumerated set rather than rendered from an internal value.

#### Scenario: A mount's serving set can be inspected

- **WHEN** an operator inspects a mount
- **THEN** each eligible entry is reported with its instance, contract version, capability set, drain state, in-flight exchange count, and time since it last proved liveness

#### Scenario: Transitions carry enumerated reasons

- **WHEN** an entry becomes ineligible
- **THEN** the recorded reason is drawn from an enumerated set
- **AND** it distinguishes a clean close, a liveness failure, an instance loss, a completed drain, and a drain deadline

#### Scenario: Inspection is possible while an exchange is in flight

- **WHEN** an exchange has been in flight for longer than a configured reporting threshold
- **THEN** the entry serving it can be identified
- **AND** that entry's instance and time since its last liveness proof can be retrieved

#### Scenario: Inspection does not depend on the stuck tunnel responding

- **WHEN** an entry has stopped producing liveness signals but has not yet reached its bound
- **THEN** its recorded state is still retrievable
- **AND** retrieving it does not require a response from that sidecar
