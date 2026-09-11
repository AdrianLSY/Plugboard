## Purpose

Defines what the proxy must do with a real client request and the real backend response that answers it: which deadlines apply to which phase of an exchange, how a response that never ends is admitted, carried and drained, how partial and conditional transfers are preserved, what the proxy is forbidden from altering, and where the line falls between a failure the proxy answers with its own error response and a failure it can only truncate. The tunnel representation of these messages is fixed by the wire contract and is taken as given here; this capability governs the conduct of the two ends that surround it — the proxy at the client edge, and the sidecar where it originates the request against the tenant's backend. Throughout this capability a route is a mount as defined by the mount-point capability, and the mount's own attributes carry the per-route values named here. Every obligation here is a property of one exchange, and the proxy is a multi-instance installation: the bounds, the phases, the causes and the fidelity rules below therefore hold per exchange at whichever instance admitted it, and hold unchanged when the instance that admitted an exchange is not the instance holding the tunnel it is dispatched to. Two identical requests SHALL NOT receive different fidelity, different bounds, or a different enumerated cause because they arrived at different instances; where an outcome does legitimately differ between instances, the only such difference is the reachability condition the requirement on tunnel availability below states.

## ADDED Requirements

### Requirement: The backend request is derived only from the mount remainder

That the origin dialled is taken only from configuration local to the sidecar and from nothing the proxy or a request supplies, that a remainder failing validation is rejected rather than repaired, that the query component is carried octet for octet, and that a backend redirection is relayed rather than followed, are the sidecar-program capability's rules and hold here as given; that capability owns them because the sidecar must apply them against a peer of any version, and this capability SHALL NOT restate them as a second set. What this capability adds is what the proxy may assume of the composition and what it must not.

The proxy SHALL compose the exchange it dispatches from the remainder the mount-point capability computed together with the method, field pairs, and body octets it received, and from nothing else. It SHALL NOT convey an origin, a host, a port, or a scheme intended to select a destination, SHALL NOT rely on any sidecar having accepted one, and SHALL NOT treat a request as unservable because the sidecar's configured origin is unknown to it. The proxy SHALL NOT assume that a remainder it considered acceptable will be accepted: a rejection arriving from the origin-facing side SHALL be attributed to it with the enumerated cause that side conveyed, and SHALL NOT be recorded as a backend connection failure or as a proxy defect.

The proxy SHALL NOT apply request processing of its own to a message it is forwarding beyond what edge hygiene enumerates, and SHALL NOT add a field to compensate for one the origin-facing side is expected to generate for its own hop.

#### Scenario: The proxy conveys no destination

- **WHEN** every field the proxy sets on a dispatched exchange is enumerated
- **THEN** none of them names an origin, host, port, or scheme intended to select a destination
- **AND** the exchange is dispatched without the proxy knowing the origin the sidecar will dial

#### Scenario: A rejected remainder is attributed to the side that rejected it

- **WHEN** the origin-facing side rejects a remainder the proxy considered acceptable
- **THEN** the recorded cause is the one that side conveyed
- **AND** it is distinguishable from a backend connection failure
- **AND** it is not recorded as a proxy defect

#### Scenario: A redirection is relayed to the client, not resolved

- **WHEN** a backend answers with a redirection status naming another location
- **THEN** the client receives that status and its fields, subject to mount-boundary rewriting
- **AND** the proxy issues no further exchange on account of it

#### Scenario: The proxy adds nothing to compensate

- **WHEN** a request whose media type a general-purpose body parser would ordinarily claim is dispatched
- **THEN** the field pairs the proxy conveys are those it received, less what edge hygiene removes
- **AND** the proxy adds no field on the origin-facing side's behalf

### Requirement: Timeout bounds are separate and independently configurable

The exchange is governed by a taxonomy of six separate bounds, and they are not all enforced in the same place. The proxy SHALL enforce, each configurable independently of the others: the time spent obtaining a usable tunnel to a sidecar serving the mount; the time from dispatch of the request head until the response head arrives; the time between successive deliveries of body octets in either direction, measured at its own hop; the total duration of the exchange; and the time allowed for the client's request header section to arrive at the edge.

The sixth — the time the origin-facing side spends establishing a connection to the backend — SHALL NOT be enforced by the proxy and SHALL NOT be conveyed to the origin-facing side as a value to apply. It is configured locally on the sidecar and enforced there, as the sidecar-program capability requires, because the proxy cannot reach the backend and a value it sent would be a value the sidecar's own configuration contradicts. What the proxy SHALL do with it is attribute it: the enumerated cause the origin-facing side conveys for an exceeded connect bound SHALL be recorded and reported as that condition, distinguishably from every bound the proxy enforces itself. The same division SHALL apply to any further bound only the origin-facing side can measure.

No bound SHALL be derived from, or substituted for, another, and a bound enforced at one hop SHALL NOT be treated as satisfying the corresponding bound at the other. The implementation SHALL NOT impose a fixed ceiling on the value an operator may configure for any bound the proxy enforces. A bound left unspecified SHALL be rejected at the point the configuration is loaded, and no route governed by that configuration SHALL serve traffic; an unspecified bound SHALL NOT be filled in with an implicit value.

#### Scenario: Bounds do not interact

- **WHEN** the total-duration bound for a route is raised
- **THEN** the time-to-first-byte bound for that route is unchanged
- **AND** the idle-between-octets bound for that route is unchanged

#### Scenario: No ceiling on a configured bound

- **WHEN** an operator configures a bound larger than any value the implementation ships with
- **THEN** that value is the bound in force
- **AND** it is not silently replaced with a smaller one

#### Scenario: Incomplete configuration is refused

- **WHEN** a timeout class is defined omitting one of the bounds the proxy enforces
- **THEN** the configuration is rejected when it is loaded
- **AND** the diagnostic names every bound that was omitted
- **AND** no route referencing that class serves traffic

#### Scenario: The connect bound is the origin-facing side's to enforce

- **WHEN** a timeout class is configured and an exchange is dispatched
- **THEN** no value the proxy sends states the time the origin-facing side may spend connecting to its backend
- **AND** the bound in force for that connection is the one configured on that side

#### Scenario: An exceeded connect bound is attributed, not enforced

- **WHEN** the origin-facing side conveys the enumerated cause for an exceeded backend-connect bound
- **THEN** the proxy records and reports that condition
- **AND** it is distinguishable from every bound the proxy enforces itself
- **AND** it is not reported as the tunnel bound or as the time-to-first-byte bound

#### Scenario: One bound is not used in place of another

- **WHEN** a response head has not arrived and the time-to-first-byte bound has not elapsed
- **THEN** the exchange is not ended even if the value configured as the idle bound has elapsed

### Requirement: Every route carries a timeout class, and one class permits an unbounded total

Each route SHALL be associated with exactly one timeout class, and the class SHALL determine every bound in force for exchanges on that route. At least one class SHALL permit an unbounded total duration, such that an exchange on that class is never ended because of elapsed wall-clock time alone. The unbounded total SHALL be expressible only as an explicit choice, never as the effect of omitting a value.

A route with no class SHALL be rejected when it is created rather than assigned an implicit one, and the rejection SHALL name what was omitted. Where more than one required value is omitted, the rejection SHALL name all of them rather than the first.

A change to a route's class SHALL apply to exchanges begun after the change and SHALL NOT alter the bounds in force for an exchange already in flight.

#### Scenario: Unbounded total class

- **WHEN** a route is assigned a class whose total duration is unbounded
- **AND** an exchange on that route continues past the largest total bound configured for any other class
- **THEN** the exchange remains open
- **AND** no failure is recorded for elapsed total time

#### Scenario: Bounded class ends a long exchange

- **WHEN** a route is assigned a class with a bounded total
- **AND** an exchange on that route exceeds it while still delivering octets within the idle bound
- **THEN** the exchange is ended
- **AND** the recorded cause names the total-duration bound

#### Scenario: Class change does not disturb an in-flight exchange

- **WHEN** an exchange is in flight on a route
- **AND** the route's timeout class is changed
- **THEN** the in-flight exchange continues under the bounds in force when it began
- **AND** the next exchange on that route uses the new bounds

#### Scenario: A route without a class is rejected, not defaulted

- **WHEN** a route is created without an explicit timeout class
- **THEN** the creation is rejected
- **AND** the rejection names the timeout class as the omitted value
- **AND** no exchange is served on that route

#### Scenario: Every omission is reported at once

- **WHEN** a route is created omitting more than one required value
- **THEN** the rejection names every omitted value
- **AND** an operator does not have to retry to discover the next one

#### Scenario: The class in force is retrievable

- **WHEN** an operator inspects a route that is serving traffic
- **THEN** the timeout class in force for that route is reported
- **AND** every bound that class determines is reported with it

### Requirement: Time to first byte is bounded separately from total duration

The proxy SHALL bound the interval between dispatching a request head toward a sidecar and receiving the corresponding response head. This bound SHALL be independent of the total-duration bound and SHALL cease to apply once the response head has been received.

Receipt of an interim response SHALL NOT satisfy this bound. An exchange whose response head is still outstanding SHALL NOT be ended for any reason attributable to elapsed body-idle time, because no body has begun.

#### Scenario: Head arrives within the bound, body stalls afterwards

- **WHEN** a response head arrives shortly before the time-to-first-byte bound elapses
- **AND** no body octets follow for longer than that bound
- **THEN** the exchange is not ended on account of the time-to-first-byte bound
- **AND** it is ended only if the idle-between-octets bound elapses

#### Scenario: Interim response does not stop the clock

- **WHEN** a backend emits an interim response and then withholds the final response head past the time-to-first-byte bound
- **THEN** the exchange is ended
- **AND** the recorded cause names the time-to-first-byte bound

#### Scenario: Bound is not the total

- **WHEN** a route's time-to-first-byte bound is shorter than its total-duration bound
- **AND** a response head arrives after the time-to-first-byte bound has elapsed
- **THEN** the exchange has already been ended
- **AND** the late response head is discarded rather than delivered

### Requirement: Idle between body octets is bounded, and the bound resets on delivery

The proxy SHALL bound the interval between successive deliveries of body octets, in each direction independently, and SHALL restart the interval whenever octets are delivered. Delivery of any non-empty group of octets SHALL restart it, regardless of how few octets the group contains.

This bound, and not the total-duration bound, SHALL be the mechanism by which a stalled but still-open exchange is ended.

#### Scenario: Periodic keepalive holds an exchange open indefinitely

- **WHEN** a backend emits a small group of octets at an interval shorter than the idle bound
- **AND** the route's class has an unbounded total
- **THEN** the exchange remains open for as long as the backend continues
- **AND** each group reaches the client

#### Scenario: Stall ends the exchange

- **WHEN** a backend delivers body octets and then delivers none for longer than the idle bound
- **THEN** the exchange is ended
- **AND** the recorded cause names the idle bound

#### Scenario: Idle applies to the request direction

- **WHEN** a client begins sending a request body and then sends no further octets for longer than the idle bound
- **THEN** the exchange is ended
- **AND** the recorded cause distinguishes a stalled request body from a stalled response body

#### Scenario: A single octet resets the interval

- **WHEN** a backend delivers one octet just before the idle bound would elapse
- **THEN** the interval restarts
- **AND** the exchange continues

### Requirement: The client request header section is bounded at the edge

The proxy SHALL bound the time allowed for a client to deliver a complete request header section, and SHALL bound the size of that header section. A request exceeding either bound SHALL be rejected at the edge without a mount being resolved and without any tunnel exchange being created.

This bound SHALL apply independently of every bound governing the forwarded exchange.

#### Scenario: Slow header section is rejected before routing

- **WHEN** a client opens a connection and sends its request header section more slowly than the header-read bound permits
- **THEN** the request is rejected
- **AND** no mount lookup is performed
- **AND** no exchange is created toward any sidecar

#### Scenario: Oversized header section is rejected

- **WHEN** a client sends a request header section larger than the configured bound
- **THEN** the request is rejected with a cause naming the header-section bound
- **AND** the rejection is distinguishable from a body-size rejection

#### Scenario: Header bound does not constrain the body

- **WHEN** a client delivers its header section promptly and then sends a body slowly but within the idle bound
- **THEN** the request proceeds
- **AND** the header-read bound plays no further part

### Requirement: Tunnel availability and origin connection are distinguishable failures

Eligibility to serve a mount is the registry's, and a sidecar is eligible only while its tunnel is established. The proxy SHALL distinguish, in the response it returns and in the record it keeps, between: no eligible sidecar entry existing anywhere in the installation for the mount; an eligible entry existing but held by an instance the admitting instance cannot reach, which the registry reports rather than selects; an eligible entry being selected but no usable path to its tunnel being obtained within the tunnel bound; and a sidecar reporting that it could not establish a connection to its backend, whether refused, unresolvable, or exceeding the connect bound that side enforces.

Where no eligible entry exists for the mount, the proxy SHALL fail immediately rather than waiting for the tunnel bound to elapse. It SHALL likewise fail immediately, rather than waiting for that bound, where the registry reports that every eligible entry is held by an instance it cannot reach. The tunnel bound SHALL apply only to obtaining a usable path to an entry the registry returned.

The client MAY observe the same status for the first two of these conditions; the enumerated cause recorded for the exchange SHALL differ, so that a tenant that has deployed no sidecar is never investigated as one whose sidecar is connected to an instance this one cannot reach.

#### Scenario: No eligible sidecar

- **WHEN** a request matches a mount for which the registry reports no eligible entry
- **THEN** the proxy responds immediately
- **AND** it does not wait for the tunnel bound
- **AND** the cause is distinguishable from a tunnel timeout

#### Scenario: Eligible but unreachable

- **WHEN** the registry returns an eligible entry and no usable path to its tunnel is obtained
- **THEN** the proxy responds once the tunnel bound elapses
- **AND** the cause names the tunnel bound
- **AND** it is distinguishable from no eligible entry existing

#### Scenario: Held by an unreachable instance is its own cause

- **WHEN** a request matches a mount whose only eligible entry is held by an instance the admitting instance cannot reach
- **THEN** the proxy responds immediately without waiting for the tunnel bound
- **AND** the recorded cause names the entry as existing but held by an unreachable instance
- **AND** that cause differs from the cause recorded when no eligible entry exists anywhere in the installation

#### Scenario: Backend refuses the sidecar's connection

- **WHEN** the sidecar cannot establish a connection to its backend
- **THEN** the proxy's response names an origin-connection failure
- **AND** it is distinguishable from a time-to-first-byte expiry, in which a connection was established but no response head followed

### Requirement: Every terminating condition is recorded with a distinct cause

Every condition that ends an exchange other than its ordinary completion SHALL produce a stable enumerated cause, drawn from a set the proxy defines, and SHALL be present in the record the proxy keeps for that exchange. This SHALL hold whether or not the proxy also generates a response, so that a truncated exchange is attributable.

No two of the bounds this capability defines SHALL share a cause with each other or with a non-timeout termination. The proxy SHALL NOT record a cause as a rendering of an internal value of its implementation language.

#### Scenario: Each bound yields its own cause

- **WHEN** each bound this capability defines is made to expire in turn under otherwise identical conditions
- **THEN** each expiry records a different enumerated cause
- **AND** no two of the recorded causes are equal

#### Scenario: A truncated exchange is still attributable

- **WHEN** an exchange is truncated after its response head was delivered and therefore carries no generated response
- **THEN** the record for that exchange still carries the enumerated cause
- **AND** the cause identifies the condition that ended it

#### Scenario: Client close is distinct from a bound expiry

- **WHEN** a client closes the connection during an exchange
- **THEN** the recorded cause is the client close
- **AND** it differs from the cause recorded for any bound expiry

#### Scenario: Cause is not a host-language rendering

- **WHEN** any exchange is ended by any of these conditions
- **THEN** the recorded cause is a value from the defined enumeration
- **AND** it does not contain a serialised internal error term

### Requirement: A response whose body never ends is carried indefinitely

The wire contract already requires incremental transfer without aggregation across the tunnel. This capability extends that obligation to the client edge: the proxy SHALL treat a response with no determinate end as an ordinary case rather than an error, and SHALL make each group of body octets observable at the client before the backend produces the next.

Such an exchange SHALL be terminated only by the client closing, the backend closing, the sidecar or tunnel being lost, a bound this capability defines being exceeded, or an operator-initiated drain. That list SHALL be exhaustive, and every termination SHALL be attributable to exactly one of its entries. An exchange SHALL NOT be terminated because a quantity of octets, a number of groups, or a period of elapsed total time has been reached on a class whose total is unbounded.

#### Scenario: Groups are observable at the client as produced

- **WHEN** a backend produces a group of octets, waits, then produces another
- **THEN** the client observes the first group before the second is produced
- **AND** the second group is delivered when it is produced

#### Scenario: Endless response outlives the ordinary total bound

- **WHEN** a response on an unbounded-total class continues past the total bound configured for the ordinary class
- **THEN** the exchange remains open
- **AND** octets continue to be delivered

#### Scenario: Client close ends the exchange without an error response

- **WHEN** a client closes the connection during an endless response
- **THEN** the exchange ends
- **AND** the proxy generates no error response
- **AND** the termination is recorded as a client close rather than a failure

#### Scenario: A slow client is not itself a termination

- **WHEN** a client consumes an endless response more slowly than the backend produces it
- **AND** the backend continues to produce within the idle bound
- **THEN** the exchange is not ended on account of the client being slow
- **AND** any later termination is attributable to one of the enumerated conditions

### Requirement: Long-lived exchanges are admitted against occupancy, not arrival rate

An exchange on a class whose total is unbounded, or whose time to first byte is long by design, occupies a connection and a share of the proxy's memory for its whole lifetime. The proxy SHALL therefore admit such an exchange against configurable bounds on the number of exchanges concurrently in flight and on the octets in flight for them, evaluated per tenant. A bound on the rate at which requests arrive SHALL NOT be accepted as satisfying this requirement.

An admitted exchange SHALL count against those bounds until it terminates, and its share SHALL be released on termination whatever the cause. An exchange refused by admission SHALL be refused before any part of it is dispatched to a sidecar, and with a cause distinct from every timeout and size cause.

The dimensions these bounds are drawn on are the per-tenant dimensions the tenancy capability enumerates; this capability enforces them at admission for request/response exchanges and SHALL NOT define a parallel set of its own. One tenant's occupancy SHALL NOT reduce the admission available to another tenant.

#### Scenario: Concurrency bound refuses within the arrival-rate allowance

- **WHEN** a tenant opens exchanges on an unbounded-total class up to its concurrency bound, at a rate within any configured arrival-rate allowance
- **AND** one further such request arrives
- **THEN** that request is refused
- **AND** the refusal names the concurrency bound rather than a rate limit
- **AND** nothing is dispatched to a sidecar for it

#### Scenario: Occupancy is released on termination

- **WHEN** a tenant is at its concurrency bound and one of its in-flight exchanges terminates
- **THEN** a subsequent request from that tenant is admitted
- **AND** this holds whether the terminated exchange completed, was closed by the client, or was ended by a bound

#### Scenario: Octets in flight are bounded separately from count

- **WHEN** a tenant's in-flight exchanges together hold octets up to the in-flight-octets bound while remaining under the concurrency bound
- **THEN** a further request is refused
- **AND** the refusal names the in-flight-octets bound

#### Scenario: One tenant's occupancy does not consume another's

- **WHEN** one tenant is at every admission bound it has
- **AND** a request arrives for a mount belonging to a different tenant
- **THEN** that request is admitted
- **AND** its admission decision does not reference the first tenant's occupancy

### Requirement: Shutdown drains long-lived exchanges rather than severing them at once

On an operator-initiated shutdown or reload, the proxy SHALL stop admitting new exchanges, SHALL allow exchanges already in flight to continue for a configurable drain interval, and SHALL terminate any that remain when the interval elapses. That interval is the one the single withdrawal lifecycle the sidecar-registry capability owns configures, applied to request/response exchanges; this capability SHALL NOT introduce a second ordering of phases or a second deadline. Termination during drain SHALL follow the commit-point rule, so an exchange whose head was already delivered is truncated rather than answered with a generated error.

Terminations of long-lived exchanges during a drain SHALL be distributed across an interval rather than issued at a single instant, so that the clients of one proxy do not all reconnect simultaneously. The proxy SHALL make the count of exchanges still in flight observable throughout the drain.

#### Scenario: In-flight short exchange completes during drain

- **WHEN** a drain begins while an ordinary exchange is in flight
- **AND** that exchange would complete well within the drain interval
- **THEN** it completes normally
- **AND** the client receives no error

#### Scenario: New exchanges are refused once draining

- **WHEN** a drain has begun
- **AND** a request arrives for a mount
- **THEN** it is refused with a cause naming the drain
- **AND** no exchange is created toward any sidecar
- **AND** the count of exchanges still in flight is retrievable by an operator while the drain continues

#### Scenario: Remaining long-lived exchanges are spread, not simultaneous

- **WHEN** many exchanges on an unbounded-total class are still in flight when the drain interval elapses
- **THEN** their terminations are distributed across an interval
- **AND** they do not all occur within a single instant

#### Scenario: Drain is bounded

- **WHEN** an exchange on an unbounded-total class is still in flight after the drain interval has elapsed
- **THEN** it is terminated
- **AND** the shutdown does not wait for it indefinitely

#### Scenario: Drain termination after commit truncates

- **WHEN** the drain interval elapses during an exchange whose response head has already been delivered
- **THEN** the client observes a truncated response
- **AND** no generated error response is appended
- **AND** the record names the drain as the cause

### Requirement: A deliberately delayed response is not a failure

The proxy SHALL support routes on which the backend holds a request open before answering, with a time-to-first-byte bound long enough to accommodate the intended hold. A long interval before the response head arrives SHALL NOT, by itself, be treated as a failure.

Where such a request is abandoned by the client before the backend answers, the proxy SHALL end the exchange without generating an error response to any party.

#### Scenario: Held-open request succeeds

- **WHEN** a route's class permits a long time to first byte
- **AND** a backend holds a request open well beyond the ordinary class's time-to-first-byte bound before responding
- **THEN** the response is delivered to the client
- **AND** no failure is recorded

#### Scenario: The class, not the protocol, decides

- **WHEN** the same request is issued to a route on the ordinary class
- **THEN** it fails with the time-to-first-byte bound named
- **AND** the outcome differs from the long-hold class solely because of the class

#### Scenario: Client abandons a held-open request

- **WHEN** a client disconnects while its request is being held open by the backend
- **THEN** the exchange ends
- **AND** no error response is generated
- **AND** the termination is recorded as a client close

#### Scenario: Long hold still has a total

- **WHEN** a long-hold class has a bounded total and a backend holds a request past it
- **THEN** the exchange is ended
- **AND** the cause names the total bound rather than the time-to-first-byte bound

### Requirement: A stated expectation is answered by the backend, not by the edge

The wire contract already permits a request head to cross the tunnel before any of its body octets exist, and fixes what the two ends do on the stream once a counterpart confirms or rejects an expectation. This capability governs the client edge around it: which party decides, what the client observes, and what is refused when no party can decide. Where a client states an expectation that the backend confirm its willingness to receive the body, the proxy SHALL dispatch the request head before reading any body octet from the client, and SHALL leave the decision to the backend: the interim confirmation or the final response the client observes SHALL be the one the backend produced, and the proxy SHALL NOT generate a confirmation of its own on any party's behalf. Dispatching the head first SHALL NOT defer or exempt a check that precedes dispatch — the header-section bounds, admission, and a declared body length already exceeding the request-body bound are decided at the edge as those requirements state, before any head is dispatched.

A recognised expectation is an ordinary end-to-end field. The proxy SHALL carry it among the request's field pairs with its value unaltered and SHALL NOT consume it at the edge; whether a field is removed as connection-scoped is the closed enumeration edge hygiene owns, and this capability SHALL NOT maintain a second one. The proxy SHALL NOT place an expectation on an exchange whose client stated none, including over a client protocol that defines no such mechanism, and the absence of a construct that protocol does not define SHALL NOT be treated as a fault.

Interim responses are an optional capability of the wire contract. Where a client states the expectation and no eligible sidecar for the matched mount, anywhere in the installation, declared interim responses, the proxy SHALL refuse the request before dispatching it, naming interim responses as the capability no eligible sidecar declared; it SHALL NOT dispatch the request and rely on the client abandoning the wait. That refusal SHALL be decided on the expectation the client stated and not on whether the client goes on to wait, so that the outcome does not vary with client timing.

An expectation whose value the proxy does not recognise SHALL likewise be refused before dispatch, with the expectation-failed status and with an enumerated cause distinct from the undeclared-capability refusal and from every other cause this capability defines. It SHALL NOT be forwarded to a sidecar, and the request SHALL NOT be served as though the expectation had not been stated.

Where a client states the expectation and begins sending its body without waiting, the exchange SHALL proceed: the octets SHALL be forwarded as they arrive, SHALL NOT be discarded, and SHALL NOT be withheld pending a confirmation that may never come; the unsolicited body SHALL NOT be treated as a violation of the expectation or as a reason to fail the exchange. A confirmation the backend produces afterwards SHALL still reach the client, and no octet already forwarded SHALL be sent a second time.

#### Scenario: The confirmation the client receives is the backend's

- **WHEN** a client states the continue expectation on a mount whose eligible sidecar declared interim responses
- **THEN** the request head reaches the backend before any body octet does
- **AND** the client observes no confirmation before the backend produces one
- **AND** the interim response the client receives is the one the backend produced

#### Scenario: The expectation reaches the origin unaltered

- **WHEN** a request stating a recognised expectation is dispatched
- **THEN** the origin receives that expectation among the request's field pairs with its value unaltered
- **AND** a request whose client stated none reaches the origin carrying none
- **AND** a request arriving over a client protocol that defines no expectation mechanism likewise carries none, and is not refused for the absence of the construct

#### Scenario: Dispatching the head first exempts no edge check

- **WHEN** a client states the expectation on a request declaring a body length larger than the route's request-body bound
- **THEN** the request is refused before any head is dispatched
- **AND** no exchange is created toward any sidecar
- **AND** the cause names the body-size bound rather than the expectation

#### Scenario: An expectation no sidecar declared is refused before dispatch

- **WHEN** a client states the expectation for a mount for which no eligible sidecar in the installation declared interim responses
- **THEN** the request is refused
- **AND** the refusal names interim responses as the capability no eligible sidecar declared
- **AND** no exchange is created toward any sidecar
- **AND** a client that states the same expectation and begins sending its body immediately receives the same refusal

#### Scenario: An unrecognised expectation is refused, not relayed

- **WHEN** a client states an expectation whose value the proxy does not recognise
- **THEN** the request is refused with the expectation-failed status
- **AND** the recorded cause differs from the one recorded when no eligible sidecar declared interim responses
- **AND** no exchange is created toward any sidecar
- **AND** the request is not served as though the expectation had not been stated

#### Scenario: A client that does not wait is served

- **WHEN** a client states the expectation and begins sending its body without waiting for a confirmation
- **THEN** the origin receives the complete body
- **AND** no octet is discarded and none is withheld awaiting a confirmation
- **AND** the exchange is not failed on account of the client not having waited
- **AND** a confirmation produced afterwards still reaches the client, and no octet is sent a second time

### Requirement: A pending expectation transfers no body octets and is not a commit

Where the backend answers the expectation with a final response instead of a confirmation, the client SHALL observe the status and the fields the origin produced, and the proxy SHALL NOT substitute a response of its own. Where the client was still waiting, no request body octet SHALL have reached the origin: a rejection SHALL NOT be preceded by a transfer of the body it declines.

The proxy SHALL deliver that response to the client in full before ending the client's connection on account of it. Where the client's negotiated protocol delimits messages such that the unsent remainder of the request body would have to be consumed before that connection could carry another message, the proxy SHALL close the connection rather than read the remainder in order to keep it reusable, and SHALL NOT forward the remainder to a sidecar or to a backend.

While neither a confirmation nor a final response has arrived, the interval is governed by the time-to-first-byte bound of the route's timeout class. The taxonomy of bounds this capability defines SHALL NOT be extended with one peculiar to expectations, and receipt of the confirmation SHALL NOT satisfy the time-to-first-byte bound, as the requirement on that bound already states. A client withholding its body while awaiting the confirmation SHALL NOT be recorded as a stalled request body: the idle-between-octets bound in the request direction begins at the first body octet.

A confirmation is an interim response and not a response head, so its delivery to the client SHALL NOT be the commit point. An exchange failing after a confirmation has reached the client but before any part of a response head has SHALL be answered with a proxy-generated error response carrying the enumerated cause, rather than truncated; where the failure is the time-to-first-byte bound elapsing with neither answer, that cause SHALL name that bound.

#### Scenario: A rejection transfers no body octets

- **WHEN** a client states the expectation for a body within the route's request-body bound and waits
- **AND** the backend answers with a final rejection instead of a confirmation
- **THEN** the client receives that status and its fields as the origin produced them
- **AND** the origin observed no request body octet
- **AND** no proxy-generated response is substituted for the backend's

#### Scenario: The unsent remainder is not read to keep the connection

- **WHEN** a rejection is delivered while the client's request body remains unsent, over a client protocol whose message boundaries depend on that body being consumed
- **THEN** the client receives that response in full
- **AND** the connection is then closed rather than reused for a further message
- **AND** the unsent octets reach no sidecar and no backend

#### Scenario: Waiting is not a stalled request body

- **WHEN** a client withholds its request body awaiting the confirmation for longer than the idle-between-octets bound
- **THEN** the exchange is not ended on account of that bound
- **AND** it is ended only if the time-to-first-byte bound elapses

#### Scenario: Neither answer within the bound

- **WHEN** a backend produces neither a confirmation nor a final response
- **THEN** the exchange is not ended before the time-to-first-byte bound of the route's timeout class elapses
- **AND** it is ended when that bound elapses, with the recorded cause naming that bound
- **AND** the client receives a proxy-generated error response rather than a truncated one

#### Scenario: A delivered confirmation is not a commit

- **WHEN** a backend's confirmation has been delivered to the client and the exchange then fails before any part of a response head has been delivered
- **THEN** the client receives a proxy-generated error response
- **AND** the response is not truncated after the confirmation
- **AND** the record states that the failure occurred before commit

### Requirement: Range and partial-content exchanges are carried unaltered

The proxy SHALL carry range requests, conditional-range requests, and their responses without alteration. It SHALL NOT add, remove, narrow, widen, coalesce, or reorder requested ranges, and SHALL NOT change the status the origin chose between a complete and a partial response.

A partial response SHALL be delivered with its range metadata intact, including a response composed of multiple parts. An open-ended range into a resource larger than available memory SHALL be carried without any hop holding the whole resource.

#### Scenario: Single range is relayed as chosen by the origin

- **WHEN** a client requests a byte range and the origin answers with a partial-content response
- **THEN** the client receives that partial status
- **AND** the range metadata is unaltered
- **AND** the body octets are exactly those the origin produced

#### Scenario: Origin declines the range

- **WHEN** a client requests a byte range and the origin answers with the complete representation instead
- **THEN** the client receives the complete representation and its status
- **AND** the proxy does not convert it into a partial response

#### Scenario: Multi-part range response survives

- **WHEN** an origin answers a multi-range request with a multi-part response
- **THEN** the client receives the body byte-identically, including part boundaries and per-part headers
- **AND** the proxy does not reassemble the parts

#### Scenario: Conditional range is decided by the origin

- **WHEN** a client sends a range request qualified by a validator
- **THEN** the validator reaches the origin unaltered
- **AND** whichever of the partial or complete responses the origin returns is relayed

#### Scenario: Open-ended range into a large resource

- **WHEN** a client requests an open-ended range beginning partway into a resource larger than the memory available to any hop
- **THEN** the response is delivered incrementally
- **AND** no hop holds the whole resource
- **AND** the exchange is subject to the idle bound rather than a bound on total octets held

#### Scenario: An unsatisfiable range is the origin's answer, not the proxy's

- **WHEN** a client requests a range the origin considers unsatisfiable and the origin answers with the corresponding status
- **THEN** the client receives that status and the origin's range metadata
- **AND** the proxy does not substitute a complete representation, a partial response, or a gateway error

### Requirement: Conditional requests are answered by the origin

The proxy SHALL carry conditional request fields to the origin unaltered and SHALL NOT evaluate a condition itself. A not-modified response SHALL be delivered with its header fields and validators intact and with no body, and SHALL be treated as a completed exchange at the point its head is delivered.

#### Scenario: Validator reaches the origin

- **WHEN** a client sends a conditional request carrying a validator
- **THEN** the origin receives that validator unaltered
- **AND** the proxy does not answer the request from any state of its own

#### Scenario: Not-modified completes at the head

- **WHEN** an origin answers with a not-modified response
- **THEN** the client receives that status and its header fields
- **AND** no body octets are delivered
- **AND** the exchange completes without waiting for body octets that will not arrive

#### Scenario: Failed condition is relayed

- **WHEN** an origin answers a conditional request with a precondition-failed status
- **THEN** the client receives that status
- **AND** the proxy does not substitute a gateway error

### Requirement: Content codings are carried without alteration

The proxy SHALL NOT decode, re-encode, or change the coding of a body it is carrying, and SHALL NOT add or remove a coding. Coding negotiation is between the client and the origin: the proxy SHALL carry the client's stated coding preferences to the origin unaltered, and carry the coding the origin selected back unaltered.

This obligation SHALL hold even where the proxy is capable of the coding and even where the client did not state that it accepts it.

#### Scenario: Encoded body passes through untouched

- **WHEN** an origin returns a body under a content coding
- **THEN** the client receives the coded octets byte-identically
- **AND** the declared coding is unchanged

#### Scenario: Proxy adds no coding of its own

- **WHEN** an origin returns an uncoded body
- **THEN** the client receives an uncoded body
- **AND** the proxy does not apply a coding the origin did not

#### Scenario: Client preferences reach the origin

- **WHEN** a client states which codings it accepts
- **THEN** the origin receives that statement unaltered
- **AND** the origin's selection is what the client observes

#### Scenario: Unrecognised coding is still carried

- **WHEN** an origin returns a body under a coding the proxy does not recognise
- **THEN** the body and its declared coding are delivered unaltered
- **AND** the proxy does not fail the exchange on account of the coding

#### Scenario: A coding the proxy could decode is still not decoded

- **WHEN** an origin returns a body under a coding the client did not state that it accepts
- **AND** the proxy is capable of decoding that coding
- **THEN** the client receives the coded octets and the declared coding unaltered
- **AND** the proxy neither decodes the body nor rejects the response on the client's behalf

### Requirement: Body size bounds are enforced without materialising the body

The proxy SHALL enforce configurable bounds on the total octets of a request body and of a response body, resolvable per route. Enforcement SHALL be by a running total of octets already transferred and SHALL NOT require any hop to hold the body in order to evaluate the bound.

A bound SHALL apply to a body whose length was never declared. Where a declared length already exceeds the bound, the proxy SHALL refuse before transferring any body octets. Where the bound is crossed during transfer, the proxy SHALL stop the transfer at the point the bound is crossed, including when the crossing occurs in the final group of octets.

#### Scenario: Undeclared length is still bounded

- **WHEN** a client sends a request body of undeclared length exceeding the request-body bound
- **THEN** the request is refused with a cause naming the body-size bound
- **AND** the proxy did not hold the body in order to decide

#### Scenario: Declared length over the bound is refused up front

- **WHEN** a client sends a request declaring a body length larger than the bound
- **THEN** the request is refused before any body octet is forwarded
- **AND** no exchange is created toward the sidecar

#### Scenario: Crossing in the final group is still caught

- **WHEN** a body crosses the bound within the last group of octets before it ends
- **THEN** the bound is enforced
- **AND** the exchange does not complete successfully

#### Scenario: Streaming class is bounded by octets, not by buffering

- **WHEN** a route on a streaming class carries a response many times larger than the memory available to any hop, under a response-body bound larger than the response
- **THEN** the response completes
- **AND** the running total is what enforces the bound, not a materialised copy of the body

#### Scenario: Response bound crossed after the head was delivered

- **WHEN** a response body crosses the response-body bound after its head has already reached the client
- **THEN** the client observes a truncated response
- **AND** no error response is substituted
- **AND** the record names the body-size bound as the cause

### Requirement: Responses defined to carry no body complete at the head

The proxy SHALL complete an exchange whose response is defined to have no body upon delivery of the response head, without waiting for body octets and without applying the idle-between-octets bound to a body that will not exist. The proxy SHALL NOT synthesise a body for such a response.

Where the origin declares the length the representation would have had, the proxy SHALL relay that declaration rather than treating the absence of a body as an inconsistency to correct or as a reason to fail the exchange. Generation of the framing the client's own connection requires is owned at the edge and is not in tension with this: the declared representation length is carried, the per-connection framing is not.

#### Scenario: HEAD response carries its declared length and no body

- **WHEN** a client issues a `HEAD` request and the origin answers with header fields including a non-zero declared body length
- **THEN** the client receives those header fields
- **AND** the client receives no body octets
- **AND** the exchange completes rather than stalling until a bound expires

#### Scenario: No-content response completes immediately

- **WHEN** an origin answers with a status defined to have no body
- **THEN** the exchange completes at the head
- **AND** no idle bound is applied

#### Scenario: No body is invented

- **WHEN** an origin answers with a head and no body on a status that permits a body
- **THEN** the client receives an empty body
- **AND** the proxy does not insert content of its own

### Requirement: Trailers reaching the edge are emitted or the request is refused

The wire contract carries a trailer section distinctly from the header section. At the client edge the proxy SHALL emit a trailer section it receives to the client wherever the client's negotiated protocol can express one, preserving the fields and their order.

Where the client's negotiated protocol cannot express a trailer section and the matched route's class declares that its responses carry one, the proxy SHALL refuse the request before dispatching it, naming trailer emission as the unavailable behaviour. The proxy SHALL NOT accept such a request and then discard the trailers, and SHALL NOT promote a trailer field into the response header section.

A route whose class declares no trailers may nevertheless be answered by a backend that emits one, and by then the response head has been delivered and the commit point has passed. In that case the proxy SHALL NOT fold the trailer fields into the header section, SHALL NOT append them to the body, and SHALL NOT generate a response of its own. It SHALL truncate the response as the commit-point rule requires and record the cause as trailers the client's protocol could not express, distinguishably from every other truncation cause, so that a route whose class is misdeclared is diagnosable rather than silently lossy.

#### Scenario: Trailers are emitted where the client protocol allows

- **WHEN** a backend emits a body followed by a trailer section
- **AND** the client's negotiated protocol can carry trailers
- **THEN** the client receives those trailer fields as trailers
- **AND** they do not appear among the response header fields

#### Scenario: A client that cannot receive trailers is refused, not silently served

- **WHEN** a request whose response is known to require trailers arrives over a client protocol that cannot express them
- **THEN** the request is refused
- **AND** the refusal names trailer emission as the unavailable behaviour
- **AND** the request is not dispatched to a sidecar

#### Scenario: Unexpected trailers after commit truncate rather than fold

- **WHEN** a route whose class declares no trailers is answered by a backend that emits a trailer section, over a client protocol that cannot express one
- **THEN** no trailer field appears among the response header fields or in the body
- **AND** the client observes a truncated response
- **AND** the recorded cause names trailers the client's protocol could not express, distinct from every other truncation cause

#### Scenario: Trailers are never folded into headers

- **WHEN** a trailer section reaches the edge
- **THEN** no field from it appears in the response header section
- **AND** no header field is replaced by a same-named trailer field

### Requirement: The response head is the commit point

Where an exchange fails before any part of a response head has been delivered to the client, the proxy SHALL answer with a response it generates itself. Once any part of a response head has been delivered to the client, the proxy SHALL NOT generate a response of its own for that exchange: it SHALL end the exchange so that the client detects an incomplete response, and SHALL NOT append content, a status, or a diagnostic to the partial response.

Every failure of an exchange SHALL resolve to exactly one of these two outcomes, and which one applied SHALL be recorded.

#### Scenario: Failure before commit becomes an error response

- **WHEN** the sidecar becomes unreachable before any response head has been delivered
- **THEN** the client receives a proxy-generated error response
- **AND** its cause names the failure

#### Scenario: Failure after commit truncates

- **WHEN** the backend fails after its response head has been delivered to the client
- **THEN** the client receives no additional status and no error content
- **AND** the client detects that the response is incomplete against the length or framing the head declared
- **AND** the record states that the failure occurred after commit

#### Scenario: The head alone is a commit

- **WHEN** a failure occurs after the response head has been delivered but before any body octet has been
- **THEN** the outcome is truncation, not a generated error response

#### Scenario: A bound expiring after commit truncates

- **WHEN** the idle bound expires during a response whose head has already been delivered
- **THEN** the client observes a truncated response
- **AND** no gateway-timeout response is generated
- **AND** the record names the idle bound

#### Scenario: Exactly one outcome

- **WHEN** any exchange fails
- **THEN** exactly one of a generated error response or a truncation is produced
- **AND** the proxy never attempts both

### Requirement: Proxy-generated error responses are distinguishable per cause

Where the proxy answers a failure with a response of its own, that response SHALL carry a stable enumerated cause distinguishing at minimum: no mount matched the request; no eligible sidecar exists for the matched mount; no usable path to an eligible sidecar's tunnel was obtained; no eligible sidecar declared a capability the request requires; trailer emission the client's protocol cannot express; incremental transfer no eligible sidecar declared; the backend could not be connected to; each timeout bound separately; each admission bound separately; the request header-section bound; the request-body size bound; the proxy draining; and a backend failure occurring before commit.

The cause SHALL be available in a machine-readable representation regardless of the media types the mount otherwise deals in, and SHALL NOT depend on content negotiation succeeding. Each response SHALL carry the correlation identifier assigned to the exchange, and that identifier SHALL be the one under which the exchange's records are retrievable.

#### Scenario: Causes do not collapse

- **WHEN** each enumerated cause is provoked in turn
- **THEN** each produces a distinct enumerated cause value
- **AND** no two distinct causes are reported as the same value

#### Scenario: Missing sidecar differs from unreachable backend

- **WHEN** no eligible sidecar exists for a mount
- **AND** separately, an eligible sidecar is serving it but its backend refuses connections
- **THEN** the two responses carry different enumerated causes
- **AND** each cause is present in the response without reference to the record

#### Scenario: Machine-readable regardless of the mount

- **WHEN** the proxy generates an error for a request to a mount that serves only binary media
- **THEN** the cause is available in a machine-readable form
- **AND** the proxy does not fail to produce an error because no acceptable representation was negotiated

#### Scenario: Error carries a correlation identifier

- **WHEN** the proxy generates an error response
- **THEN** it carries the exchange's correlation identifier
- **AND** the same identifier appears in the record kept for that exchange
- **AND** it is not a value the client supplied

### Requirement: Reflected input in generated errors is escaped and bounded

Where a proxy-generated error response reflects any value taken from the request — a path, a host, a query, a header field value, or any part of one — every such value SHALL be escaped for the representation it is placed into, such that no reflected value can be interpreted as markup, script, or structure by a client rendering the response. Escaping SHALL be applied to every reflected value, including values that were assembled or formatted before reflection.

Each reflected value SHALL be truncated to a configured bound. The proxy SHALL NOT reflect credential-bearing request fields, nor internal addresses or identifiers of the tenant's infrastructure.

#### Scenario: Markup in a path is rendered as text

- **WHEN** a client requests a path containing markup that would execute if rendered
- **AND** the proxy generates a not-found response reflecting the path
- **THEN** the response contains the escaped form of that text
- **AND** it does not contain the executable form

#### Scenario: An already-escaped value is escaped again, not passed through

- **WHEN** a reflected value already contains the escaped form of markup
- **THEN** the delivered response contains the escape-introducing character of that sequence in its own escaped form
- **AND** rendering the response displays the escape sequence literally rather than the markup it would otherwise decode to

#### Scenario: Formatted detail is escaped too

- **WHEN** a generated error reflects a value that was formatted into a larger diagnostic string
- **THEN** the formatted diagnostic is escaped in full
- **AND** no reflected component escapes the escaping

#### Scenario: Long reflected value is truncated

- **WHEN** a client sends a very long path and the proxy generates an error reflecting it
- **THEN** the reflected value is truncated to the configured bound
- **AND** the truncation is visible rather than silent

#### Scenario: Credentials are not reflected

- **WHEN** a request carrying an authorization or cookie field provokes a generated error
- **THEN** no part of those field values appears in the response

### Requirement: The proxy stores no response and serves none from store

The proxy SHALL NOT store a response, or any part of one, for reuse by a later request, and SHALL NOT answer any request from stored content. Every request matching a mount SHALL result in an exchange with a sidecar.

Cache-directive and validator fields SHALL be carried unaltered in both directions so that the client and the origin remain the only parties to the caching relationship.

#### Scenario: Identical requests both reach the origin

- **WHEN** two identical requests are made in succession to a cacheable resource
- **THEN** the origin receives both
- **AND** neither is answered from proxy-held content

#### Scenario: Cache directives are relayed, not consumed

- **WHEN** an origin returns a response bearing cache directives
- **THEN** the client receives those directives unaltered
- **AND** the proxy retains no copy of the response

#### Scenario: Partial content is never synthesised

- **WHEN** a client requests a range of a resource the proxy has previously carried in full
- **THEN** the range request is forwarded
- **AND** the response is produced by the origin, not derived by the proxy

### Requirement: The proxy performs no body transformation

The proxy SHALL deliver response body octets exactly as produced by the origin and request body octets exactly as produced by the client. It SHALL NOT transcode, normalise, minify, pretty-print, validate, or replace any octet, and SHALL NOT substitute its own content for a body the origin produced.

The sole exception is mount-boundary rewriting, which is owned by another capability, is inert unless explicitly configured for a route and a content type, and SHALL NOT apply to any body outside that configuration.

#### Scenario: Backend error body is relayed, not replaced

- **WHEN** an origin returns a failure status with a body of its own
- **THEN** the client receives that status and that body
- **AND** the proxy does not substitute a generated error page

#### Scenario: An in-body trailer convention is not interpreted

- **WHEN** an origin returns a body whose final octets encode a trailer section inside the body, as a browser-oriented framing does
- **THEN** the client receives those octets as part of the body
- **AND** the proxy neither lifts them into the response header section nor removes them from the body

#### Scenario: Rewriting is inert by default

- **WHEN** a route has no mount-boundary rewriting configured
- **THEN** every response body is delivered byte-identically
- **AND** no absolute reference in a body is altered

#### Scenario: Rewriting does not spread to unconfigured content types

- **WHEN** mount-boundary rewriting is configured for one content type
- **AND** a response of a different content type is carried
- **THEN** that response body is delivered byte-identically

### Requirement: A forwarded exchange is never replayed

Once the request head of an exchange has been delivered to a sidecar, the proxy SHALL NOT deliver that exchange to any sidecar again, whether after a tunnel loss, a sidecar disconnect, a reset, or a bound expiry. Selecting a different sidecar is permitted only while no part of the request has been delivered to any sidecar.

The method of the request SHALL NOT be used to decide whether an exchange may be replayed, because the proxy cannot know whether the backend treats it as idempotent.

#### Scenario: Tunnel loss after dispatch does not resend

- **WHEN** the tunnel is lost after the request head has been delivered to a sidecar
- **THEN** the exchange fails or truncates according to the commit point
- **AND** the request is not delivered to another sidecar

#### Scenario: Failover before dispatch is permitted

- **WHEN** the selected sidecar becomes unavailable before any part of the request has been delivered to it
- **THEN** the proxy may select another sidecar serving the mount
- **AND** the backend of the first sidecar receives nothing

#### Scenario: Method does not authorise a replay

- **WHEN** an exchange using a method commonly treated as idempotent fails after dispatch
- **THEN** it is not replayed
- **AND** the outcome is identical to that of a method not treated as idempotent

#### Scenario: Exactly one backend request per dispatched exchange

- **WHEN** a backend counts the requests it receives for one client request that was dispatched and then failed
- **THEN** the count is exactly one
- **AND** the count is unchanged by a tunnel reconnect occurring during the failure
