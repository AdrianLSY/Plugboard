## Purpose

Defines the isolation promise the product is sold on: one tenant cannot observe, affect, or degrade another. It governs how every resource is attributed to a tenancy, how reads are scoped and mutations authorized, what the role model grants and withholds, the per-tenant resource ceilings that keep one tenant's load off another's latency, the containment of faults, and the audit trail that makes all of it reviewable. Isolation here is a property of the data model and of the contract of every operation, not a check that callers are trusted to remember. Three terms are fixed for the whole system here: a *tenancy* is the same boundary other capabilities call a *tenant*; a *routing entry* is a node in the path hierarchy the mount-point capability defines, whether or not that node is a mount point; and an *instance* is one running process of a deployable — what the listener capability calls an *accepting instance* — while the *installation* is the whole set of instances under one operator's configuration. The word *node*, reserved above for the path hierarchy, is therefore never used for a running process by any capability: a running proxy process is an *instance*, or a *proxy instance* where it must be told apart from a sidecar instance or an instance of the client-facing terminator. Because the proxy is a multi-instance installation and a tenant's traffic arrives at whichever instance the load balancer chose, this capability also settles what a per-tenant bound means across instances: a ceiling enforced once per instance would grant a tenant as many allowances as there are instances, which would falsify the promise stated above.

## ADDED Requirements

### Requirement: Every resource belongs to exactly one tenancy

Every routing entry, credential, hostname claim, sidecar registration, membership grant, audit record, log record, and metric sample SHALL be attributed to exactly one tenancy at the moment it is created. A resource SHALL NOT exist without a tenancy attribution, and it SHALL NOT be possible to create one in a state where the attribution is absent, empty, or inferred later.

The attribution SHALL be immutable. No operation SHALL move a resource from one tenancy to another; transferring ownership of a subject is expressed as removing it from one tenancy and creating a new resource in another, so that the audit trail records both.

#### Scenario: Creation without an attribution is impossible

- **WHEN** a routing entry, credential, hostname claim, or sidecar registration is created
- **THEN** the resulting resource carries exactly one tenancy attribution
- **AND** an attempt to persist such a resource with an absent or empty attribution is rejected at the point of persistence, independently of the code path that attempted it

#### Scenario: Attribution cannot be reassigned

- **WHEN** any principal, including one holding the highest role in both tenancies, attempts to change the tenancy attribution of an existing resource
- **THEN** the attempt is refused
- **AND** the resource's attribution is unchanged

#### Scenario: Derived records inherit the attribution of their subject

- **WHEN** an audit record, log record, or metric sample is produced while serving a request for a mount
- **THEN** it carries the tenancy attribution of that mount
- **AND** it is reachable only through reads scoped to that tenancy

### Requirement: Every read is scoped to the requesting principal's tenancy

No read operation performed on behalf of a tenant principal SHALL return, count, or otherwise reveal a resource belonging to a tenancy that principal has no grant in. This SHALL hold for single-resource reads, list operations, searches, aggregates, exports, and any diagnostic or administrative view.

Scoping SHALL be a property of the read operation itself, not a filter applied by its caller. A read operation over tenant-attributed state that is invoked without a tenancy scope SHALL fail rather than return the unscoped result. Where a principal holds grants in more than one tenancy, a read SHALL be scoped to exactly one named tenancy and SHALL NOT return the union of them.

An installation-wide read spanning tenancies SHALL be available only to an operator principal, SHALL be a distinct operation from any tenant-scoped read, and SHALL itself be recorded.

#### Scenario: Routing entries are scoped

- **WHEN** a principal with grants in one tenancy lists routing entries
- **THEN** only routing entries of that tenancy are returned
- **AND** the count returned matches the number of entries in that tenancy, not the installation

#### Scenario: Credentials are scoped

- **WHEN** a principal lists the credentials that may register a sidecar
- **THEN** only credentials issued within their own tenancy are returned
- **AND** no attribute of any other tenancy's credential is returned, including its identifier, its label, and its issuance time

#### Scenario: Hostname claims are scoped

- **WHEN** a principal lists claimed hostnames
- **THEN** only hostnames claimed within their own tenancy are returned
- **AND** hostnames claimed by other tenancies are absent from the result

#### Scenario: Sidecar registrations are scoped

- **WHEN** a principal views connected sidecars
- **THEN** only sidecars registered against mounts in their own tenancy are shown
- **AND** neither the count nor the connection state of any other tenancy's sidecars is revealed

#### Scenario: Logs are scoped

- **WHEN** a principal reads request or diagnostic logs
- **THEN** only records produced while serving their own tenancy's mounts are returned
- **AND** no record naming another tenancy's hostname, path, or backend is returned

#### Scenario: Metrics are scoped

- **WHEN** a tenant principal reads metrics
- **THEN** the values reflect only their own tenancy's traffic and resource consumption
- **AND** no value returned is an installation-wide aggregate
- **AND** no value returned changes when a different tenancy's traffic changes

#### Scenario: An unscoped read cannot be expressed

- **WHEN** a read operation over a tenant-attributed resource is invoked without a tenancy scope
- **THEN** the invocation fails
- **AND** no resource is returned

#### Scenario: A principal with grants in two tenancies reads one at a time

- **WHEN** a principal holding grants in two tenancies performs a read naming one of them
- **THEN** only that tenancy's resources are returned
- **AND** the other tenancy's resources are absent from the result and from its count
- **AND** a read naming neither tenancy fails rather than returning both

#### Scenario: An operator read spanning tenancies is distinct and recorded

- **WHEN** an operator principal performs an installation-wide read spanning tenancies
- **THEN** the operation is one no tenant principal can invoke
- **AND** a record of it exists naming the operator, the time, and the scope read

### Requirement: Authorization is intrinsic to the mutation

Every operation that creates, modifies, revokes, or removes tenant-attributed state SHALL be performed on behalf of an identified principal supplied as part of the invocation. It SHALL NOT be possible to invoke such an operation without a principal.

The operation SHALL itself determine whether that principal holds the authority the operation requires, and SHALL refuse otherwise. Authorization SHALL NOT depend on a check performed by the caller: a caller that performs no check of its own SHALL be unable to cause an unauthorized mutation. When an operation refuses, it SHALL make no partial change.

#### Scenario: Mutation without a principal is refused

- **WHEN** a mutation is invoked with no principal
- **THEN** the invocation fails
- **AND** the subject is unchanged

#### Scenario: The caller forgot to check

- **WHEN** a mutation is reached through an entry point that performs no authorization check of its own
- **AND** the supplied principal holds no grant conferring the required authority on the subject
- **THEN** the mutation is refused
- **AND** the subject is unchanged

#### Scenario: Every mutation in the administrative surface is covered

- **WHEN** each mutation over routing entries, credentials, hostname claims, and membership is invoked in turn with a principal holding no grant on the subject
- **THEN** every one of them is refused
- **AND** no subject is modified by any of them

#### Scenario: Sibling operations on one subject class do not diverge

- **WHEN** every operation over a credential — issuing it, modifying it, and revoking it — is invoked in turn without a principal
- **THEN** every one of them fails
- **AND** no credential is created, modified, or revoked
- **AND** the same holds when each is invoked with a principal holding no grant on the credential's tenancy

#### Scenario: Refusal is atomic

- **WHEN** a mutation that would change several related records is refused for lack of authority
- **THEN** none of those records is changed
- **AND** no side effect of the mutation is observable afterwards

### Requirement: Knowing an identifier confers no access

Possession of the identifier of a resource SHALL confer no read or write access to it. Authority SHALL be derived only from the grants the principal holds on the subject's tenancy and mount hierarchy.

Identifiers SHALL be opaque and SHALL NOT be guessable by enumeration or derivable from a sequence, a count, or a timestamp. Where a principal has no grant on the subject, the outcome SHALL be indistinguishable from the outcome for an identifier that does not exist. Where the principal does hold a grant on the subject's tenancy, an absent subject MAY be reported as absent, because doing so reveals nothing the principal is not entitled to know.

#### Scenario: Reading another tenancy's resource by identifier

- **WHEN** a principal supplies the exact identifier of a routing entry belonging to another tenancy
- **THEN** the read is refused
- **AND** the outcome is identical, in status and in message, to supplying an identifier that exists nowhere in the installation

#### Scenario: Writing to another tenancy's resource by identifier

- **WHEN** a principal supplies the exact identifier of a credential belonging to another tenancy and attempts to modify it
- **THEN** the mutation is refused
- **AND** the credential is unchanged
- **AND** the attempt is recorded against the principal

#### Scenario: Absence is reported within one's own tenancy

- **WHEN** a principal holding a grant in a tenancy supplies an identifier that does not exist in it
- **THEN** the outcome states that the subject was not found

#### Scenario: Identifiers cannot be enumerated

- **WHEN** a principal observes the identifiers of several resources created in their own tenancy in a known order
- **THEN** the identifiers are not ordered, not adjacent, and do not encode a creation index or a creation time
- **AND** the interval between two consecutively issued identifiers does not indicate how many resources were created elsewhere in the installation between them

### Requirement: Roles carry defined and bounded authority

The role model SHALL define at least three roles on a routing entry — a node in the path hierarchy the mount-point capability defines, whether or not it is a mount point: owner, maintainer, and viewer. A principal with no grant SHALL have no authority of any kind on that entry.

A viewer SHALL be able to read the entry and its configuration and SHALL NOT be able to modify anything. A maintainer SHALL hold the viewer's authority and additionally be able to modify the entry's routing configuration, its hostname claims, and its credentials, and SHALL NOT be able to alter membership. An owner SHALL hold the maintainer's authority and additionally be able to alter membership and remove the entry. Every operation SHALL state which role it requires, and SHALL refuse a principal below it.

#### Scenario: A viewer cannot mutate routing

- **WHEN** a principal holding the viewer role attempts to change a routing entry's configuration
- **THEN** the attempt is refused
- **AND** the entry is unchanged

#### Scenario: A viewer cannot mutate credentials or hostnames

- **WHEN** a principal holding the viewer role attempts to issue, modify, or revoke a credential, or to claim or release a hostname
- **THEN** each attempt is refused
- **AND** no credential and no hostname claim is changed

#### Scenario: A maintainer cannot manage membership

- **WHEN** a principal holding the maintainer role attempts to add a principal to an entry, remove one, or change another principal's role
- **THEN** the attempt is refused
- **AND** the membership of the entry is unchanged

#### Scenario: A maintainer cannot remove the entry

- **WHEN** a principal holding the maintainer role attempts to remove a routing entry
- **THEN** the attempt is refused
- **AND** the entry remains in service

#### Scenario: A maintainer can do maintainer work

- **WHEN** a principal holding the maintainer role revokes a credential of that entry
- **THEN** the revocation succeeds
- **AND** it is recorded against that principal

#### Scenario: No grant means no access

- **WHEN** a principal holding no grant on an entry attempts any read or any mutation of it
- **THEN** every attempt is refused
- **AND** the outcome does not distinguish the entry from one that does not exist

### Requirement: Roles are inherited down the mount hierarchy

A grant made on a routing entry SHALL confer the same role on every entry beneath it in the mount hierarchy. A principal's effective role on an entry SHALL be determined by the grants held on that entry and its ancestors, and SHALL NOT be affected by grants held on its descendants or its siblings.

Where grants exist at more than one level, the grant on the most specific ancestor SHALL determine the effective role, including when that grant is narrower than one held higher up. Removing a grant SHALL remove the authority it conferred on all entries that derived from it, with no further action required.

#### Scenario: An ancestor grant reaches a descendant

- **WHEN** a principal holds the maintainer role on an entry
- **AND** a new entry is created beneath it
- **THEN** the principal holds the maintainer role on the new entry
- **AND** a maintainer operation on the new entry succeeds with no further grant made

#### Scenario: A descendant grant does not reach upward

- **WHEN** a principal holds the owner role on an entry beneath another
- **THEN** the principal has no authority on the entry above it
- **AND** a read of the entry above is refused

#### Scenario: A sibling grant confers nothing

- **WHEN** a principal holds the owner role on one entry
- **THEN** the principal has no authority on a sibling entry sharing the same parent

#### Scenario: The most specific grant wins, including when narrower

- **WHEN** a principal holds the maintainer role on an entry and the viewer role on an entry beneath it
- **THEN** the principal's effective role on the lower entry is viewer
- **AND** a mutation of the lower entry is refused

#### Scenario: Revoking an ancestor grant removes derived authority

- **WHEN** a principal's grant on an entry is removed
- **AND** the principal holds no other grant on that entry or its ancestors
- **THEN** the principal loses access to that entry and to every entry beneath it
- **AND** an operation already authorized under the removed grant does not continue to be authorized

#### Scenario: Removing a narrowing grant restores the ancestor's authority

- **WHEN** a principal holds the maintainer role on an entry and the viewer role on an entry beneath it
- **AND** the viewer grant on the lower entry is removed
- **THEN** the principal's effective role on the lower entry becomes maintainer
- **AND** a mutation of the lower entry that was previously refused now succeeds

### Requirement: Membership changes preserve an accountable owner

Changes to membership SHALL require the owner role on the entry whose membership is changing. A routing entry SHALL NOT be left with no principal holding the owner role on it or on an ancestor of it; an operation that would produce that state SHALL be refused.

A principal SHALL NOT be able to raise their own role, and SHALL NOT be able to grant a role higher than the one they hold.

#### Scenario: The last owner cannot be removed

- **WHEN** an owner attempts to remove the only remaining owner grant covering an entry
- **THEN** the attempt is refused
- **AND** the membership is unchanged

#### Scenario: Self-promotion is refused

- **WHEN** a principal holding the maintainer role attempts to change their own role to owner
- **THEN** the attempt is refused
- **AND** the recorded outcome names the principal as both actor and subject

#### Scenario: A grant cannot exceed the granter's role

- **WHEN** a principal attempts to grant a role higher than the one they themselves hold on the entry
- **THEN** the attempt is refused

#### Scenario: A legitimate membership change succeeds

- **WHEN** an owner grants the maintainer role on the entry to another principal of the same tenancy
- **THEN** the grant takes effect and that principal can perform maintainer operations on the entry
- **AND** the change is recorded naming the granting owner, the receiving principal, and the role granted

#### Scenario: An owner is removable while another owner remains

- **WHEN** an entry is covered by two owner grants and one of them is removed
- **THEN** the removal succeeds
- **AND** the remaining owner retains the owner role
- **AND** a subsequent attempt to remove that remaining owner grant is refused

### Requirement: Reclaiming a released name confers no access to prior state

When a routing entry, hostname, or other named resource is removed and its name subsequently becomes available again, creating a new resource under that name SHALL produce a resource with a new identity in the creating principal's tenancy. It SHALL NOT restore, adopt, or make reachable any prior resource of that name, any membership grant on it, any credential issued for it, or any audit record belonging to it.

Removal SHALL take effect across every resource that depends on the removed subject, so that no dependant remains active, claimable, or blocking after its subject is gone.

#### Scenario: Name reuse does not resurrect another tenancy's entry

- **WHEN** a routing entry belonging to one tenancy is removed
- **AND** a principal of a different tenancy creates an entry with the same name
- **THEN** the new entry is empty of prior configuration
- **AND** the creating principal receives no access to the removed entry's history, credentials, or grants

#### Scenario: Credentials do not survive removal of their subject

- **WHEN** a routing entry is removed
- **THEN** every credential issued for it ceases to authorize anything
- **AND** a sidecar presenting such a credential is refused
- **AND** a tunnel already established with such a credential stops serving the removed entry rather than continuing until it reconnects

#### Scenario: The prior holder's grants do not reach the new resource

- **WHEN** a routing entry is removed and a principal of a different tenancy creates an entry under the same name
- **THEN** no principal who held a grant on the removed entry holds any authority on the new one
- **AND** a read of the new entry by such a principal is refused
- **AND** the new entry's only grants are those created with it

#### Scenario: Dependants do not block reuse after removal

- **WHEN** a routing entry with a hostname claim is removed
- **THEN** the hostname claim is released with it
- **AND** the hostname can be claimed afresh, subject to ownership verification

### Requirement: Data-plane traffic never crosses a tenant boundary

A request matched to a mount SHALL be forwarded only to a sidecar registered against a mount in the same tenancy. Selection among sidecars, failover, and affinity SHALL operate only within that set, and SHALL treat a sidecar of another tenancy as if it did not exist.

A credential SHALL authorize registration only for the mounts within the tenancy it was issued in. Establishing a tunnel SHALL NOT grant visibility of any exchange, stream, mount, or hostname outside that tenancy.

#### Scenario: Selection is confined to the tenancy

- **WHEN** sidecars of two tenancies are connected simultaneously
- **AND** a request arrives for a mount of the first
- **THEN** it is forwarded only to a sidecar of the first tenancy
- **AND** it is refused rather than served if no such sidecar is connected

#### Scenario: A credential cannot register outside its tenancy

- **WHEN** a sidecar presents a valid credential and attempts to register for a mount in another tenancy
- **THEN** registration is refused
- **AND** the refusal does not confirm whether that mount exists

#### Scenario: A tunnel reveals nothing outside its tenancy

- **WHEN** a sidecar is connected and other tenancies are serving traffic
- **THEN** no frame, error, or diagnostic delivered over that tunnel refers to an exchange, mount, or hostname of another tenancy

### Requirement: Tenant attribution of traffic derives only from authenticated input

The tenancy a request is attributed to SHALL be derived solely from inputs the system itself established or verified: the mount the request matched, the hostname binding the edge authenticated for the connection, and the credential a sidecar presented. A field the client supplies and the system does not verify SHALL NOT select, alter, or contribute to that attribution.

Per-tenant accounting, bounds, and audit attribution SHALL use the same derived tenancy. A client SHALL NOT be able to obtain a fresh accounting position, a distinct bound, or a different attribution by varying, omitting, or forging any value it supplies.

Traffic that cannot be attributed to a tenancy SHALL be refused rather than served under a default, shared, or absent attribution.

#### Scenario: A client-supplied tenancy hint is ignored

- **WHEN** a client sends a request to a mount carrying a header field naming a different tenancy or a different account
- **THEN** the request is attributed to the tenancy of the matched mount
- **AND** it is not routed to the tenancy the supplied field names
- **AND** the accounting, the bounds applied, and the audit attribution for the request all name the matched mount's tenancy

#### Scenario: Varying a client-supplied value does not reset accounting

- **WHEN** a client issues a sequence of requests to one tenancy's mount, supplying a different value for the same unverified identifying field on every request
- **THEN** every request is accounted against the same tenancy
- **AND** the per-tenant bounds are reached at the same point as if the field had been constant
- **AND** no request obtains a fresh accounting position by changing that value

#### Scenario: A forged host does not select another tenancy

- **WHEN** a request arrives whose client-supplied host names a hostname claimed by another tenancy, and the connection was not authenticated for that hostname
- **THEN** the request is not routed to that other tenancy's mounts
- **AND** it is refused
- **AND** the refusal does not confirm whether that hostname is claimed

#### Scenario: Unattributable traffic is refused

- **WHEN** a request arrives that matches no mount and no authenticated hostname binding
- **THEN** it is refused
- **AND** it is not served, counted, or logged under a default or shared tenancy

### Requirement: Client credentials issued for one mount do not reach another tenancy's mount

A credential a backend asks a client to store — including any field instructing the client to return a value on subsequent requests — SHALL be confined to the mount that issued it. Where two tenancies are reachable under one hostname, a value stored on behalf of one tenancy's mount SHALL NOT be transmitted to another tenancy's mount, and SHALL NOT be readable by another tenancy's backend.

The system SHALL NOT rely on the tenant's backend to scope such a value correctly. The mechanism by which an over-broad scope is narrowed on the way out and a foreign value is withheld on the way in is owned by the edge-hygiene capability and is not restated here; this requirement states the isolation property that mechanism exists to hold, and the property SHALL be testable independently of it. Every narrowing or withholding SHALL be observable and attributed to the tenancy it protected.

#### Scenario: A session value does not cross a mount boundary on a shared hostname

- **WHEN** two tenancies are mounted under one hostname and the first tenancy's backend instructs the client to store a session value scoped to the whole hostname
- **AND** the client subsequently requests a path belonging to the second tenancy's mount
- **THEN** the second tenancy's backend does not receive that value

#### Scenario: An over-broad scope is narrowed, not relayed

- **WHEN** a backend emits a stored-value instruction whose declared scope covers paths outside its own mount
- **THEN** the value delivered to the client is scoped to that mount, or the instruction is not relayed
- **AND** the narrowing or refusal is recorded and attributed to that tenancy

#### Scenario: A client cannot present another tenancy's value across the boundary

- **WHEN** a client presents a stored value that was issued for one tenancy's mount on a request to another tenancy's mount
- **THEN** the value is not forwarded to the second tenancy's backend
- **AND** the second request is served as though no such value had been presented

#### Scenario: Per-tenant hostnames keep values separate

- **WHEN** two tenancies are reachable on distinct verified hostnames sharing a parent domain
- **THEN** a value stored for one hostname is not transmitted to the other
- **AND** neither backend can cause a value to be stored that the other would receive

### Requirement: Per-tenant resource bounds are enforced on every dimension

This capability owns the enumeration of the dimensions on which a tenant is bounded, and that enumeration SHALL be closed: nothing SHALL be bounded per tenant that is not an entry in it. The enumeration has two parts, and both are retrievable in one place.

The **occupancy dimensions**, which describe what a tenant's traffic holds and which this capability defines outright, SHALL be: concurrent exchanges, concurrent long-lived streams, octets in flight, octets buffered on the tenant's behalf, and request admission rate. A tenant exceeding a bound SHALL be throttled or refused, with a distinguishable, machine-readable outcome naming the bound that was reached.

The **standing-resource dimensions**, which describe what a tenant may hold whether or not traffic is flowing, SHALL be contributed to this same enumeration by the capability that owns the resource, because only that capability can state what the resource is: at minimum concurrently registered sidecar entries per mount and per tenant, and concurrent affinity bindings per tenant, contributed by the sidecar-registry capability; and hostname claims held, claim creation rate, challenge issuance rate, and certificate issuance, contributed by the custom-domain capability. A contributed dimension SHALL be an entry of this enumeration on the same terms as an occupancy dimension — one configured value per tenant, a distinguishable outcome naming it, and observability of each tenant's consumption of it — and contributing one SHALL be the only way a per-tenant dimension comes to exist.

A capability that admits work or holds a resource SHALL enforce the enumerated dimensions at its own admission points and SHALL NOT introduce a per-tenant dimension that is not an entry here. A narrowing *within* one tenant's already-bounded allowance — a bound on what a single credential, mount, or claim may occupy of it — SHALL NOT be a new dimension, SHALL NOT be able to exceed the per-tenant value it narrows, and SHALL be stated by the capability that owns the subject it narrows. Where a dimension is bounded at more than one admission point, the bound SHALL be one configured value per tenant, accounted once, so that a tenant's total occupancy cannot exceed it by arriving through two surfaces. "Accounted once" is a statement about the installation and not only about admission surfaces: the requirements that follow settle what one value means across instances, what holds while instances cannot reach one another, and the closed exception under which a dimension may instead be accounted per instance.

A request rate bound alone SHALL NOT be treated as sufficient. One admitted request may hold an exchange, a stream, and buffered octets for hours, so a tenant within its rate bound can still hold an unbounded share of the installation's capacity; occupancy and volume SHALL therefore be bounded independently of arrival rate.

Octets SHALL be counted as they occupy the system's own memory at the hop that holds them, after any expansion that hop performs, so that a small compressed input which expands enormously is bounded by the octets it actually occupies rather than by its transferred size. The system SHALL NOT expand a payload solely in order to account for it: a payload forwarded without expansion SHALL be counted at its transferred size.

A tenant within every one of its bounds SHALL NOT be throttled or refused by this requirement.

#### Scenario: Concurrent exchange bound

- **WHEN** a tenant's concurrent exchanges reach the configured bound
- **AND** a further request for that tenant arrives
- **THEN** the request is refused
- **AND** the outcome names the concurrent exchange bound
- **AND** exchanges already in flight are not disturbed

#### Scenario: Long-lived streams are bounded separately

- **WHEN** a tenant holds the configured maximum number of long-lived streams, all of them within the request rate bound
- **AND** a further long-lived stream is requested
- **THEN** it is refused
- **AND** the outcome names the long-lived stream bound rather than a rate bound

#### Scenario: Buffered octets are bounded

- **WHEN** the octets buffered on one tenant's behalf reach the configured bound
- **THEN** further buffering for that tenant is refused or its producers are throttled
- **AND** the octets held for that tenant do not exceed the bound

#### Scenario: Expansion is counted, not the compressed size

- **WHEN** a tenant sends a small payload that the system must expand at its own hop before forwarding, and the expanded form is very large
- **THEN** the expanded octets are counted against that tenant's bound
- **AND** the transfer is refused or throttled before the bound is exceeded
- **AND** the octets held for that tenant never exceed the bound at any point during the expansion

#### Scenario: A tenant within its bounds is not throttled

- **WHEN** a tenant's concurrent exchanges, long-lived streams, octets in flight, buffered octets, and arrival rate are all below their configured bounds
- **THEN** its requests are admitted
- **AND** no bound-related refusal or throttling outcome is produced for that tenant

#### Scenario: Rate bound alone does not admit unbounded occupancy

- **WHEN** a tenant issues requests slowly enough to remain within its rate bound
- **AND** each admitted request holds an exchange open indefinitely
- **THEN** the tenant is stopped by an occupancy bound
- **AND** the installation's capacity consumed by that tenant remains bounded

#### Scenario: Bound outcomes are attributable

- **WHEN** any per-tenant bound is reached
- **THEN** the event is recorded naming the tenancy and the bound
- **AND** an operator can determine which tenant caused it without inspecting request contents

#### Scenario: The enumeration is closed and retrievable in one place

- **WHEN** an operator retrieves the per-tenant bound dimensions in force
- **THEN** the occupancy dimensions and every contributed standing-resource dimension appear in one enumeration
- **AND** every per-tenant bound the installation enforces is an entry in it
- **AND** no capability enforces a per-tenant bound on a dimension absent from it

#### Scenario: A contributed dimension behaves as an entry

- **WHEN** a tenant reaches a contributed standing-resource dimension's bound
- **THEN** the refusal names that dimension
- **AND** that tenant's consumption of it is observable as for any occupancy dimension
- **AND** another tenant's ability to hold that resource is unaffected

#### Scenario: A narrowing is not a new dimension

- **WHEN** a bound on what one credential may occupy of its tenant's allowance is configured
- **THEN** it does not appear as a further per-tenant dimension
- **AND** it cannot be set above the per-tenant value it narrows
- **AND** the tenant's allowance is consumed by all its credentials together rather than by each separately

#### Scenario: One dimension is accounted once across admission points

- **WHEN** a tenant opens long-lived work through more than one admission surface at the same time
- **THEN** all of it counts against the one configured bound for that dimension
- **AND** the tenant's total occupancy on that dimension does not exceed the bound
- **AND** the outcome names the same bound whichever surface refused it

### Requirement: A per-tenant bound is one value for the installation, not one value per instance

Every entry in the closed enumeration of per-tenant dimensions — every occupancy dimension and every contributed standing-resource dimension alike — SHALL be one configured value for the installation. A tenant's total consumption of that dimension, summed over every instance that admits or holds work on the tenant's behalf, SHALL NOT exceed the configured value. The value SHALL NOT be interpreted as an allowance each instance grants independently, and no capability SHALL enforce a per-tenant dimension solely against the consumption observed at the instance handling the current admission.

Adding an instance to the installation SHALL NOT increase any tenant's allowance on any dimension, and removing one SHALL NOT reduce it. A tenant SHALL NOT obtain more of a dimension than the configured value by distributing its clients across instances, by holding tunnels terminated on different instances, by directing successive admissions to different instances, or by any other means whose only effect is to change which instance handles the work.

Conversely, the configured value SHALL NOT be silently divided among instances in normal operation: a tenant whose work all arrives at one instance SHALL be able to consume its whole configured allowance there. A partitioned or otherwise degraded installation is the only condition under which a locally-held share may bound a tenant below its configured value, and that condition is governed by the partition requirement below.

Where more than one instance participates in accounting a tenant's consumption, the work of doing so SHALL be proportional to that tenant's own admissions and SHALL NOT be proportional to the number of tenants in the installation.

#### Scenario: Occupancy spread across instances counts once

- **WHEN** a tenant opens concurrent exchanges against several instances at the same time, such that the total across all instances reaches the configured bound
- **AND** a further request for that tenant arrives at any instance
- **THEN** the request is refused
- **AND** the outcome names the concurrent exchange bound
- **AND** the tenant's total concurrent exchanges across the installation do not exceed the configured value

#### Scenario: Adding instances does not enlarge an allowance

- **WHEN** a tenant's consumption of any enumerated dimension is at the configured bound
- **AND** further instances are added to the installation
- **THEN** the tenant's admitted consumption of that dimension does not rise above the configured value
- **AND** requests that would exceed it are still refused with the same named dimension

#### Scenario: A contributed dimension is accounted across instances

- **WHEN** a tenant's sidecars register through more than one instance until the tenant's registered entries reach the contributed bound
- **AND** a further registration is attempted at a different instance
- **THEN** it is refused with a reason naming that dimension
- **AND** no existing registration is displaced to admit it

#### Scenario: Work arriving at one instance may consume the whole allowance

- **WHEN** every request for a tenant arrives at a single instance while the installation holds many instances and accounting is not degraded
- **THEN** that tenant is admitted up to its whole configured value on each dimension
- **AND** it is not refused at a fraction of the configured value

#### Scenario: Accounting cost does not grow with the installation's tenant count

- **WHEN** a tenant's admissions are accounted across instances
- **AND** the number of unrelated tenants in the installation is increased by an order of magnitude
- **THEN** the accounting work performed per admission for that tenant is unchanged
- **AND** other tenants observe no change in request latency beyond the declared interference tolerance

### Requirement: Per-instance accounting is a closed and justified exception

One class of bound cannot be accounted for the installation without doing coordination work on a path any party can reach. A dimension bounded on an arrival that has not yet been attributed to a tenancy is such a bound — whether because the arriving party has not authenticated, as with the pre-authentication connection bound `tunnel/listener` states, or because the arrival has not yet been matched to a tenant's mount, as with an arrival-rate bound the edge applies on a client identity it established from a connection: an installation-wide count taken on every arrival is work an unidentified party could cause at an instance it never connected to. That bound MAY therefore be accounted per instance, and it is the only ground on which a dimension that bounds a party's consumption of the installation's capacity may be accounted per instance. It SHALL NOT be the means by which a per-tenant dimension is enforced: where the same arrivals are also bounded per tenant once attributed, that per-tenant bound remains subject to installation-wide accounting. A bound on what one instance itself holds — its own capacity, whoever consumes it — is not such a dimension: it is inherently local, is owned by the capability that operates the instance, is not a per-tenant dimension, and this requirement neither permits nor constrains it beyond the observability and non-attribution obligations below.

Where a capability accounts a dimension per instance, all of the following SHALL hold. The capability that owns the dimension SHALL state that it is accounted per instance and SHALL state that ground; per-instance accounting SHALL NOT be an unstated property of an implementation. The per-instance nature SHALL be observable: the dimension SHALL be identified as per-instance wherever the bounds in force are retrieved, every record of reaching it SHALL identify the instance, and its consumption SHALL be retrievable per instance. It SHALL NOT be attributed to any tenancy, SHALL NOT be an entry in the closed enumeration of per-tenant dimensions, and reaching it SHALL NOT be recorded as a per-tenant bound refusal.

The exception SHALL NOT be available to a dimension bounded per tenant. A dimension accounted only after the consumption has been attributed to a tenancy SHALL NOT claim it, and no capability SHALL claim it on the ground that installation-wide accounting is merely inconvenient, slower, or harder to implement. A per-tenant dimension found to be accounted per instance SHALL be a conformance failure of the capability that enforces it, not a permitted variation.

#### Scenario: A permitted per-instance dimension is declared and observable

- **WHEN** an operator retrieves the bounds in force for a capability that bounds arrivals before any identity is established
- **THEN** that dimension is identified as accounted per instance
- **AND** the ground for it is stated
- **AND** its consumption and the fact of reaching it are retrievable per instance, naming the instance

#### Scenario: A pre-attribution bound does not substitute for the per-tenant one

- **WHEN** arrivals bounded per instance before attribution are also bounded per tenant once attributed to a tenancy
- **AND** one tenant spreads its arrivals across every instance until its total reaches the configured per-tenant value
- **THEN** further arrivals for that tenant are refused at whichever instance they reach
- **AND** the per-instance bound having not been reached at any single instance does not admit them

#### Scenario: A per-instance dimension is charged to no tenancy

- **WHEN** a per-instance dimension reaches its bound and refuses further arrivals
- **THEN** no tenancy's consumption of any enumerated dimension changes
- **AND** the refusals are not recorded as a per-tenant bound refusal
- **AND** the refusals are counted under that dimension by its own name

#### Scenario: A per-tenant dimension cannot be accounted per instance

- **WHEN** a capability enforces an entry of the per-tenant enumeration against only the consumption it observes at the admitting instance
- **THEN** a tenant distributing its work across instances exceeds the configured value
- **AND** that excess is detectable as a conformance failure against the installation-wide accounting requirement

#### Scenario: The exception cannot be claimed silently

- **WHEN** the dimensions the installation bounds are retrieved in full
- **THEN** every dimension accounted per instance appears as such with its stated ground
- **AND** a dimension accounted per instance without appearing there is a conformance failure
- **AND** no entry of the per-tenant enumeration appears among them

#### Scenario: Convenience is not a ground

- **WHEN** a dimension whose consumption is attributed to a tenancy is accounted per instance
- **THEN** the arrangement is refused as non-conforming whatever performance or simplicity is claimed for it
- **AND** the dimension remains subject to installation-wide accounting

### Requirement: Bound accounting under partition follows a declared discipline with bounded and recorded overshoot

While instances cannot reach one another, exact installation-wide accounting is unattainable, so what the installation does instead SHALL be a declared property of its configuration rather than whatever its implementation happens to do. For each enumerated dimension the installation SHALL declare exactly one accounting discipline for the condition in which an instance cannot account installation-wide. It SHALL be one of exactly two: *refuse*, under which the instance admits no further consumption of that dimension for any tenant whose consumption it cannot account and refuses with an outcome naming that dimension; or *admit to a local share*, under which the instance admits further consumption only up to a share of the configured value it holds locally and refuses beyond that share with an outcome naming that dimension. No third discipline SHALL be available, and an instance that can account installation-wide SHALL apply neither.

The declared discipline SHALL be retrievable alongside the bounds in force, together with which dimensions it governs. It SHALL be a property of the installation and not of an instance: an instance SHALL NOT select, infer, or vary its own discipline, and instances that disagree about the discipline in force SHALL be an enumerated degraded condition observable while it holds.

Under either discipline the following SHALL hold. Consumption admitted before accounting became degraded SHALL NOT be refused, reset, or displaced merely because accounting degraded. Any total consumption above the configured value that arises while accounting is degraded SHALL be bounded: the maximum a tenant's total consumption of a dimension can reach SHALL be determinable in advance from configuration, SHALL be finite, and SHALL NOT grow with the duration of the degradation, with the number of times it recurs, or with how many admissions are attempted during it. No degradation, however long, SHALL admit unbounded consumption.

Every admission made without installation-wide accounting SHALL be recorded, naming the tenancy, the dimension, and the instance. Degraded accounting SHALL itself be an enumerated degraded condition, observable continuously while it holds, stating when it began and which dimensions it affects. Where a tenant's total consumption is known to have exceeded its configured value, that SHALL be observable as a distinct condition naming the tenancy, the dimension, and the extent and duration of the excess; an excess SHALL NOT be discarded, rounded away, or reported only as consumption within the bound.

A refusal caused by degraded accounting SHALL name the dimension that could not be accounted, and SHALL additionally be distinguishable from a refusal caused by the tenant actually reaching that dimension's bound, so that an operator can tell a tenant at its ceiling from an installation that could not determine where the tenant stood.

When instances can reach one another again, accounting SHALL return to installation-wide within a bounded time and without operator action. A tenant whose total consumption is then above its configured value SHALL be admitted no further consumption of that dimension until its total falls below the value. Whether existing consumption above the value is also shed SHALL be declared, and where it is shed the shedding SHALL be recorded and attributed to the tenancy.

#### Scenario: The declared discipline is retrievable and uniform

- **WHEN** an operator retrieves the bounds in force
- **THEN** the accounting discipline in force while an instance cannot account installation-wide is stated for each enumerated dimension
- **AND** every instance reports the same discipline for the same dimension
- **AND** an instance reporting a different discipline appears as an enumerated degraded condition

#### Scenario: Refusing under the refuse discipline

- **WHEN** the refuse discipline is declared for a dimension and an instance cannot account installation-wide
- **AND** a tenant requests further consumption of that dimension at that instance
- **THEN** the request is refused with an outcome naming that dimension
- **AND** the refusal is distinguishable from the tenant having reached that dimension's bound
- **AND** consumption that tenant already held is neither reset nor displaced

#### Scenario: Admitting to a local share

- **WHEN** the admit-to-a-local-share discipline is declared for a dimension and an instance cannot account installation-wide
- **THEN** that instance admits further consumption for a tenant up to the share it holds locally
- **AND** it refuses beyond that share with an outcome naming that dimension
- **AND** the tenant's total consumption across the installation does not exceed the declared maximum for degraded accounting

#### Scenario: Overshoot does not grow with the length of the degradation

- **WHEN** instances remain unable to reach one another for an extended period
- **AND** tenants continuously attempt further consumption at every instance throughout it
- **THEN** each tenant's total consumption of each dimension remains at or below the maximum determinable in advance from configuration
- **AND** that maximum is the same for a long degradation as for a short one
- **AND** repeated degradations do not raise it

#### Scenario: Admissions without installation-wide accounting are recorded

- **WHEN** consumption is admitted while accounting is degraded
- **THEN** each such admission is recorded naming the tenancy, the dimension, and the instance
- **AND** an operator can retrieve, for the period of the degradation, which tenants were admitted without installation-wide accounting

#### Scenario: An excess above the configured value is observable, not silent

- **WHEN** a tenant's total consumption of a dimension has exceeded its configured value during degraded accounting
- **THEN** a distinct condition names the tenancy, the dimension, the extent of the excess, and how long it held
- **AND** that tenant's reported consumption is not clamped to the configured value
- **AND** the excess remains retrievable after the degradation has ended

#### Scenario: Degraded accounting is announced while it holds

- **WHEN** an instance cannot account a dimension installation-wide
- **THEN** an operator inspecting that instance finds an enumerated degraded condition naming the affected dimensions and when it began
- **AND** the instance does not report itself as fully healthy during it

#### Scenario: Recovery admits nothing further until the tenant is under its value

- **WHEN** instances can reach one another again and a tenant's total consumption of a dimension is above its configured value
- **THEN** installation-wide accounting resumes within a bounded time and without operator action
- **AND** no further consumption of that dimension is admitted for that tenant at any instance until its total falls below the configured value
- **AND** whether existing consumption above the value is shed matches what the installation declared, and any shedding is recorded and attributed to the tenancy

#### Scenario: Another tenant is unharmed by one tenant's excess

- **WHEN** one tenant's total consumption is above its configured value because accounting was degraded
- **THEN** another tenant's requests continue to be admitted up to that tenant's own bounds
- **AND** their completion times remain within the declared interference tolerance of their unloaded baseline

### Requirement: Accounting survives restart and rejoin without granting a fresh allowance

An instance that starts, restarts, or rejoins the installation SHALL NOT assume that any tenant's consumption of any enumerated dimension is zero. Before admitting consumption of a dimension it SHALL either account that dimension installation-wide, or treat itself as unable to do so and apply the declared discipline for that condition. Admitting a full fresh allowance on the ground that the instance has no local record of prior consumption SHALL NOT occur.

Consumption of a standing-resource dimension SHALL be recoverable from the state that holds the resource, so that after the restart of one instance or of every instance the consumption reported for each tenant reflects the resources that still exist rather than what has been admitted since the restart.

Consumption held by an instance that is lost SHALL be released within a bounded time and SHALL NOT remain charged to the tenancy indefinitely; the release SHALL be recorded and attributed. Equally, consumption held by instances that are still running SHALL remain charged while they hold it, so a restart neither leaks a tenant's allowance nor returns it.

A tenant SHALL NOT be able to obtain consumption above its configured value by causing, or waiting for, an instance to restart or rejoin.

#### Scenario: A rejoining instance does not admit a fresh allowance

- **WHEN** a tenant's consumption of a dimension is at its configured bound, held through other instances
- **AND** an instance restarts and rejoins the installation
- **AND** a request for that tenant arrives at the rejoined instance
- **THEN** it is refused with an outcome naming that dimension
- **AND** the tenant's total consumption does not rise above the configured value

#### Scenario: Standing-resource consumption is recovered, not reset

- **WHEN** every instance in the installation is restarted while tenants hold registered sidecar entries and hostname claims
- **THEN** each tenant's reported consumption of those contributed dimensions reflects the resources that still exist
- **AND** a tenant already at such a bound is refused a further one
- **AND** no tenant is reported as consuming none of a dimension it still holds

#### Scenario: Consumption of a lost instance is released

- **WHEN** an instance holding consumption for a tenant is lost
- **THEN** that consumption ceases to be charged to the tenancy within a bounded time
- **AND** the release is recorded and attributed to the tenancy and the dimension
- **AND** consumption the tenant holds through surviving instances remains charged

#### Scenario: Forcing a restart yields no extra allowance

- **WHEN** a tenant repeatedly drives its consumption to the bound while instances are restarted around it
- **THEN** its total consumption of each dimension never exceeds the configured value, save within the declared maximum for degraded accounting
- **AND** every refusal names the dimension reached

### Requirement: A tenant's consumption is observable as an installation total

For every entry in the closed enumeration, each tenant's current consumption SHALL be retrievable as one installation-wide total, alongside the configured value for that tenant, without an operator summing per-instance values by hand. A tenant approaching its ceiling SHALL therefore be identifiable from that one retrieval.

The per-instance breakdown of that consumption SHALL also be retrievable, and while accounting is not degraded the breakdown SHALL be consistent with the total. Each reported total SHALL state whether the accounting behind it is installation-wide or degraded, so that a total obtained during degraded accounting is not mistaken for an exact one.

A dimension accounted per instance under the closed exception SHALL be reported per instance and SHALL NOT be presented as an installation-wide total for a tenancy.

These retrievals are operator reads spanning tenancies where they name more than one tenancy, and remain subject to the scoping rules above: a tenant principal reading its own consumption SHALL receive its own installation-wide total and SHALL NOT learn another tenancy's consumption, another tenancy's configured value, or the number of instances in the installation.

#### Scenario: One retrieval shows the installation total against the configured value

- **WHEN** an operator retrieves a tenant's consumption of the enumerated dimensions
- **THEN** each dimension is reported as one installation-wide total alongside that tenant's configured value
- **AND** no summing of per-instance values is required to obtain it
- **AND** a tenant close to a ceiling is evident from that retrieval alone

#### Scenario: The per-instance breakdown agrees with the total

- **WHEN** a tenant holds consumption of a dimension through several instances and accounting is not degraded
- **THEN** the per-instance breakdown is retrievable
- **AND** the reported installation total equals the consumption held across those instances
- **AND** the total is labelled as installation-wide accounting

#### Scenario: A total obtained during degraded accounting says so

- **WHEN** a tenant's consumption is retrieved while an instance cannot account installation-wide
- **THEN** the reported total states that the accounting behind it is degraded
- **AND** it is not presented as an exact installation-wide figure

#### Scenario: A per-instance dimension is not reported as a tenant total

- **WHEN** the consumption of a dimension accounted per instance under the closed exception is retrieved
- **THEN** it is reported per instance
- **AND** it is not reported as an installation-wide total for any tenancy

#### Scenario: A tenant's own read reveals nothing of the installation

- **WHEN** a tenant principal reads its own consumption of the enumerated dimensions
- **THEN** its own installation-wide total and its own configured value are returned
- **AND** no other tenancy's consumption or configured value is returned
- **AND** the number of instances in the installation is not disclosed

### Requirement: A bound refusal is the same whichever instance refuses

For every entry in the closed enumeration, the outcome of reaching a bound SHALL NOT depend on which instance handled the admission. The refusal SHALL name the same dimension, and SHALL be of the same class and the same machine-readable form, at every instance.

A tenant SHALL NOT obtain a different outcome by retrying the same work against another instance: work refused at one instance for reaching an enumerated dimension's bound SHALL be refused at every other instance for the same dimension, for as long as the tenant's total consumption remains at the bound. An outcome may differ only because consumption was released in the interval, not because a different instance was chosen.

A refusal SHALL NOT disclose which instance produced it to the refused party, SHALL NOT disclose how many instances the installation holds, and SHALL NOT reveal how the tenant's consumption is distributed across them; that distribution remains retrievable by an operator.

This requirement governs the entries of the per-tenant enumeration. It does not govern a dimension accounted per instance under the closed exception, whose per-instance nature is declared and observable, and where reaching a bound at one instance is expected not to refuse at another.

#### Scenario: Retrying at another instance is refused identically

- **WHEN** a tenant's request is refused at one instance for reaching an enumerated dimension's bound
- **AND** the same work is immediately retried at a different instance while the tenant's consumption is unchanged
- **THEN** it is refused there too
- **AND** the outcome names the same dimension
- **AND** the two outcomes are of the same class and the same machine-readable form

#### Scenario: Round-robin retrying does not accumulate consumption

- **WHEN** a tenant at an enumerated dimension's bound retries in turn against every instance in the installation
- **THEN** every attempt is refused naming that dimension
- **AND** the tenant's total consumption of that dimension does not rise

#### Scenario: A different outcome follows released consumption, not a different instance

- **WHEN** a tenant at a bound has consumption released and then requests further work at any instance
- **THEN** the request is admitted
- **AND** the admission is attributable to the release rather than to the instance chosen

#### Scenario: A refusal discloses nothing of the installation's shape

- **WHEN** a tenant receives a bound refusal
- **THEN** the outcome names the dimension reached
- **AND** it does not identify the refusing instance, the number of instances, or how the tenant's consumption is distributed across them
- **AND** an operator can still retrieve that distribution

### Requirement: One tenant at its ceiling does not degrade another

The system SHALL declare a published interference tolerance: the maximum change in admission, latency, and error rate that one tenant's load may cause for another. A tenant reaching or exceeding any of its bounds SHALL NOT change the admission, latency, or error rate observed by another tenant beyond that declared tolerance. Capacity reserved for the accounting and refusal of an over-consuming tenant SHALL NOT be drawn from the capacity serving others.

Refusals caused by one tenant's consumption SHALL be delivered to that tenant only. No other tenant SHALL receive a refusal, a reset, or a disconnection as a consequence.

#### Scenario: Saturation is contained

- **WHEN** one tenant drives its traffic past every bound it has
- **THEN** another tenant's requests continue to be admitted
- **AND** their completion times remain within the declared interference tolerance of their unloaded baseline
- **AND** none of their exchanges is refused or reset

#### Scenario: Long-lived streams of one tenant do not crowd out another

- **WHEN** one tenant holds its maximum number of long-lived streams for an extended period
- **THEN** another tenant can still open long-lived streams up to its own bound

#### Scenario: A large transfer does not displace another tenant

- **WHEN** one tenant transfers a very large body slowly
- **THEN** another tenant's short exchanges complete without waiting for it
- **AND** the octets buffered for the large transfer remain within its own tenant's bound

### Requirement: Work caused by a change is proportional to the changing tenant

A change to one tenant's routing entries, hostname claims, credentials, or membership SHALL cause work proportional to that tenant's own configuration. It SHALL NOT cause work proportional to the number of tenants, routing entries, or hostnames in the installation.

Recomputation, invalidation, and propagation of derived state SHALL be scoped to the changing tenancy. Reading routing state for a request SHALL remain correct and uninterrupted while another tenant's derived state is being recomputed.

#### Scenario: Change cost does not grow with the installation

- **WHEN** a tenant makes a routing change
- **AND** the number of unrelated tenants and routing entries in the installation is increased by an order of magnitude
- **THEN** the number of stored routing records read in order to apply that change is unchanged
- **AND** the number of derived routing entries written or removed in order to apply it is unchanged

#### Scenario: Recomputation is scoped

- **WHEN** one tenant's routing entry is added, modified, or removed
- **THEN** only that tenancy's derived routing state is recomputed
- **AND** no other tenancy's derived state is read, rewritten, or invalidated

#### Scenario: Reads are uninterrupted during recomputation

- **WHEN** one tenant's derived routing state is being recomputed
- **THEN** requests for other tenants continue to match their mounts correctly
- **AND** requests for the changing tenant match either the previous or the new configuration, and never an empty one

#### Scenario: Rapid changes by one tenant do not amplify

- **WHEN** one tenant makes many routing changes in quick succession
- **THEN** the work imposed on the installation remains proportional to that tenant's configuration
- **AND** other tenants observe no change in request latency beyond the declared interference tolerance

### Requirement: Faults are contained to the tenant that caused them

A failure occurring while serving one tenant SHALL NOT interrupt, reset, or delay an exchange belonging to another tenant. Recovery from such a failure SHALL NOT require restarting or reinitialising anything shared with other tenants.

A malformed, hostile, or unsupported input arriving from a tenant's client or a tenant's sidecar SHALL affect at most that tenant's exchanges and that tenant's tunnels. Repeated failures for one tenant SHALL NOT accumulate into a condition that degrades the installation. Every contained fault SHALL be recorded and attributed to the tenancy in which it occurred, so that containment does not become silence.

#### Scenario: A crash serving one tenant spares another

- **WHEN** the work serving one tenant's exchange fails unexpectedly
- **THEN** exchanges belonging to other tenants continue and complete
- **AND** their tunnels remain established

#### Scenario: Recovery needs no shared restart

- **WHEN** a fault requires the failed work for one tenant to be reinitialised
- **THEN** the reinitialisation affects only that tenant
- **AND** no other tenant observes a disconnection, a reset, or a refused request

#### Scenario: Repeated faults do not accumulate

- **WHEN** one tenant's traffic causes failures continuously over an extended period
- **THEN** the installation continues to serve other tenants
- **AND** resources released by each failure are reclaimed, so that consumption does not grow without bound

#### Scenario: Hostile input from one sidecar is contained

- **WHEN** a sidecar sends input that the proxy cannot process
- **THEN** at most that sidecar's tunnel and its own tenant's exchanges are affected
- **AND** other tenants' tunnels remain established

#### Scenario: Containment is not silence

- **WHEN** a fault is contained to one tenancy
- **THEN** it is recorded with the tenancy it was attributed to
- **AND** an operator can retrieve it without correlating unrelated records

### Requirement: Every mutation is recorded in an audit trail

Every mutation of a routing entry, a credential, a hostname claim, or a membership grant SHALL produce an audit record stating the acting principal, the subject, the time, the nature of the change, and the outcome. A record SHALL be produced whether the outcome was success or refusal.

A refused authorization attempt SHALL produce a record, including one refused because the principal holds no grant on the subject and one refused because the principal supplied an identifier belonging to another tenancy. An audit record SHALL NOT contain the secret value of any credential.

#### Scenario: A successful mutation is recorded

- **WHEN** a principal changes a routing entry's configuration
- **THEN** an audit record exists naming that principal, that entry, the time, the change, and a successful outcome

#### Scenario: A refused authorization is recorded

- **WHEN** a principal attempts a mutation for which they lack the required role
- **THEN** an audit record exists naming that principal, the subject, the time, the attempted change, and a refused outcome

#### Scenario: A cross-tenancy attempt is recorded in the acting principal's tenancy

- **WHEN** a principal supplies an identifier belonging to another tenancy and the operation is refused
- **THEN** a record of the refused attempt exists and is readable within the acting principal's tenancy
- **AND** the record does not name the other tenancy or any attribute of the subject

#### Scenario: Credential secrets are absent from the trail

- **WHEN** a credential is issued, modified, or revoked
- **THEN** the audit record names the credential and the action
- **AND** it does not contain a value that could be presented to authenticate

#### Scenario: Coverage matches the mutation surface

- **WHEN** each mutation over routing entries, credentials, hostname claims, and membership is performed in turn
- **THEN** each produces an audit record
- **AND** no such mutation completes without one

#### Scenario: An operator action is attributable to the operator

- **WHEN** an operator principal mutates tenant-attributed state or reads across tenancies
- **THEN** an audit record exists naming the operator, the subject, the time, and the action
- **AND** the record distinguishes an operator action from an action by a principal of the affected tenancy

### Requirement: The audit trail is append-only and readable within its own scope

An audit record SHALL be immutable once written, and SHALL NOT be modifiable or removable by any tenant principal, including one holding the owner role over the subject. Retention and removal of audit records SHALL be an operator function only.

A tenant SHALL be able to read the audit records within their own scope, bounded by the grants they hold, and SHALL NOT be able to read any record outside it. Failure to write an audit record SHALL NOT be silent: where the record covers a mutation that has not yet taken effect, the mutation SHALL be refused rather than applied unrecorded.

#### Scenario: An owner cannot amend the trail

- **WHEN** a principal holding the owner role attempts to modify or delete an audit record covering their own tenancy
- **THEN** the attempt is refused
- **AND** the record is unchanged
- **AND** the attempt itself is recorded

#### Scenario: A tenant reads only their own trail

- **WHEN** a principal reads audit records
- **THEN** only records within the scope of their own grants are returned
- **AND** no record concerning another tenancy is returned or counted

#### Scenario: Scope follows the role hierarchy

- **WHEN** a principal holds a grant on an entry and no grant on its parent
- **THEN** they can read audit records for that entry and the entries beneath it
- **AND** they cannot read audit records for the parent

#### Scenario: A failed write is surfaced

- **WHEN** an audit record for a pending mutation cannot be written
- **THEN** the mutation is refused and the subject is unchanged
- **AND** the condition is reported to an operator
- **AND** it is not discarded silently

### Requirement: The audit trail is one trail for the installation, with a stated ordering

Audit records are produced by whichever instance handled the operation, so an installation writes one trail from many instances. That trail SHALL be one trail: a record written at any instance SHALL be readable, within the reader's own scope, from any instance, within a bounded time and without operator action, and a read SHALL NOT return only the records the answering instance produced. A read that cannot cover the whole installation SHALL be marked as not covering it, on the terms `operability/observability` states for an answer spanning the installation, rather than presented as a complete trail — a trail that silently omits one instance's records is worse than one that reports itself incomplete.

Every record SHALL identify the instance that produced it, in addition to the acting principal, the subject, the time, the nature of the change, and the outcome.

The order records are returned in SHALL be stated, SHALL be the same for every reader of the same scope, and SHALL be total, so that two reads of one scope do not interleave the same records differently. It SHALL NOT be claimed or presented as the order in which operations took effect across the installation, except that for a single subject the recorded order SHALL agree with the order the mutations to that subject took effect; a mutation recorded as later than another mutation of the same subject SHALL NOT have taken effect before it.

Disagreement between instances about the current time SHALL NOT cause a record to be lost, overwritten, discarded as out of order, or placed outside the ordering of the subject it concerns. Reading the trail in parts SHALL NOT skip a record: a record that becomes readable after a read of an earlier part has been returned SHALL still be reachable by continuing that read, and SHALL NOT be silently omitted because it arrived late.

A record SHALL NOT be lost because the instance that produced it stopped or fell out of the installation after committing the mutation it describes; where a mutation has taken effect, its record SHALL be readable installation-wide within the bounded time above.

#### Scenario: A record written at one instance is readable at another

- **WHEN** a principal performs a mutation through one instance of the installation
- **THEN** within a bounded time and with no operator action the record is returned by a read directed at any other instance
- **AND** the record identifies the instance that produced it

#### Scenario: A read that cannot span the installation says so

- **WHEN** a scope is read from an instance that cannot reach another instance of the installation
- **THEN** the answer is marked as not covering the whole installation, naming the instance whose records are missing
- **AND** it is not returned in the same shape as a complete answer
- **AND** it does not report that the missing instance produced no records

#### Scenario: Two reads of one scope agree on order

- **WHEN** the same scope is read twice, from different instances, after a period of mutations performed at every instance
- **THEN** the records common to both reads are returned in the same order
- **AND** neither read interleaves them differently

#### Scenario: One subject's records follow the order its mutations took effect

- **WHEN** two mutations of one subject are performed in sequence through two different instances
- **THEN** the trail returns the record of the earlier-effective mutation before the record of the later one
- **AND** this holds when the two instances disagree about the current time

#### Scenario: Clock disagreement loses no record

- **WHEN** instances disagree about the current time and mutations are performed at each of them
- **THEN** every mutation has a record in the trail
- **AND** no record was discarded, overwritten, or rejected as out of order

#### Scenario: A late record is not skipped by a partial read

- **WHEN** a scope is read in parts and a record from another instance becomes readable after an earlier part was returned
- **THEN** continuing the read reaches that record
- **AND** no record is omitted from the sequence of parts

#### Scenario: A record survives the instance that wrote it

- **WHEN** an instance commits a mutation and is then lost before it is queried
- **THEN** the record of that mutation is readable from a surviving instance
- **AND** the mutation is not readable as having taken effect unrecorded

### Requirement: Shared infrastructure does not leak between tenants

Any cache, index, projection, pool, counter, or identifier space shared between tenants SHALL be keyed such that a lookup performed for one tenancy cannot return, or be satisfied by, an entry belonging to another. A stale, evicted, corrupt, or partially populated shared structure SHALL fail to answer rather than answer with another tenancy's data.

Pressure applied to a shared structure by one tenant SHALL NOT cause another tenant's entries to be served incorrectly, and SHALL NOT reveal the presence, size, or activity of another tenancy.

#### Scenario: A lookup cannot cross the key boundary

- **WHEN** two tenancies hold entries whose natural keys would otherwise collide
- **THEN** a lookup performed for one tenancy returns only its own entry
- **AND** never the other's

#### Scenario: A degraded shared structure fails closed

- **WHEN** a shared projection is empty, stale, or partially populated
- **THEN** a lookup for a tenancy either returns that tenancy's correct entry or fails
- **AND** it never returns an entry belonging to another tenancy

#### Scenario: Eviction pressure does not leak

- **WHEN** one tenant causes heavy eviction in a shared structure
- **THEN** another tenant's lookups continue to return their own correct entries
- **AND** whether that tenant's lookup succeeds does not depend on the presence, absence, or volume of any other tenancy's entries

#### Scenario: Identifier spaces do not reveal neighbours

- **WHEN** a tenant observes the identifiers assigned to their own resources over time
- **THEN** those identifiers do not reveal how many resources other tenancies created in the same period

### Requirement: Isolation invariants hold under genuine contention

Every invariant in this capability SHALL hold when the operations that could violate it are executed concurrently from independent sessions against shared state, not only when they are executed in sequence. Where two concurrent operations would each individually be permitted but would jointly produce a state this capability forbids, at most the number of them that preserves the invariant SHALL succeed and the remainder SHALL be refused with a distinguishable outcome.

An invariant SHALL NOT depend for its enforcement on a check whose result can be invalidated between the check and the change it guards.

#### Scenario: Two tenancies claim one hostname at once

- **WHEN** two principals of different tenancies concurrently claim the same hostname, from independent sessions
- **THEN** exactly one claim succeeds
- **AND** the other is refused
- **AND** the hostname is attributed to exactly one tenancy afterwards

#### Scenario: The last owner cannot be removed by a race

- **WHEN** two owners of one entry concurrently remove each other's owner grant, from independent sessions
- **THEN** at least one owner grant covering that entry remains afterwards
- **AND** at least one of the removals is refused

#### Scenario: A released name is claimed once, not twice

- **WHEN** two principals of different tenancies concurrently create a resource under a name that has just become available
- **THEN** exactly one creation succeeds
- **AND** the resulting resource carries exactly one tenancy attribution
- **AND** the losing principal receives a refusal, not a resource shared with the winner

#### Scenario: A grant removed concurrently with a mutation

- **WHEN** a principal's grant on an entry is removed concurrently with a mutation of that entry authorized under it
- **THEN** the mutation either completes in full or is refused in full
- **AND** no partially applied change remains
- **AND** every subsequent mutation by that principal is refused

### Requirement: Refusals disclose nothing about another tenant

An error, refusal, or diagnostic delivered to a tenant or to a tenant's client SHALL NOT reveal the existence, identity, configuration, or activity of another tenancy. This SHALL hold for administrative operations, for proxied traffic, and for tunnel-level errors.

Where a resource is unavailable because another tenancy holds it, the refusal SHALL state that the resource is unavailable and SHALL NOT name or characterise the holder. Where a request does not match any mount, the response SHALL be the same regardless of whether some other tenancy has a mount that would have matched.

#### Scenario: A claimed hostname does not name its holder

- **WHEN** a principal attempts to claim a hostname already claimed in another tenancy
- **THEN** the refusal states that the hostname is unavailable
- **AND** it does not name the holding tenancy, its principals, or its mounts

#### Scenario: An unmatched request reveals no neighbour

- **WHEN** a request arrives on a shared hostname for a path that matches no mount of the addressed tenancy
- **AND** an identical path is mounted by a different tenancy
- **THEN** the response is identical to the response for a path mounted by nobody

#### Scenario: Diagnostics stay within the tenancy

- **WHEN** a refusal or diagnostic is returned to a tenant's client
- **THEN** it contains no hostname, path, identifier, backend address, or version belonging to another tenancy

#### Scenario: Internal detail is not reflected

- **WHEN** an unexpected internal failure occurs while serving a tenant
- **THEN** the response to that tenant's client contains no hostname, path, identifier, backend address, credential, or counter belonging to another tenancy
- **AND** it contains no internal state from which another tenancy's traffic or configuration could be described
- **AND** the full detail of the failure is retained where an operator can read it
