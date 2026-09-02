## Purpose

Defines the endpoint a sidecar dials to establish a tunnel: the verifiable identity the endpoint presents so a sidecar can decide whether to offer a credential at all, the protection the connection carries before any credential is read, the explicit identification of the framing spoken over it, the namespace the endpoint occupies and its separation from client traffic, the bounds that govern an accept path reachable by anyone who can route to it, and how the endpoint drains, is advertised, and is moved. Everything this capability describes happens before the authenticated identity exists, which is why its bounds and its disclosure rules are stated here rather than inherited from the capabilities that take over afterwards. It also owns the observed source of a connection *at this accept path*, because every pre-authentication bound in the system keys on that source and no capability defines it for a peer that has not authenticated. One concept, two surfaces: the edge-hygiene capability establishes the equivalent value for a client connection and owns the rule for honouring a source conveyed by a trusted intermediary; what is added here is that the same rule governs the accept path and that no authenticated identity is yet available to fall back on.

The endpoint is stated without choosing a transport. The framing carried over it is transport-independent by design, the transport for the first release is deliberately undecided, and every requirement here SHALL hold for any transport that can carry an ordered, protected, bidirectional octet stream.

## ADDED Requirements

### Requirement: The listener presents a verifiable endpoint identity on every connection

Authentication over the tunnel runs in one direction: the sidecar proves its entitlement to the proxy, and the proxy proves nothing to the sidecar by presenting a credential of its own. The sidecar's credential is therefore the only secret either party volunteers, and the sidecar's obligation to verify the endpoint before offering it — owned by the credential capability — requires a counterpart obligation here: the listener SHALL present, during connection setup and before any octet a peer sends could carry a credential, an identity bound to the name the endpoint is advertised under and backed by material a peer can verify.

The identity SHALL be presented on every connection the listener accepts, without exception for a re-establishment, a connection from a peer that has connected before, a connection arriving on an alternative advertised address, or a connection accepted while the listener is draining. There SHALL be no configuration, deployment mode, or address on which the listener accepts a tunnel connection while presenting no identity.

The identity SHALL be the platform's own class, as the custody capability's separation of that class from every tenant's requires. Material issued for a tenant hostname SHALL NOT be presented on the listener, and the listener SHALL NOT be reachable under a hostname whose identity is held on a tenant's behalf. Where the listener cannot present a valid identity — the material is absent, unreadable, expired, or does not cover the advertised name — it SHALL refuse the connection rather than proceed without one, and the refusal SHALL be recorded with that specific cause.

#### Scenario: Identity precedes anything a peer could send

- **WHEN** a sidecar connects to the listener
- **THEN** the endpoint's identity is presented before the listener reads any octet the peer sent
- **AND** a peer that abandons the connection immediately after receiving the identity has sent no credential and no establishment declaration

#### Scenario: Identity is presented on a re-establishment too

- **WHEN** a sidecar whose tunnel was lost connects again
- **THEN** the identity is presented on the new connection as on the first
- **AND** no state carried over from the previous connection substitutes for presenting it

#### Scenario: No tenant material is presented at the listener

- **WHEN** connections are accepted at the listener while tenant hostnames with their own identity material are being served at the client edge
- **THEN** every listener connection is presented the platform's own identity
- **AND** no tenant's identity material is presented on any listener connection

#### Scenario: An endpoint that cannot present an identity accepts nothing

- **WHEN** the listener's identity material is expired and no replacement is available
- **THEN** connections are refused
- **AND** no connection proceeds to read a peer's declaration or credential
- **AND** the refusal is recorded naming the identity material as the cause

#### Scenario: Identity that does not cover the advertised name is not presented

- **WHEN** the identity material available to the listener does not cover the name the endpoint is advertised under
- **THEN** the listener does not present it as though it did
- **AND** connections on that name are refused with the mismatch recorded

#### Scenario: A refusal while not accepting is either identified or not answered at all

- **WHEN** the listener is not accepting and a peer dials it
- **THEN** either the peer's connection is closed without the listener answering, or the answer it receives carries the endpoint identity
- **AND** the listener does not convey a refusal on a connection carrying no endpoint identity

### Requirement: The endpoint identity is renewable without invalidating a pinned fleet

The listener's identity material expires and is replaced, while sidecars verifying it are deployed in tenants' infrastructure and are not upgraded or reconfigured by the operator. A rotation that invalidates every sidecar's expectation simultaneously is an outage of the whole fleet's ability to reconnect, and it is not correctable from the operator's side.

The primary identity a sidecar is expected to verify SHALL therefore be the advertised endpoint name, which SHALL remain stable across renewal of the material behind it. Where a deployment requires a sidecar to expect a specific identity rather than a trust path — the case the credential capability permits explicitly — the retiring identity and its replacement SHALL both be verifiable at the endpoint throughout a configured overlap period: a peer expecting either SHALL establish, and neither SHALL be locked out while the other is in service. Withdrawing the retiring identity SHALL be a deliberate step distinct from introducing the replacement.

An impending expiry of the listener's identity material SHALL be surfaced as an operator-actionable condition ahead of the expiry by a configured margin, and SHALL remain observable for as long as it holds. Because a lapsed listener identity locks the entire fleet out and no sidecar-side action can correct it, this condition SHALL be raised whether or not a replacement is in progress, and SHALL NOT be satisfied by the stalled-replacement condition the custody capability defines. The count of connections verifying against each identity in service SHALL be separately retrievable, so that an operator can establish whether any peer still depends on the retiring material before withdrawing it.

#### Scenario: Renewal does not change what a sidecar verifies

- **WHEN** the listener's identity material is replaced while the advertised endpoint name is unchanged
- **THEN** a sidecar verifying against the advertised name continues to verify successfully
- **AND** no sidecar reconfiguration is required

#### Scenario: An overlap admits peers expecting either identity

- **WHEN** a replacement identity is introduced while the retiring one is still in service
- **THEN** a peer pinned to the retiring identity establishes a tunnel
- **AND** a peer pinned to the replacement establishes a tunnel
- **AND** neither is refused for a verification failure during the overlap

#### Scenario: Impending expiry is surfaced before it bites

- **WHEN** the listener's identity material will expire within the configured margin
- **THEN** the condition is observable as operator-actionable for as long as it holds
- **AND** it is observable before the material expires rather than at the moment connections begin failing

#### Scenario: Dependence on retiring material is countable before retirement

- **WHEN** two identities are presented during an overlap and some peers still verify against the retiring one
- **THEN** the count of connections verifying against each is separately retrievable
- **AND** an operator can determine that peers still depend on the retiring material

#### Scenario: Retiring material with dependants is not silent

- **WHEN** the retiring identity is withdrawn while connections were still verifying against it
- **THEN** the withdrawal is recorded together with how many connections had been verifying against it
- **AND** subsequent failures to establish are attributable to the withdrawal rather than reported as unexplained

### Requirement: The connection is confidential and integrity-protected before anything is read

Everything the listener reads before authentication is reachable by any party that can route to the endpoint. The credential a sidecar presents is the one secret in the system that travels toward the proxy, and it is presented on a connection whose peer is unauthenticated at the moment it is presented.

The listener SHALL establish confidentiality and integrity protection for a connection before it reads any octet of a protocol identification, an establishment declaration, or a credential. A connection on which protection has not been established SHALL be refused, and the listener SHALL NOT read, parse, buffer, or act on content received on it beyond what is required to refuse it.

The listener SHALL NOT offer a path by which an unprotected connection becomes protected in band: there SHALL be no negotiation, upgrade, or opportunistic promotion on an accepted connection, and a peer requesting one SHALL be refused. A deployment SHALL NOT be able to configure the listener to accept an unprotected tunnel connection on any address, including a loopback or private-network address, because an address believed to be private is not an authentication of the peer that reached it.

#### Scenario: An unprotected connection is refused, having been read from

- **WHEN** a peer opens an unprotected connection to the listener and immediately sends an establishment declaration and a credential
- **THEN** the connection is refused
- **AND** the declaration is not parsed and the credential is not evaluated
- **AND** no tunnel is established

#### Scenario: There is no in-band promotion to a protected connection

- **WHEN** a peer on an unprotected connection asks to upgrade it to a protected one
- **THEN** the request is refused
- **AND** the connection remains unprotected and carries no tunnel

#### Scenario: No configuration admits an unprotected tunnel

- **WHEN** a deployment is configured to accept tunnel connections without protection on a private address
- **THEN** the component refuses to start
- **AND** the refusal names that setting

#### Scenario: Abandoned protection setup yields nothing read

- **WHEN** a peer begins establishing protection, sends an establishment declaration and a credential, and never completes the protection setup
- **THEN** no framing identifier, declaration, or credential is parsed or evaluated
- **AND** no tunnel is established and no registry entry is created

#### Scenario: Octets before protection are discarded, not queued

- **WHEN** a peer sends a large volume of octets before protection is established
- **THEN** the octets are not retained
- **AND** the memory held for that connection does not grow with the volume sent

### Requirement: Protection policy is configurable above a floor that cannot be configured away

An operator needs to raise the protection policy — to require newer protocol versions or a narrower set of algorithms than the default — without a code change, because a policy that cannot be tightened in a deployment is a policy that ages into a liability. An operator SHALL NOT be able to lower it below a floor, because a setting that weakens the one protected hop the credential travels over is a setting whose consequence is invisible until it is exploited.

The listener SHALL accept configuration of the protocol versions and the algorithm set it will use. The component SHALL fix a floor for both, and configuration SHALL only be able to raise the effective policy above that floor. A configuration whose stated policy falls below the floor, or which disables the enforcement of the floor, SHALL cause the component to refuse to start with the offending item named. There SHALL be no setting, environment value, or operational command that admits a connection below the floor.

A peer offering no parameters the effective policy permits SHALL be refused during connection setup, with an outcome distinguishable from an authentication failure and from a refusal for an unidentified framing. A peer attempting to negotiate a version or algorithm below the effective policy SHALL be refused rather than served at the lower parameters. The effective policy in force, and the parameters negotiated for each established connection, SHALL be retrievable by an operator.

#### Scenario: A raised policy is honoured

- **WHEN** a deployment configures a protection policy stricter than the component's floor
- **THEN** the configured policy is the effective policy
- **AND** a peer offering only parameters the floor would have permitted but the configuration does not is refused

#### Scenario: A policy below the floor refuses to start

- **WHEN** a deployment configures a protocol version or algorithm below the component's floor
- **THEN** the component refuses to start
- **AND** the refusal names the offending configuration item and the floor

#### Scenario: The floor cannot be switched off

- **WHEN** a deployment sets any value intended to disable enforcement of the protection floor
- **THEN** the component refuses to start
- **AND** the refusal names that setting

#### Scenario: A downgrade attempt is refused, not accommodated

- **WHEN** a peer attempts to negotiate a protocol version below the effective policy
- **THEN** the connection is refused
- **AND** it is not served at the lower version
- **AND** the cause recorded for the operator is distinct from that of an authentication failure

#### Scenario: An unacceptable offer is distinguishable from a framing refusal

- **WHEN** one peer offers no permitted protection parameters and another offers permitted parameters but no recognised framing identifier
- **THEN** the two refusals carry distinct enumerated causes in the operator's records
- **AND** neither is recorded as an authentication failure

#### Scenario: Effective policy and negotiated parameters are observable

- **WHEN** an operator inspects the listener and an established tunnel connection
- **THEN** the effective protection policy is retrievable
- **AND** the parameters negotiated for that connection are retrievable

### Requirement: A transport-level peer identity never substitutes for the credential

A deployment MAY be configured to require the dialling peer to present an identity during connection setup as an additional gate. That identity SHALL be treated as an admission control on the accept path only. It SHALL NOT authenticate a sidecar, SHALL NOT determine or contribute to the tenant or the mount a tunnel is authorised for, and SHALL NOT permit the credential presentation to be skipped, weakened, or replaced.

Where a deployment requires a peer identity, a connection presenting none or presenting one the policy rejects SHALL be refused before any establishment declaration is read, with the refusal distinguishable from an authentication failure. Where a deployment requires none, a peer presenting one SHALL be neither privileged nor penalised by it.

The peer identity observed for a connection SHALL be recorded as an attribute of that connection, available to an operator alongside the authenticated identity, and SHALL be distinguishable from it in every record. A tunnel's tenant and mount SHALL derive solely from the credential presented, as the tenancy capability requires of all traffic attribution.

#### Scenario: A peer identity confers no tenant or mount

- **WHEN** a peer presents a transport-level identity naming a tenant and then presents a credential scoped to a different tenant's mount
- **THEN** the tunnel is authorised for the credential's tenant and mount
- **AND** the presented identity has no effect on that authorisation

#### Scenario: A required peer identity gates before the declaration

- **WHEN** a deployment requires a peer identity and a connection presents none
- **THEN** the connection is refused before any establishment declaration is read
- **AND** the refusal is distinguishable from an authentication failure

#### Scenario: A peer identity does not replace the credential

- **WHEN** a peer presents an identity the deployment's policy accepts and then presents no credential
- **THEN** no tunnel is established
- **AND** the connection is ended once the unauthenticated bound elapses

#### Scenario: An unrequired peer identity changes nothing

- **WHEN** a deployment requires no peer identity and a peer presents one
- **THEN** the connection proceeds exactly as one presenting none
- **AND** the tunnel's authorisation is unchanged by it

#### Scenario: The two identities are distinguishable in records

- **WHEN** an operator inspects an established tunnel whose connection presented a peer identity
- **THEN** the peer identity and the authenticated credential identity are both retrievable
- **AND** the record does not conflate them

### Requirement: The framing spoken over the connection is identified explicitly at setup

The listener SHALL require the peer to name, during connection setup, the framing it intends to speak, drawn from a published set of identifiers the listener serves. The listener SHALL NOT infer the framing from the first octets received, from the address or port the connection was accepted on, from a heuristic over the peer's behaviour, or from the absence of an alternative. A listener serving exactly one identifier SHALL still refuse a connection naming none.

A connection naming no framing SHALL be recorded with an enumerated cause distinct from that of a connection naming a framing the listener does not serve, and both SHALL be distinct from an authentication failure and from a protection-policy refusal. Because the served set is published configuration and discloses nothing about any credential, tenant, mount, or the installation's occupancy, a refusal in the framing class SHALL be permitted to convey its specific cause and that set to the peer, under the carve-out the disclosure requirement of this capability states.

The identifier named at setup identifies the framing only. The contract version the tunnel operates at SHALL be negotiated in band as the wire contract requires, and SHALL NOT be derived from the setup identifier, from the transport's own version, or from any other property of the connection. Changing the transport under an unchanged framing SHALL NOT change the identifier's meaning, and the listener SHALL serve more than one identifier concurrently where more than one is configured, so that a framing can be introduced without withdrawing the one in service.

#### Scenario: An explicitly named framing is served

- **WHEN** a peer names a framing identifier the listener serves
- **THEN** the connection proceeds to establishment under that framing
- **AND** the identifier is recorded for the connection

#### Scenario: An absent identifier is refused distinguishably

- **WHEN** a peer completes protection and names no framing identifier
- **THEN** the connection is refused
- **AND** the recorded enumerated cause names an absent framing identification
- **AND** it is distinct from the cause recorded for an unserved identifier

#### Scenario: Serving one identifier does not make naming it optional

- **WHEN** the listener is configured to serve exactly one framing identifier and a peer names none
- **THEN** the connection is refused for an absent framing identification
- **AND** the single served framing is not applied to it by default

#### Scenario: An unserved identifier is refused distinguishably

- **WHEN** a peer names a framing identifier the listener does not serve
- **THEN** the connection is refused
- **AND** the enumerated cause names an unserved framing identification
- **AND** no establishment declaration is read from the connection

#### Scenario: Framing is never inferred from content

- **WHEN** a peer names no framing identifier but sends octets that are a valid establishment declaration in a framing the listener serves
- **THEN** the connection is refused for an absent framing identification
- **AND** the octets are not interpreted as a declaration

#### Scenario: The setup identifier does not set the contract version

- **WHEN** two connections name the same framing identifier and declare different contract version ranges in band
- **THEN** each tunnel operates at the version its in-band negotiation determined
- **AND** neither version is derived from the setup identifier

#### Scenario: Two framings are served concurrently

- **WHEN** the listener is configured to serve two framing identifiers and peers name each
- **THEN** both connections are served under the framing they named
- **AND** introducing the second did not require withdrawing the first

### Requirement: The listener serves establishment and nothing else

The listener SHALL serve exactly one behaviour: accepting a connection, identifying its framing, and carrying it into tunnel establishment. It SHALL serve no other behaviour on its endpoint — no static content, no administrative operation, no liveness or readiness answer, no hostname-ownership challenge, no informational description of the installation, and no request forwarded to any mount.

A connection or request arriving at the listener that is not an establishment attempt in a served framing SHALL be refused with an enumerated cause, and SHALL NOT be answered by anything that reveals the software, its version, its configuration, or the installation's occupancy beyond what the refusal itself conveys. The listener SHALL NOT read a request body, and SHALL NOT establish any cookie, session, or client-identity value.

The listener SHALL generate no tunnel exchange on behalf of anything it receives, and no mount SHALL be looked up for anything arriving at it.

#### Scenario: An ordinary request to the listener is refused

- **WHEN** an ordinary client request arrives at the listener endpoint
- **THEN** it is refused with an enumerated cause
- **AND** no mount is looked up
- **AND** no tunnel exchange is generated

#### Scenario: The listener answers no probe

- **WHEN** a liveness or readiness probe is directed at the listener endpoint
- **THEN** it is refused rather than answered
- **AND** the readiness and liveness surfaces remain answerable at their own surfaces

#### Scenario: The listener answers no ownership challenge

- **WHEN** a hostname-ownership challenge is directed at the listener endpoint
- **THEN** it is refused
- **AND** the challenge continues to be answerable at the reserved challenge path the edge serves

#### Scenario: No body is read

- **WHEN** a peer sends a request with a large body to the listener endpoint
- **THEN** no body octets are consumed beyond what refusing the connection requires
- **AND** the memory held does not grow with the body's size

#### Scenario: Refusal discloses nothing about the installation

- **WHEN** the listener refuses a connection that is not an establishment attempt
- **THEN** the refusal names no software identity or version, no configuration value, and no count of tenants, mounts, or connections

### Requirement: The listener never directs a dialling peer to another endpoint

A sidecar that follows an instruction to connect elsewhere would present its credential to an endpoint it did not configure and did not verify against its configuration. The listener SHALL therefore never answer a dialling peer with a redirection, a referral, an alternative-endpoint advertisement, or any other instruction to connect to a different address, and the establishment surface SHALL define no field by which an endpoint address is conveyed to a peer as an instruction to move.

Where the listener cannot serve a connection for any reason — it is draining, it is at a bound, the framing is unserved, or the address is being retired — it SHALL refuse with an enumerated cause and leave the address the peer dials to that peer's own configuration.

A change to the address a sidecar dials SHALL be a change to discoverable configuration, as required elsewhere in this capability, and SHALL NOT be communicable in band on an accepted connection.

#### Scenario: No redirection is answered

- **WHEN** a peer connects to an address the operator intends to retire
- **THEN** the listener does not answer with a redirection or an alternative address
- **AND** it either serves the connection or refuses it with an enumerated cause

#### Scenario: The establishment surface carries no address instruction

- **WHEN** every field the establishment surface conveys to a peer is enumerated
- **THEN** none of them names an endpoint address for the peer to connect to instead

#### Scenario: A refusal while draining names the cause, not a destination

- **WHEN** a peer dials the listener while it is draining
- **THEN** the refusal names that the endpoint is not accepting
- **AND** it names no other endpoint to dial

#### Scenario: A bound refusal offers no alternative

- **WHEN** a peer is refused because the listener is at a connection bound
- **THEN** the refusal conveys no alternative address
- **AND** the peer's configured endpoint is unchanged by the refusal

### Requirement: The listener's namespace is reserved in the single reserved enumeration

The identifier the listener occupies — the path prefix where it is exposed on a hostname that also serves other traffic, and the hostname where it is exposed on one of its own — SHALL be reserved, and the reservation SHALL be made by contributing to the single enumerations the routing capabilities own rather than by a check maintained here. The path prefix SHALL be contributed to the one reserved-path enumeration the mount-point capability holds. A hostname dedicated to the listener SHALL be contributed to the reserved-hostname set the custom-domain capability holds, so that no tenant can claim it, obtain material for it, or scope a stored value to it.

The reserved prefix SHALL be the narrowest prefix the endpoint requires, SHALL apply at segment boundaries only, and SHALL NOT be extendable, overridden, or shadowed by any tenant-supplied value. This capability SHALL NOT maintain a second enumeration, a second check, or a second set of reserved names.

Changing where the listener is exposed SHALL change the contributed entry in the one enumeration, so that the reservation cannot fall out of step with what is served. Exposure at an identifier absent from the enumeration SHALL be a startup validation failure where it is detectable at startup, and where the enumeration diverges while the component is running it SHALL be raised as a defect condition and the endpoint SHALL cease to be served at that identifier rather than continue unreserved.

#### Scenario: The listener's identifier appears in the one enumeration

- **WHEN** an operator retrieves the reserved path prefixes in force
- **THEN** the prefix on which the listener is exposed appears among them
- **AND** no second enumeration of reserved prefixes exists to be retrieved

#### Scenario: A tenant cannot claim a listener hostname

- **WHEN** a tenant claims the hostname on which the listener is exposed
- **THEN** the claim is rejected
- **AND** the listener continues to be served on it
- **AND** a normalised variant of the hostname is equally rejected

#### Scenario: No mount can occupy the listener's prefix

- **WHEN** a mount definition exists whose prefix would otherwise match the listener's path prefix
- **THEN** requests under that prefix are not forwarded to any mount
- **AND** no tunnel exchange is generated for them

#### Scenario: The reservation cannot drift from what is served

- **WHEN** the listener is configured to be exposed at a different prefix
- **THEN** the contributed entry in the reserved enumeration names the new prefix
- **AND** where the enumeration diverges from what is served while the component runs, the divergence is raised as a defect and the unreserved identifier stops being served

#### Scenario: A similar prefix remains matchable

- **WHEN** a mount exists whose first path segment begins with the characters of the listener prefix's first segment but is longer
- **AND** a request arrives for that mount
- **THEN** the request is matched to the mount
- **AND** it is not diverted to the listener

### Requirement: The listener is distinct from the administrative and operational surfaces

The endpoint a sidecar dials, the administrative surface an operator or tenant uses, and the liveness, readiness and diagnostic surfaces SHALL be three separately identified surfaces. Each SHALL be reachable at its own identifier, each SHALL be separately observable, and none SHALL accept the establishment attempt or the credential belonging to another.

A credential presented at an administrative or operational surface SHALL authenticate nothing and SHALL establish no tunnel, and the surface SHALL NOT evaluate it as a credential. An establishment attempt directed at either surface SHALL be refused with an enumerated cause distinguishable from an authentication failure.

Where a deployment exposes more than one of these surfaces on one hostname, they SHALL remain distinct prefixes in the one reserved enumeration, and reserving one SHALL NOT reserve the others' siblings.

#### Scenario: A credential at a probe surface authenticates nothing

- **WHEN** a valid sidecar credential is presented to the readiness surface
- **THEN** no tunnel is established
- **AND** the value is not evaluated as a credential
- **AND** the probe answers only its own state

#### Scenario: An establishment attempt at the administrative surface is refused

- **WHEN** a tunnel establishment attempt is directed at the administrative surface
- **THEN** it is refused with an enumerated cause
- **AND** the cause is distinguishable from an authentication failure
- **AND** no tunnel is established

#### Scenario: The three surfaces are separately observable

- **WHEN** an operator retrieves the surfaces the component exposes
- **THEN** the listener, the administrative surface, and the operational surfaces are separately identified
- **AND** the connections accepted at each are separately countable

#### Scenario: The listener does not answer for another surface

- **WHEN** the administrative surface is unavailable
- **THEN** the listener does not begin answering requests directed at it
- **AND** tunnel establishment at the listener is unaffected

### Requirement: No client request reaches the listener

A request arriving on a client-facing surface SHALL never be delivered to the listener's establishment path, whatever its target, its fields, its body, or the mount definitions in force. Dispatch of a reserved target to the proxy's own handling before any mount lookup is owned by the edge capability; what this capability adds is that the proxy's own handling of the listener's reserved target on a client-facing surface is a refusal, not an establishment attempt.

A client request that carries a well-formed establishment declaration, names a served framing identifier in a field it supplies, or presents a valid sidecar credential SHALL establish no tunnel, SHALL be attributed to no tenant on account of it, and SHALL NOT cause the declaration or credential to be evaluated. No value a client supplies SHALL cause a client-facing connection to be treated as a tunnel connection.

#### Scenario: A client request for the listener's target is refused, not established

- **WHEN** a client request arrives on a client-facing surface targeting the listener's reserved prefix
- **THEN** it is refused by the proxy's own handling
- **AND** no establishment path is entered
- **AND** no mount is looked up and no tunnel exchange is generated

#### Scenario: A mount cannot deliver a client request to the listener

- **WHEN** a mount definition exists whose prefix would match the listener's reserved prefix
- **AND** a client request arrives for a target under it
- **THEN** the request reaches neither the listener nor any sidecar
- **AND** the outcome is the same as if the mount did not exist

#### Scenario: A client-supplied declaration establishes nothing

- **WHEN** a client request on a client-facing surface carries a well-formed establishment declaration and a valid sidecar credential
- **THEN** no tunnel is established
- **AND** neither the declaration nor the credential is evaluated
- **AND** the request is handled as ordinary client traffic or refused

#### Scenario: A client-supplied framing identifier changes nothing

- **WHEN** a client request names a served framing identifier in a field it supplies
- **THEN** the connection is not treated as a tunnel connection
- **AND** the request is handled as ordinary client traffic or refused

### Requirement: A tunnel connection is never treated as client traffic

A connection accepted at the listener SHALL never enter mount matching, hostname claim selection, or client-facing request handling, whatever it carries. Content received on such a connection SHALL be interpreted only as the framing named at setup, and SHALL NOT be interpreted as a client request even where it would parse as one.

No exchange SHALL be generated whose destination is the listener's own endpoint. The listener SHALL refuse to serve, and SHALL record as a defect, a configuration or a routing state under which an exchange dispatched to a sidecar would arrive back at the listener endpoint. Without this, a sidecar's own connection is proxied through the proxy it is connected to: the connection consumes an exchange and a sidecar slot, the loop is invisible in ordinary traffic records, and each iteration multiplies the occupancy attributed to the tenant.

Connections accepted at the listener and connections accepted at a client-facing surface SHALL be counted, bounded, and attributed separately, and no record SHALL conflate the two.

#### Scenario: An established tunnel connection produces no mount lookup

- **WHEN** a tunnel is established and carries traffic for an extended period
- **THEN** no mount lookup is performed for the tunnel connection itself
- **AND** no hostname claim is consulted for it

#### Scenario: Client-request-shaped content on a tunnel is not a client request

- **WHEN** a peer on an established tunnel connection sends octets that would parse as a client request
- **THEN** they are interpreted only as the framing named at setup
- **AND** the framing violation is reported rather than the content being served
- **AND** no mount is matched

#### Scenario: An exchange is never dispatched back to the listener

- **WHEN** a routing state exists under which an exchange dispatched to a sidecar would be directed at the listener's own endpoint
- **THEN** the exchange is refused with an enumerated cause
- **AND** the condition is recorded as a defect for the operator
- **AND** no connection to the listener is opened on behalf of it

#### Scenario: A self-proxy loop does not consume unbounded capacity

- **WHEN** a configuration that would proxy the listener endpoint through itself is put in force
- **THEN** no loop of connections forms
- **AND** the occupancy attributed to the tenant does not grow with each iteration

#### Scenario: Listener and client connections are counted separately

- **WHEN** an operator retrieves connection counts
- **THEN** connections accepted at the listener and at client-facing surfaces are separately retrievable
- **AND** no record attributes a listener connection to a mount or a client request

### Requirement: The observed source of a connection is derived from the connection, never claimed by the peer

Every bound, allowance, and record in this capability that is keyed on or reports an observed source rests on that source being an attribute the peer cannot choose. Before authentication there is no other unforgeable attribute available, so if a peer can state its own source it can mint a fresh allowance per attempt and every per-source bound here bounds nothing.

The listener SHALL derive the observed source of a connection from the connection itself. It SHALL NOT derive it, in whole or in part, from any value the peer states — in a framing identifier, in an establishment declaration, in a field of a request that reached the endpoint, or in a preamble the peer sends. A peer-stated source SHALL NOT become a limiting key, an accounting key for any bound, or a measurement label value.

That a conveyed source is honoured only from a configured set of trusted intermediaries, that from any other peer it is discarded rather than deprioritised, weighted, or recorded as a fallback, and that the value the component contributes is always the one it observed itself, are the edge-hygiene capability's rules for establishing a client identity, and they hold here as given against the same configured set rather than a second one. This capability SHALL NOT maintain a separate trusted-intermediary set, a separate parsing rule, or a separate name for the value. What it adds is that at this accept path the conveyed source SHALL additionally be honoured only on a connection from that intermediary which itself satisfies the protection policy, that where no intermediary set is configured no conveyed source SHALL be honoured from any peer, and that no chain is extended: this surface consumes a single source, not a chain, because there is no authenticated identity behind it to reconcile a chain against.

For a connection whose source was conveyed, both the intermediary and the conveyed source SHALL be separately retrievable, and no record SHALL report a conveyed source as though it had been observed directly. Where every connection arrives from one intermediary and no conveyed source is available, the per-source allowance collapses to a single source and therefore discriminates nothing; that collapse SHALL be an observable condition rather than a silent loss of the bound.

#### Scenario: A peer-stated source mints no fresh allowance

- **WHEN** a peer states a distinct source value on every connection it opens, in every field it controls
- **THEN** all of those connections are accounted against one observed source
- **AND** the per-source allowance is reached at the same point as for a peer stating a constant value
- **AND** no measurement label value is derived from the stated values

#### Scenario: A conveyed source from an unconfigured peer is ignored

- **WHEN** a peer that is not in the configured intermediary set conveys an originating source
- **THEN** the connection is accounted against the source observed from the connection itself
- **AND** the conveyed value is not recorded as the connection's source and not used as any key

#### Scenario: With no intermediary configured, nothing conveyed is honoured

- **WHEN** no intermediary set is configured and a peer conveys an originating source
- **THEN** the conveyed value is ignored
- **AND** the accounting is identical to that for a peer conveying nothing

#### Scenario: A conveyed source is not reported as directly observed

- **WHEN** a configured intermediary conveys an originating source on a connection satisfying the protection policy
- **THEN** the intermediary and the conveyed source are separately retrievable for that connection
- **AND** no record presents the conveyed source as directly observed

#### Scenario: A collapsed per-source allowance is announced

- **WHEN** every connection arrives from one intermediary and no conveyed source is available
- **THEN** the condition that the per-source allowance discriminates a single source is observable
- **AND** the per-instance pre-authentication bound and the total connection bound continue to be enforced

#### Scenario: An intermediary that fails the protection policy conveys nothing

- **WHEN** a peer in the configured intermediary set connects without satisfying the protection policy and conveys an originating source
- **THEN** the connection is refused for the protection policy
- **AND** the conveyed source is not read, retained, or used as any key

### Requirement: Connections in the pre-authentication state are bounded

Every connection the listener has accepted but not yet authenticated occupies capacity on behalf of a party whose identity is not established. There is no tenant to charge it to, so it cannot be bounded by the per-tenant dimensions, and any party that can route to the endpoint can create it.

The listener SHALL enforce a configured bound on the number of connections concurrently in the pre-authentication state. Reaching the bound SHALL cause a further connection to be refused; it SHALL NOT displace a pre-authentication connection already admitted, SHALL NOT disturb any established tunnel, and SHALL NOT delay or fail an authentication already in progress. Capacity SHALL be released when a connection authenticates, is refused, or ends.

The bound SHALL be accounted per accepting instance and, separately, per observed source, so that one source cannot occupy the whole allowance of the instance it reached. It SHALL NOT be accounted across instances: an installation-wide count of unauthenticated connections would require coordination between instances on every accept, which is work an unidentified party can cause at an instance it did not connect to, and which this capability forbids elsewhere. Consumption in this state SHALL NOT be attributed to any tenant, and reaching the bound SHALL NOT be recorded as a per-tenant bound refusal. Reaching the bound SHALL be observable while it holds, per instance, and countable by cause.

#### Scenario: The bound refuses further pre-authentication connections

- **WHEN** the number of connections in the pre-authentication state reaches the configured bound
- **AND** a further connection is opened
- **THEN** it is refused
- **AND** no already-admitted pre-authentication connection is displaced

#### Scenario: Established tunnels are unaffected

- **WHEN** the pre-authentication bound is held at its ceiling by peers that never authenticate
- **THEN** established tunnels continue to carry exchanges
- **AND** their exchanges are neither refused nor reset

#### Scenario: An authentication in progress is not sacrificed

- **WHEN** the pre-authentication bound is reached while a legitimate peer is midway through presenting its credential
- **THEN** that authentication completes
- **AND** the connection is not closed to make room

#### Scenario: One source cannot occupy the whole allowance

- **WHEN** one observed source opens pre-authentication connections as fast as it can
- **THEN** it is refused at its own per-source allowance
- **AND** a peer from another source is still admitted into the pre-authentication state

#### Scenario: Pre-authentication consumption is charged to no tenant

- **WHEN** the pre-authentication bound is reached
- **THEN** the refusals are not recorded against any tenant
- **AND** no tenant's per-tenant bound accounting changes
- **AND** the refusals are counted under the pre-authentication bound by name

#### Scenario: Capacity is released on authentication

- **WHEN** a connection in the pre-authentication state authenticates
- **THEN** the capacity it occupied in that state is released
- **AND** a further connection is admitted into the pre-authentication state

#### Scenario: One instance at its bound does not refuse at another

- **WHEN** one accepting instance holds its pre-authentication bound at the ceiling
- **THEN** a peer dialling a different instance is admitted into the pre-authentication state there
- **AND** the accepting instance consulted no other instance in order to admit or refuse

### Requirement: A connection may remain unauthenticated only for a bounded total time

The listener SHALL enforce a configured bound on the total elapsed time from accepting a connection to that connection being authenticated. The bound SHALL be one budget covering every phase before authentication — establishing protection, identifying the framing, receiving the establishment declaration, and presenting and evaluating the credential — so that no phase can be stretched at the expense of the whole and no progress in one phase resets the budget.

Exceeding the budget SHALL end the connection with an enumerated cause naming an unauthenticated timeout, distinguishable from an authentication failure, from a version refusal, from a protection-policy refusal, and from a capacity refusal. A peer that sends octets slowly, sends them in small increments, or completes each phase just inside its own bound SHALL be ended at the same budget as a silent one.

The wire contract's bound on waiting for a peer's establishment declaration SHALL operate within this budget rather than in addition to it: the connection ends at whichever elapses first, and the cause conveyed identifies which one did. The budget SHALL be settable in a deployment so the boundary can be exercised without waiting a long period.

#### Scenario: A silent peer is ended at the budget

- **WHEN** a peer opens a connection and sends nothing
- **THEN** the connection is ended once the unauthenticated budget elapses
- **AND** the cause names an unauthenticated timeout

#### Scenario: A trickling peer is ended at the same budget

- **WHEN** a peer sends a small number of octets at intervals just short of every phase bound
- **THEN** the connection is ended at the same total budget as a silent peer
- **AND** progress in one phase does not extend the budget

#### Scenario: The budget covers protection setup, not only the declaration

- **WHEN** a peer stalls midway through establishing protection and never completes it
- **THEN** the connection is ended once the unauthenticated budget elapses
- **AND** the budget is not measured from the completion of protection

#### Scenario: The declaration bound operates inside the budget

- **WHEN** a peer completes protection and framing identification and then withholds its declaration
- **THEN** the connection ends at whichever of the declaration bound and the unauthenticated budget elapses first
- **AND** the cause conveyed identifies which of the two ended it

#### Scenario: The timeout is distinguishable from every other refusal

- **WHEN** connections are ended for an unauthenticated timeout, an authentication failure, a protection-policy refusal, and a capacity refusal
- **THEN** the four carry four distinct enumerated causes in the operator's records

#### Scenario: Many stalled connections do not accumulate

- **WHEN** a large number of peers open connections and never authenticate
- **THEN** each is ended once the budget elapses
- **AND** the state retained by the listener does not grow with the number of them over time

### Requirement: Everything read before authentication is bounded and is not retained

The listener SHALL enforce a configured bound on the total octets it will read from a connection before that connection is authenticated, covering the framing identification, the establishment declaration, and the credential presentation together. It SHALL enforce the bound before the content is parsed, and SHALL NOT allocate for a stated length before the octets arrive.

Exceeding the bound SHALL end the connection with an enumerated cause distinguishable from an unauthenticated timeout and from an authentication failure. Content read before authentication SHALL NOT be retained beyond what evaluating it requires, and SHALL NOT appear in any emitted record except as bounded, labelled values: an unrecognised framing identifier, an oversized declaration, and unrecognised names within a declaration SHALL be counted rather than recorded individually, consistently with the wire contract's treatment of unrecognised declaration content.

Memory the listener holds for one unauthenticated connection SHALL be bounded by configuration independently of what the peer sends, and the total memory held for all unauthenticated connections SHALL be bounded by that value together with the pre-authentication connection bound.

#### Scenario: The octet bound ends the connection

- **WHEN** a peer sends more octets before authenticating than the configured bound permits
- **THEN** the connection is ended
- **AND** the enumerated cause names the exceeded pre-authentication read bound
- **AND** it is distinguishable from an unauthenticated timeout

#### Scenario: A stated length does not cause an allocation

- **WHEN** a peer declares a length far above the pre-authentication read bound and sends no further octets
- **THEN** no allocation is made for the stated length
- **AND** the connection is refused for the exceeded bound

#### Scenario: A huge framing identifier is bounded

- **WHEN** a peer sends a framing identifier longer than the configured bound
- **THEN** the connection is refused
- **AND** the identifier is not recorded in full

#### Scenario: Pre-authentication content is not recorded individually

- **WHEN** peers send unrecognised framing identifiers and declarations carrying many unrecognised names
- **THEN** the occurrences are counted by cause
- **AND** the individual values are not recorded as distinct entries
- **AND** no measurement label is derived from them

#### Scenario: Memory for unauthenticated connections is bounded in total

- **WHEN** the pre-authentication connection bound is fully occupied by peers each sending as much as the read bound permits
- **THEN** the memory held for them does not grow further however long the peers persist
- **AND** lowering either configured bound lowers the memory held at full occupancy
- **AND** the memory held is unchanged by which octets the peers chose to send

### Requirement: The total number of connections the listener holds is bounded

The listener SHALL enforce a configured bound on the total number of connections it holds, counting authenticated and unauthenticated connections together. This bound SHALL be independent of the pre-authentication bound and of every per-tenant bound: a population of legitimately authenticated tunnels can exhaust an accept path without any single tenant reaching a bound of its own.

Reaching the total bound SHALL cause a further connection to be refused with an enumerated cause naming the total connection bound, distinguishable from the pre-authentication bound, from a per-tenant or per-credential bound, and from an authentication failure. It SHALL NOT close, displace, or degrade an established tunnel in order to admit a new one. Capacity SHALL be released when a connection ends.

Operating at the total bound SHALL be an enumerated degraded condition, observable continuously for as long as it holds and stating when it began, because at that point no sidecar can re-establish a lost tunnel at that instance and the operator's remedy is capacity rather than configuration.

#### Scenario: The total bound refuses new connections

- **WHEN** the total number of connections the listener holds reaches the configured bound
- **AND** a further connection is opened
- **THEN** it is refused with the cause naming the total connection bound

#### Scenario: No established tunnel is displaced

- **WHEN** the total bound is reached and further connections are attempted continuously
- **THEN** every established tunnel remains established
- **AND** no exchange in flight is reset to admit a new connection

#### Scenario: The total bound is distinguishable from the others

- **WHEN** connections are refused for the total bound, for the pre-authentication bound, and for a per-tenant bound
- **THEN** the three carry three distinct enumerated causes
- **AND** an operator can tell which bound was reached without inspecting connection contents

#### Scenario: Operating at the bound is announced while it holds

- **WHEN** the listener has been at its total connection bound for a period
- **THEN** an operator inspecting the component finds that condition listed with the time it began
- **AND** the component does not report itself as fully healthy during it

#### Scenario: Capacity is released as connections end

- **WHEN** the listener is at its total bound and an established tunnel ends
- **THEN** the capacity it held is released
- **AND** a subsequent connection is admitted

### Requirement: Work performed for an unauthenticated peer is bounded and cheap

Before a connection is authenticated, all of the work the listener performs for it is work an unidentified party can cause. The listener SHALL therefore complete its cheap admission checks — the protection policy, the framing identification, the pre-authentication bounds, and the rate limit — before performing any work whose cost is proportional to the installation or that touches a durable store, and the rate at which expensive work is performed SHALL NOT rise with the rate of attempts.

The rate limit applied at the accept path SHALL be the one the credential capability defines, keyed on the observed source as this capability determines it where a presentation has not resolved, and on the credential's identity where it has. The listener SHALL NOT introduce a second limiter, a second key, or a second allowance for the same attempts.

A flood of connections that never authenticate SHALL NOT cause a durable-store query or secret-protection work per attempt, SHALL NOT prevent an unrelated tunnel from being established, and SHALL NOT prevent established tunnels from carrying exchanges. Nothing about the accept path SHALL cause work at an instance other than the one that accepted the connection until the connection has authenticated.

#### Scenario: A flood causes no per-attempt durable work

- **WHEN** a party opens connections as fast as it can and never presents a credential
- **THEN** no durable-store query is performed for those attempts
- **AND** no secret-protection work is performed for them

#### Scenario: Expensive work does not scale with the attempt rate

- **WHEN** the rate of unresolvable credential presentations is increased by an order of magnitude
- **THEN** the rate at which secret-protection work is performed does not rise proportionally
- **AND** it remains bounded by the configured limit

#### Scenario: Legitimate establishment continues during a flood

- **WHEN** a flood of connections that never authenticate is in progress
- **THEN** a sidecar presenting a valid credential still establishes a tunnel
- **AND** established tunnels continue to carry exchanges throughout

#### Scenario: Exhausting the allowance once exhausts it entirely

- **WHEN** a peer exhausts the accept path's allowance for its observed source and continues to attempt
- **THEN** no further attempt from that source is admitted at the accept path
- **AND** it is not admitted by a second allowance keyed on the same source
- **AND** varying the framing identifier it names does not obtain a fresh allowance

#### Scenario: An unauthenticated connection causes no installation-wide work

- **WHEN** a party opens many connections at one instance and never authenticates
- **THEN** no other instance performs work on behalf of those connections
- **AND** establishment at other instances is unaffected

### Requirement: Established tunnels are bounded per tenant, per mount, and per credential, accounted once

The listener admits a connection that becomes a registry entry, so its admission point is a second place a per-tenant bound could be applied. The listener SHALL apply the same configured per-tenant and per-mount registration bound the registry capability defines, accounted once across both admission points, and SHALL NOT introduce a parallel per-tenant dimension of its own. A tenant's total occupancy on that dimension SHALL NOT be exceedable by arriving through both surfaces.

The listener SHALL additionally enforce a configured bound on the number of concurrent tunnels admitted for one credential. This is not a per-tenant dimension and does not enlarge the closed enumeration the tenancy capability owns: it is a narrowing, within one tenant's already-bounded registration allowance, of what a single credential may occupy of it, so that a leaked credential cannot consume the whole allowance its tenant holds. Its value SHALL NOT be able to exceed the per-tenant registration bound in force, and a configuration in which it does SHALL cause the component to refuse to start with both items named.

A refusal for any of these bounds occurs after the credential has authenticated, so the refusal SHALL name the exceeded bound to the peer, as the registry capability requires. It SHALL NOT displace an established tunnel, SHALL NOT make an existing entry ineligible, and SHALL release capacity when a tunnel ends. Exhausting a bound for one tenant or one credential SHALL NOT affect any other tenant's or credential's ability to establish.

#### Scenario: A per-credential bound refuses without displacing

- **WHEN** the configured number of concurrent tunnels for one credential is already established
- **AND** a further connection presents the same credential
- **THEN** it is refused with the exceeded bound named
- **AND** every established tunnel for that credential remains established and eligible

#### Scenario: A per-tenant bound is one value accounted once

- **WHEN** a tenant's tunnels are established such that the per-tenant registration bound is reached
- **THEN** the bound reached is the same configured value whether the refusal occurred at the listener or at registration
- **AND** the tenant's total does not exceed that value
- **AND** the outcome names the same bound in either case

#### Scenario: One credential at its bound does not affect its siblings

- **WHEN** one credential holds its maximum number of concurrent tunnels and is being refused
- **THEN** another credential of the same tenant and the same mount still establishes a tunnel
- **AND** the tenant's registration allowance is consumed by both credentials together rather than by each separately

#### Scenario: A per-credential bound above the tenant bound refuses startup

- **WHEN** the per-credential tunnel bound is configured above the per-tenant registration bound in force
- **THEN** the component refuses to start
- **AND** the refusal names both items

#### Scenario: A bound refusal is not an authentication failure

- **WHEN** a valid credential is refused because a bound is exhausted
- **THEN** the peer is told the exceeded bound
- **AND** the outcome is distinguishable from an authentication failure
- **AND** the peer does not treat the credential as invalid

#### Scenario: Lowering the one configured value lowers it at both admission points

- **WHEN** the per-tenant registration bound is lowered and a tenant then establishes tunnels until it is refused
- **THEN** the number it holds reflects the lowered value
- **AND** it reflects it whether the tunnels were admitted at the listener or registered directly
- **AND** no separate listener-side per-tenant value had to be lowered as well

#### Scenario: Capacity is released when a tunnel ends

- **WHEN** a credential at its per-credential bound loses one of its tunnels
- **THEN** the capacity is released
- **AND** a subsequent connection presenting that credential is admitted

### Requirement: Overlapping connections from one credential are admitted rather than resolved by closure

A sidecar re-establishing a tunnel, rotating a credential, or being redeployed will briefly hold two connections bearing the same credential, and the proxy cannot distinguish that from a duplicate. The listener SHALL admit a second connection bearing a credential already in use, within the per-credential bound, and SHALL NOT close, drain, or make ineligible an existing tunnel on the grounds that another connection presented the same credential.

The per-credential bound SHALL have a floor sufficient to permit such an overlap, and a configuration setting it below that floor SHALL cause the component to refuse to start with the item named. Superseding an earlier incarnation, and the guarantee that a superseded incarnation never removes its successor, are owned by the registry capability; what this capability adds is that the listener's admission does not pre-empt that resolution by refusing or severing at accept time.

#### Scenario: A second connection with the same credential is admitted

- **WHEN** a sidecar holding an established tunnel opens a second connection presenting the same credential
- **THEN** the second connection is admitted within the per-credential bound
- **AND** the first tunnel is not closed or made ineligible on account of it

#### Scenario: A re-establishment overlap loses no work

- **WHEN** a sidecar re-establishes while exchanges are in flight on its previous tunnel
- **THEN** the new tunnel is established
- **AND** the in-flight exchanges on the previous tunnel are not reset by the admission of the new one

#### Scenario: The per-credential bound cannot forbid an overlap

- **WHEN** a deployment configures a per-credential tunnel bound below the overlap floor
- **THEN** the component refuses to start
- **AND** the refusal names that configuration item and the floor

#### Scenario: Admission does not pre-empt supersession

- **WHEN** two connections bearing one credential are established concurrently
- **THEN** the listener refuses neither at accept time on the grounds of the other
- **AND** which entry serves traffic is resolved by the registry rather than by the accept path

### Requirement: Failed attempts that never resolved to a credential do not deny it service

A denial mechanism that locks out a credential after failed attempts is a mechanism by which anyone who learns a credential's non-secret component can take a tenant's mount offline. The listener SHALL NOT deny establishment to a credential on the basis of attempts that did not resolve to that credential, and SHALL NOT place a credential into a state in which a subsequent valid presentation is refused because of prior failures.

Limiting of attempts that did not authenticate SHALL be keyed on the observed source, as the credential capability requires, and its effect SHALL be confined to that source. This SHALL include an attempt whose non-secret component resolved to a stored record but whose secret did not verify: the non-secret component is not a secret, so an attempt bearing it SHALL NOT be charged to the credential it names. Only a presentation that authenticated SHALL be limited on that credential's identity, as that capability also requires; reaching that allowance SHALL refuse further attempts for that credential without invalidating it, without revoking it, and without extending to any other credential of the same tenant or mount. An allowance SHALL be restored by the passage of time alone, without an operator action, so that a transient burst does not become a permanent denial.

A credential's inability to establish because of limiting SHALL be observable to an operator as such, distinguishable from an authentication failure and from a revocation, so that a legitimate sidecar reporting repeated refusals is diagnosable.

#### Scenario: A third party cannot lock out a credential

- **WHEN** a party makes a large number of failed presentations bearing a credential's non-secret component with the wrong secret
- **THEN** the legitimate holder of that credential still establishes a tunnel
- **AND** the credential is neither invalidated nor revoked by the failures

#### Scenario: Limiting is confined to the observed property

- **WHEN** unresolved attempts from one observed source exhaust that source's allowance
- **THEN** a sidecar presenting a valid credential from another source establishes a tunnel
- **AND** the exhausted allowance does not extend to the credential's identity

#### Scenario: A credential's own allowance does not invalidate it

- **WHEN** a resolved credential exhausts its own allowance
- **THEN** further attempts for it are refused
- **AND** the credential remains valid
- **AND** other credentials of the same tenant and mount are unaffected

#### Scenario: Limiting is diagnosable as limiting

- **WHEN** a legitimate sidecar is being refused because of limiting
- **THEN** an operator can determine that limiting is the cause
- **AND** it is distinguishable from an authentication failure and from a revocation

#### Scenario: An allowance is restored without intervention

- **WHEN** a credential exhausts its own allowance and then presents nothing for a period
- **THEN** a subsequent presentation of that credential establishes a tunnel
- **AND** no operator action was required to restore it

### Requirement: The accept path is resourced independently of the client edge

If a flood of client traffic can exhaust the resources tunnel establishment needs, every mount loses the ability to replace a lost sidecar at exactly the moment its traffic is highest. The listener's accept path SHALL therefore hold its own capacity: the connections, memory, and admission allowances it consumes SHALL be accounted and bounded separately from those of the client-facing surfaces, and exhausting one SHALL NOT exhaust the other.

Reaching a bound on one SHALL produce the outcome belonging to that surface and not the other's, so an operator can tell a client-edge saturation from a listener saturation. The two SHALL be separately observable in every measurement that admits or refuses work.

Where both surfaces are served by one component, this separation SHALL hold within it. Where the client edge is a separate component, the listener SHALL remain reachable and functional while that component is unavailable, and SHALL NOT depend on it to accept or authenticate a connection.

#### Scenario: A client flood does not prevent establishment

- **WHEN** client-facing surfaces are saturated and refusing requests at their bounds
- **THEN** a sidecar still establishes a tunnel at the listener
- **AND** its establishment is not refused for a client-edge bound

#### Scenario: A listener flood does not stop client traffic

- **WHEN** the listener is at its total connection bound and refusing connections
- **THEN** client requests to mounts with connected sidecars continue to be served
- **AND** they are not refused for a listener bound

#### Scenario: The two saturations are distinguishable

- **WHEN** a bound is reached at the client edge and, separately, at the listener
- **THEN** the outcomes recorded name the surface whose bound was reached
- **AND** an operator can tell the two conditions apart from the signals alone

#### Scenario: An unavailable client edge does not disable the listener

- **WHEN** the client-facing edge component is unavailable
- **THEN** sidecars continue to establish and authenticate tunnels at the listener
- **AND** the registry continues to reflect their entries

### Requirement: A refusal is specific to the operator and opaque to an unauthenticated peer

Every refusal at the accept path SHALL produce a record naming the specific cause, the phase the connection had reached, the observed source, the identity presented if any, and the time. The operator SHALL be able to count refusals by cause and to distinguish, without inspecting connection contents, a protection-policy refusal, an absent framing identification, an unserved framing identification, an oversized pre-authentication read, an unauthenticated timeout, a pre-authentication bound, a total connection bound, a rate limit, and an authentication failure.

What the peer is told SHALL depend on whether it has authenticated. Before a credential has been presented, a refusal SHALL convey only the class of the refusal — protection, framing, capacity, or timeout — and SHALL convey nothing about any credential, mount, tenant, or hostname. Within the protection and framing classes the specific cause and the served framing identifiers SHALL be permitted, because both are published configuration and a tenant diagnosing a sidecar it deployed itself needs them. Within the capacity and timeout classes nothing SHALL distinguish one instance of the class from another and no occupancy figure SHALL be conveyed, because those figures describe what other tenants hold. At and after credential presentation, the refusal SHALL convey exactly what the credential capability permits and nothing further, and the listener SHALL NOT add a field, a description, or a timing difference that separates causes that capability requires to be indistinguishable.

Refusal SHALL be cheap: no refusal path SHALL perform work proportional to what the peer sent, and the listener SHALL continue to accept and authenticate legitimate peers while refusing at a sustained rate. Where the volume of individual refusal records is reduced, that reduction SHALL be the summarisation the observability capability defines, which states the number suppressed and leaves counts by cause exact; this capability SHALL NOT introduce a suppression rule of its own.

#### Scenario: The operator can separate every accept-path cause

- **WHEN** connections are refused for each of the enumerated accept-path causes in turn
- **THEN** each refusal is recorded with its own distinct cause
- **AND** the counts by cause are separately retrievable

#### Scenario: A pre-credential capacity refusal conveys only the class

- **WHEN** one peer is refused for a pre-authentication bound and another for a total connection bound, both before presenting a credential
- **THEN** both are told only that capacity refused them
- **AND** neither refusal indicates which bound, nor any occupancy figure
- **AND** the operator's records distinguish the two

#### Scenario: A framing refusal is specific where a capacity refusal is not

- **WHEN** a peer is refused for an unserved framing identifier and another for a capacity bound
- **THEN** the framing refusal conveys its specific cause and the served identifiers
- **AND** the capacity refusal conveys neither a specific cause nor any figure

#### Scenario: A refusal reveals nothing about a credential or mount

- **WHEN** a peer is refused before presenting a credential
- **THEN** the refusal names no credential, mount, tenant, or hostname
- **AND** it does not indicate whether any of them exists

#### Scenario: The listener adds nothing that separates authentication causes

- **WHEN** an unknown, an expired, and a revoked credential are each presented at the listener
- **THEN** the phase, framing identifier, observed source, and elapsed time the listener attaches to the three refusals do not differ in a way that separates them
- **AND** the listener adds no field to the refusal beyond what the credential capability permits

#### Scenario: Refusal work does not scale with what was sent

- **WHEN** a peer sends as much as the pre-authentication read bound permits and is refused
- **THEN** the work performed to refuse it does not grow with the octets sent
- **AND** the record emitted does not contain them

#### Scenario: A refusal storm does not stop legitimate establishment

- **WHEN** refusals occur at a sustained rate far above the configured record volume
- **THEN** a sidecar presenting a valid credential still establishes a tunnel throughout
- **AND** the counts of refusals by cause remain exact despite any reduction in individual records

### Requirement: Every connection is attributable to an enumerated phase while it is open

A connection that never authenticates produces no exchange, so the diagnostics built around exchanges cannot see it. An operator investigating sidecars that cannot connect needs to see where they are stopping.

The listener SHALL attribute every connection it holds to a phase drawn from a stable enumerated set distinguishing at minimum: accepted, protection being established, framing being identified, awaiting the establishment declaration, credential being evaluated, established, draining, and ended. For every connection currently open, the operator SHALL be able to obtain its phase, how long it has been in that phase, its age since accept, its observed source, its framing identifier where one was named, and its negotiated protection parameters. For every connection that has ended, the terminal phase and the enumerated cause SHALL be recorded.

The phase enumeration, and the enumerated causes a connection is refused or ended with at this accept path, SHALL be published as connection-level vocabularies under the observability capability's registry, bound by its stable-identifier obligation and separately countable by cause. They SHALL NOT be mapped into that capability's per-exchange outcome enumeration, because a connection that never authenticates produces no exchange to attribute an outcome to; where a tunnel that had been serving ends, this vocabulary describes the connection and the per-exchange outcome describes each exchange it abandoned. Neither SHALL be a second private enumeration maintained here. Phases before authentication SHALL carry no tenant attribution, and any measurement label for them SHALL collapse to one reserved value rather than deriving a value from what the peer supplied. Counts of connections by phase SHALL return to their resting values once the connections have ended.

#### Scenario: A connection stuck before authentication is visible

- **WHEN** a peer has been awaiting the establishment declaration phase for some time
- **THEN** an operator can obtain that connection's phase, its time in that phase, its age, and its observed source
- **AND** finding it does not require it to have produced an exchange

#### Scenario: A refused connection records its terminal phase

- **WHEN** a connection is refused during framing identification
- **THEN** the record names that phase as the terminal phase
- **AND** it names the enumerated cause of the refusal

#### Scenario: The phase vocabulary is the published one

- **WHEN** the phase values the listener produces are enumerated
- **THEN** each appears in the single published registry, stated to be a connection-level vocabulary
- **AND** each is countable by cause
- **AND** none is mapped to a per-exchange outcome value
- **AND** no second private enumeration of connection phases exists

#### Scenario: Pre-authentication phases carry no tenant attribution

- **WHEN** many connections are held in pre-authentication phases by unidentified peers
- **THEN** none is attributed to a tenant
- **AND** every measurement label for them collapses to one reserved value
- **AND** no label value is derived from anything the peers supplied

#### Scenario: Phase counts return to rest

- **WHEN** a period of connection churn ends and every connection has reached a terminal phase
- **THEN** the counts of connections in each non-terminal phase return to the values they held before the churn

### Requirement: The listener drains by ceasing to accept while established tunnels continue

The listener SHALL support a state in which it accepts no new connection while every established tunnel remains established and continues to carry exchanges. Entering the state SHALL NOT end any tunnel, reset any exchange, or make any registry entry ineligible.

Where the state is entered as part of withdrawing an instance, it SHALL be a phase of the one ordered withdrawal lifecycle the registry capability defines, governed by that one deadline, and this capability SHALL NOT introduce a second ordering or a second deadline. Where an operator suspends the accept path on its own — to quiesce establishment without withdrawing the instance — that suspension SHALL be reversible, and SHALL be distinguishable from a withdrawal, which is not.

The state SHALL be observable continuously while it holds, stating when it began, why it began, and how many tunnels remain established. The readiness signal SHALL reflect it. A peer dialling a listener in this state SHALL be refused with an enumerated cause naming that the endpoint is not accepting, distinguishable from an authentication failure, from a capacity refusal, and from a credential-no-longer-valid ending, so that a sidecar backs off and retries rather than treating its credential as invalid or retrying tightly.

#### Scenario: Established tunnels survive the listener ceasing to accept

- **WHEN** the listener stops accepting while tunnels are established and exchanges are in flight
- **THEN** every established tunnel remains established
- **AND** its in-flight exchanges complete normally
- **AND** no registry entry becomes ineligible on account of it

#### Scenario: The state is observable with its onset and reason

- **WHEN** the listener has not been accepting for a period
- **THEN** an operator can observe that it is not accepting, when that began, why it began, and how many tunnels remain
- **AND** the reason distinguishes an operator suspension, an instance withdrawal, and a received termination signal

#### Scenario: Readiness reflects the state

- **WHEN** the listener is not accepting
- **THEN** the readiness signal reports that the component is not ready to take new work
- **AND** the liveness signal does not report failure on that account

#### Scenario: An operator suspension is reversible and a withdrawal is not

- **WHEN** an operator suspends the accept path and later resumes it
- **THEN** the listener accepts connections again
- **AND** the same resumption applied to an instance in withdrawal has no effect and the instance continues to withdraw

#### Scenario: A dialling peer is told the endpoint is not accepting

- **WHEN** a sidecar dials a listener that is not accepting
- **THEN** the refusal names that the endpoint is not accepting
- **AND** it is distinguishable from an authentication failure, a capacity refusal, and a credential-no-longer-valid ending
- **AND** it is a cause the re-establishment behaviour the registry capability defines treats as retryable rather than as an invalid credential

#### Scenario: Withdrawal stops acceptance before any tunnel ends

- **WHEN** an instance begins withdrawal while holding established tunnels
- **THEN** it stops accepting new connections before it ends any tunnel
- **AND** it does so under the one withdrawal deadline rather than a deadline of the listener's own

### Requirement: The endpoint a sidecar dials is discoverable configuration

A sidecar cannot be configured without knowing what to dial and what identity to expect. That information SHALL be discoverable configuration rather than folklore: the platform SHALL make retrievable, for a party provisioning a sidecar, the address to dial, the framing identifier to name, and the endpoint identity to verify, and an operator SHALL be able to retrieve the same together with what the listener is actually serving.

The platform SHALL NOT advertise an endpoint it does not serve. Where an advertised address stops being served, the advertisement SHALL stop being emitted. Where an address is advertised, the listener SHALL be serving it with an identity that covers the advertised name, and a discrepancy between what is advertised and what is served SHALL be reported as a defect rather than left for a sidecar to discover as a verification failure.

The advertisement is installation-wide configuration and SHALL be identical for every party entitled to retrieve it. It SHALL carry no credential and no secret, and SHALL disclose nothing about any tenant, any mount, or the installation's occupancy, so that retrieving it discloses nothing a party could not learn by dialling the endpoint. A credential SHALL NOT be obtainable through the same retrieval, so that a party provisioning a sidecar cannot mistake the advertisement for a means of issuance.

#### Scenario: The advertised endpoint matches what is served

- **WHEN** a party provisioning a sidecar retrieves the endpoint to dial
- **THEN** the address, the framing identifier, and the identity to verify are all stated
- **AND** the listener is serving that address with an identity covering the advertised name

#### Scenario: An unserved endpoint is not advertised

- **WHEN** an address stops being served by the listener
- **THEN** it stops being advertised
- **AND** no party provisioning a sidecar is given it

#### Scenario: A discrepancy is a defect, not a sidecar's problem

- **WHEN** the advertised endpoint names an address or identity the listener does not serve
- **THEN** the discrepancy is reported as a defect for the operator
- **AND** it is reported without waiting for a sidecar's verification to fail

#### Scenario: The framing identifier is part of the advertisement

- **WHEN** the listener serves a framing identifier and an additional one is introduced
- **THEN** the advertisement states both identifiers
- **AND** a sidecar naming either is served

#### Scenario: The advertisement carries nothing sensitive

- **WHEN** the advertisement is retrieved
- **THEN** it carries no credential and no secret
- **AND** it names no tenant, no mount, and no count of tenants, mounts, or connections
- **AND** what two entitled parties retrieve is identical

### Requirement: Changing the dialling address does not silently break connected sidecars

Sidecars hold the address they dial in configuration the operator does not control, so an address change is a change whose completion depends on parties who may never act. The listener SHALL be able to serve a new address before an old one is withdrawn, and the two SHALL be served concurrently for a configured overlap period.

Putting a new address into service SHALL NOT disconnect, drain, or degrade any tunnel established on the old one. Withdrawal of an old address SHALL be a distinct, deliberate step from introducing the new one, SHALL be observable, and SHALL record how many tunnels were still established on the withdrawn address and how many establishment attempts had arrived at it during a recent period, so an operator can determine whether any sidecar has yet to move.

An establishment attempt arriving at a withdrawn address SHALL be refused with an enumerated cause naming that the address is no longer served, distinguishable from an authentication failure and from the endpoint not accepting, and the refusal SHALL NOT name a replacement address. Attempts by address SHALL be separately countable so a fleet's migration is observable as it proceeds.

#### Scenario: A new address is served before the old is withdrawn

- **WHEN** a new dialling address is put into service while the old one is still advertised
- **THEN** sidecars dialling either address establish tunnels
- **AND** tunnels established on the old address are not disconnected

#### Scenario: Migration progress is observable

- **WHEN** two addresses are served concurrently and part of the fleet has moved
- **THEN** the count of established tunnels and of establishment attempts is separately retrievable per address
- **AND** an operator can determine how much of the fleet has yet to move

#### Scenario: Withdrawal records who was still using the address

- **WHEN** an old address is withdrawn while tunnels were still established on it
- **THEN** the withdrawal records how many were established on it and how many attempts had recently arrived at it
- **AND** the record is available without inspecting tenant traffic

#### Scenario: An attempt at a withdrawn address is refused distinguishably

- **WHEN** a sidecar dials an address that has been withdrawn
- **THEN** the refusal names that the address is no longer served
- **AND** it is distinguishable from an authentication failure and from the endpoint not accepting
- **AND** it names no replacement address

#### Scenario: Introducing an address disturbs nothing established

- **WHEN** a new address is put into service while exchanges are in flight on tunnels established at the old one
- **THEN** no exchange is reset
- **AND** no registry entry becomes ineligible

### Requirement: Listener configuration is validated in one pass before anything is accepted

The one-pass startup validation, the naming of every failing item together, the prohibition on implicit defaults, and the guarantee that nothing is accepted during a startup that ends in refusal are the observability capability's, and the validation of required material before service begins is the custody capability's. What this capability adds is which listener items that pass covers and which cross-item relations it checks; the listener SHALL NOT perform a validation pass of its own, SHALL NOT refuse on its first failing item, and SHALL NOT accept a connection before the pass has completed successfully.

The items covered SHALL include at minimum: the address or addresses to serve, the identity material and its coverage of each name advertised or served, the protection policy, the framing identifiers served, the configured intermediary set from which a conveyed source is honoured, the pre-authentication connection bound, the per-source allowance, the unauthenticated time budget, the pre-authentication read bound, the per-connection memory bound, the total connection bound, the per-credential tunnel bound, the identity overlap period, the address overlap period, and the reserved identifier the listener contributes to the routing enumerations.

The relations checked SHALL include: that the protection policy is at or above the floor and that no value disables the floor's enforcement, that the identity material covers every name served or advertised, that the per-credential tunnel bound is at or above the overlap floor and not above the per-tenant registration bound in force, that every framing identifier advertised is one the listener serves, and that the reserved identifier the listener is exposed at is present in the routing enumerations it contributes to. A relation that fails SHALL be reported naming both items it relates, not one of them.

#### Scenario: Identity coverage is validated against every advertised name

- **WHEN** the listener is configured to serve two addresses and the identity material covers only one
- **THEN** the component refuses to start
- **AND** the refusal names the address the material does not cover

#### Scenario: A missing listener bound is a failure, not a default

- **WHEN** the pre-authentication connection bound is absent from the configuration
- **THEN** the component refuses to start naming it
- **AND** no bound is silently applied in its place
- **AND** no connection was accepted at any point

#### Scenario: A failing relation names both items

- **WHEN** the per-credential tunnel bound is configured above the per-tenant registration bound in force
- **THEN** the refusal names both items and the relation between them
- **AND** it does not name only the one it read second

#### Scenario: An unreserved exposure point is a startup failure

- **WHEN** the listener is configured to be exposed at a path prefix absent from the reserved-path enumeration it contributes to
- **THEN** the component refuses to start naming the prefix and the enumeration
- **AND** the endpoint was not served at that prefix at any point

#### Scenario: An advertised framing the listener does not serve is a startup failure

- **WHEN** the advertisement is configured with a framing identifier the listener is not configured to serve
- **THEN** the component refuses to start naming both
- **AND** no sidecar was given the unserved identifier
