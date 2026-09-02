## Purpose

Defines how a tenant brings their own hostname to the platform: how a hostname is claimed against one of that tenant's mounts, how the platform establishes that the claimant actually controls the hostname before serving a single byte or requesting a single certificate for it, and how the certificate that terminates connections for that hostname is obtained, renewed, selected, and kept isolated from every other tenant. This is the capability where a routing mistake stops being a routing mistake and becomes a publicly trusted certificate issued for someone else's hostname.

## ADDED Requirements

### Requirement: A hostname claim names one mount

A hostname claim SHALL associate exactly one hostname with exactly one mount. The named target SHALL be a mount; a claim naming a path that is not a mount SHALL be rejected at the point of creation with a reason identifying the target as ineligible.

The claiming tenant SHALL be the tenant that owns the named mount. A hostname SHALL resolve to at most one mount at any instant, across all tenants.

When the named mount ceases to exist or ceases to be a mount, the claim SHALL stop being served, and the hostname SHALL NOT continue to occupy the uniqueness of the mapping. Removal of a mount SHALL NOT leave a claim that neither serves traffic nor can be replaced.

A claim MAY be retargeted to a different mount owned by the same tenant. Retargeting SHALL NOT require the hostname to be verified again and SHALL NOT interrupt certificate presentation, because control of the hostname is unchanged. Retargeting SHALL take effect as a single transition, so that no request for the hostname is routed to both mounts or to neither. A claim SHALL NOT be retargeted to a mount owned by a different tenant.

#### Scenario: Claim against a non-mount target

- **WHEN** a tenant claims a hostname naming a path that is not a mount
- **THEN** the claim is rejected
- **AND** the reason identifies the target as not being a mount
- **AND** no verification is started and no certificate is requested

#### Scenario: Claim against another tenant's mount

- **WHEN** a tenant claims a hostname naming a mount owned by a different tenant
- **THEN** the claim is rejected
- **AND** the existence of the other tenant's mount is not disclosed by the rejection

#### Scenario: Target mount is removed

- **WHEN** a mount named by a verified, served hostname is removed
- **THEN** traffic for that hostname stops being served
- **AND** the hostname becomes available to be claimed again subject to verification
- **AND** the removed claim does not prevent a new claim for the same hostname from being created

#### Scenario: One hostname, one mount

- **WHEN** a hostname is already mapped to a mount
- **AND** a claim is made mapping the same hostname to a second mount
- **THEN** the second mapping does not take effect while the first is in force
- **AND** requests for that hostname continue to reach exactly one mount

#### Scenario: Retarget within the same tenant

- **WHEN** a tenant retargets a verified hostname claim from one of their mounts to another of their mounts
- **THEN** the claim remains verified without a new challenge
- **AND** requests for the hostname reach the new mount
- **AND** the certificate presented for the hostname is unchanged

#### Scenario: Retarget across tenants is rejected

- **WHEN** a tenant retargets a verified hostname claim to a mount owned by a different tenant
- **THEN** the retarget is rejected
- **AND** requests for the hostname continue to reach the original mount

### Requirement: Hostname normalisation is defined and applied everywhere

The capability SHALL define a single normalisation for hostnames, and SHALL apply it identically when a claim is created, when uniqueness is enforced, when a verification challenge is constructed, when a certificate is selected, and when an incoming request is matched. Two inputs that normalise to the same value SHALL be the same hostname for every one of those purposes.

Normalisation SHALL at minimum case-fold the hostname, remove a trailing label separator, remove any port component, and convert internationalised labels to their ASCII-compatible form. A hostname that cannot be normalised — including an address literal, an empty label, a label exceeding the permitted length, or a name containing characters not permitted in a hostname — SHALL be rejected at claim time rather than stored.

#### Scenario: Case and trailing separator do not create a second hostname

- **WHEN** a tenant claims a hostname differing from an existing verified hostname only in letter case or a trailing separator
- **THEN** the claim is treated as naming the existing hostname
- **AND** it does not create a second independent mapping

#### Scenario: Internationalised name is stored in one form

- **WHEN** a tenant claims a hostname containing non-ASCII labels
- **THEN** the stored hostname is its ASCII-compatible form
- **AND** a request arriving for either form matches the same claim

#### Scenario: Address literal is refused

- **WHEN** a tenant claims an address literal rather than a hostname
- **THEN** the claim is rejected with a reason naming the input as not a hostname

#### Scenario: Malformed hostname is refused at claim time

- **WHEN** a tenant claims a hostname containing an empty label, a label longer than the permitted length, or a character not permitted in a hostname
- **THEN** the claim is rejected
- **AND** nothing is stored for it
- **AND** no verification is started

#### Scenario: Matching uses the normalised form

- **WHEN** a request arrives whose target hostname differs from the claimed hostname only by case
- **THEN** it matches the claim
- **AND** it is served by the same mount as the canonical form

### Requirement: A claim confers nothing until ownership is verified

A hostname claim SHALL confer no capability of any kind until the claimant has completed a verification challenge that can only be satisfied by a party who controls the hostname. Until verification completes, the platform SHALL NOT serve any request for that hostname, SHALL NOT request a certificate for it from any certificate authority, and SHALL NOT present the hostname as belonging to the claimant anywhere it is treated as authoritative.

Verification SHALL be a property of the hostname and the claimant together. Possession of an account, ownership of a mount, prior use of a related hostname, and the order in which claims were made SHALL NOT substitute for it.

#### Scenario: Unverified claim serves no traffic

- **WHEN** a tenant creates a claim for a hostname and the hostname's traffic is directed at the platform
- **AND** verification has not completed
- **THEN** the request is not routed to the claimant's mount
- **AND** the claimant's backend receives nothing

#### Scenario: Unverified claim requests no certificate

- **WHEN** a claim exists for which verification has not completed
- **THEN** no certificate request for that hostname is submitted to any certificate authority
- **AND** no certificate for that hostname exists in the platform's certificate material

#### Scenario: Verification is required even for a hostname under an already-verified parent

- **WHEN** a tenant has a verified claim for one hostname
- **AND** the same tenant claims a different hostname under the same parent name
- **THEN** the new claim is unverified
- **AND** it is served only after its own verification completes

#### Scenario: Verification outcome is recorded

- **WHEN** a claim's verification completes
- **THEN** the record of the claim states which challenge class was satisfied, when it was satisfied, and which principal held the claim at that moment
- **AND** that record is retrievable by an operator afterwards

### Requirement: Verification challenges are unpredictable and bound to one claim

A verification challenge SHALL require the claimant to demonstrate control of the hostname by placing a platform-issued value where only a controller of that hostname can place it. The capability SHALL support at minimum: a challenge satisfied by publishing the value in the hostname's delegated naming records, a challenge satisfied by serving the value over an unencrypted request to a reserved path on the hostname, and a challenge satisfied by presenting the value during connection setup for the hostname.

Each issued challenge value SHALL be unpredictable to anyone who has not been issued it, SHALL be valid for exactly one claim of one hostname by one tenant, and SHALL expire after a configured lifetime. A value issued for one claim SHALL NOT satisfy any other claim, including a claim by another tenant for the same hostname, and including a claim by the same tenant for a different hostname.

Two challenges issued for the same hostname, the same tenant, and the same claim SHALL carry different values. No value SHALL be accepted for a claim before the platform has issued it for that claim.

#### Scenario: A challenge value satisfies only its own claim

- **WHEN** a challenge value issued for one tenant's claim is observed and then presented against a second tenant's claim for the same hostname
- **THEN** the second claim is not verified
- **AND** the reuse is recorded

#### Scenario: Challenge values expire

- **WHEN** a challenge is satisfied after its issued lifetime has elapsed
- **THEN** verification does not complete
- **AND** a new challenge value is required

#### Scenario: A replacement challenge for the same claim differs

- **WHEN** a challenge is issued for a claim and a replacement challenge is then issued for the same hostname, the same tenant, and the same claim
- **THEN** the replacement value differs from the first
- **AND** the first value no longer satisfies the claim

#### Scenario: An unissued value never verifies

- **WHEN** a value is placed where a challenge would be satisfied and presented for a claim for which the platform has issued no challenge
- **THEN** verification does not complete
- **AND** the claim remains unverified

#### Scenario: Challenge class is recorded per claim

- **WHEN** a claim is verified by one challenge class
- **THEN** the claim records that class
- **AND** re-verification of that claim by a different challenge class does not invalidate the claim

### Requirement: The verification responder belongs to the edge, never to a tenant

Requests to the reserved path used by the request-served challenge class SHALL be answered by the platform edge and SHALL NOT be forwarded over any tunnel, regardless of which mount the hostname maps to or whether the hostname is mapped at all.

The edge SHALL answer such a request only with a value it issued for a claim of that exact hostname, and SHALL answer with a not-found result otherwise. A tenant backend SHALL have no means of causing the edge to answer a challenge for a hostname that tenant has not been issued a challenge for.

The reserved path SHALL be contributed to the single reserved-path enumeration the mount-point capability owns, rather than held as a second reserved set here. It SHALL be the narrowest path that the challenge class requires, so that requests to sibling paths under any shared ancestor are routed to the hostname's mount like any other request, because a tenant's own service-discovery resources live there.

#### Scenario: Challenge path is not proxied

- **WHEN** a request arrives on the reserved challenge path for a hostname that maps to a mount
- **THEN** the request is answered by the edge
- **AND** no frame for that request crosses any tunnel
- **AND** the tenant's backend does not observe the request

#### Scenario: Challenge path for an unknown token

- **WHEN** a request arrives on the reserved challenge path bearing a value the edge did not issue for that hostname
- **THEN** the edge answers with a not-found result
- **AND** it does not disclose whether any challenge is outstanding for that hostname

#### Scenario: A tenant cannot answer for a hostname it has not claimed

- **WHEN** a tenant's backend attempts to serve a value on the reserved challenge path for a hostname pointed at the platform
- **THEN** the value the backend produced is never presented to any validator
- **AND** verification for that hostname does not complete on the basis of it

#### Scenario: Sibling reserved-prefix paths still reach the tenant

- **WHEN** a request arrives on a verified hostname for a well-known discovery path that shares a prefix with the reserved challenge path but is not the challenge path
- **THEN** the request is routed to the hostname's mount
- **AND** the tenant's backend produces the response

### Requirement: Verification is re-checked and lapses

Verification SHALL NOT be permanent. The platform SHALL re-establish control of every verified hostname at a configured interval. A hostname whose control can no longer be demonstrated SHALL stop being served after a configured grace period, and SHALL return to the unverified state.

This SHALL hold specifically for a hostname whose delegation to the platform still exists but whose owner has released it — a name still pointing at the platform that the original claimant no longer controls SHALL NOT continue to be served to that claimant, and SHALL NOT continue to have certificates renewed for it.

The transition from verified to lapsed SHALL be observable to both the tenant and the operator before service stops, not only after.

#### Scenario: Control is withdrawn

- **WHEN** a verified hostname's delegation no longer carries the platform's verification value and re-verification fails repeatedly
- **THEN** the hostname stops being served once the grace period elapses
- **AND** the claim returns to the unverified state
- **AND** certificate renewal for that hostname stops

#### Scenario: Dangling delegation does not confer continuing control

- **WHEN** a hostname still directs traffic to the platform
- **AND** the claimant can no longer satisfy a verification challenge for it
- **THEN** the claimant's mount stops receiving that hostname's traffic
- **AND** a new claimant may claim the hostname by completing verification

#### Scenario: Lapse is warned before it is enforced

- **WHEN** re-verification for a hostname begins failing
- **THEN** the tenant and the operator can observe the failing state before service for that hostname stops
- **AND** the observable state names the hostname and the failing challenge

#### Scenario: Transient re-verification failure does not drop service

- **WHEN** a single re-verification attempt fails and a subsequent attempt within the grace period succeeds
- **THEN** service for the hostname is uninterrupted
- **AND** the claim remains verified

### Requirement: Competing claims are resolved by verification, not by order

The existence of an unverified claim SHALL NOT prevent another tenant from claiming the same hostname, and SHALL NOT prevent another tenant from verifying it. Being first to claim SHALL confer no priority.

Where a hostname is verified and served for one tenant, a second tenant's claim for the same hostname SHALL NOT displace it merely by being verified; the conflict SHALL be surfaced to an operator, and the incumbent mapping SHALL remain in force until it is removed or lapses. When an incumbent mapping lapses or is removed, a claim whose verification is current SHALL become eligible to take effect without a further challenge, and the platform SHALL make the succession observable to an operator.

A rejection or a pending state arising from another tenant's claim SHALL NOT disclose the other tenant's identity.

#### Scenario: First claim does not win

- **WHEN** tenant A creates an unverified claim for a hostname
- **AND** tenant B later creates a claim for the same hostname and completes verification
- **THEN** the hostname is served for tenant B
- **AND** tenant A's unverified claim confers nothing

#### Scenario: Both claims unverified

- **WHEN** two tenants hold unverified claims for the same hostname
- **THEN** neither is served
- **AND** neither claim is rejected on the ground that the other exists

#### Scenario: Second verification against a live incumbent

- **WHEN** a hostname is verified and served for tenant A
- **AND** tenant B completes verification for the same hostname
- **THEN** traffic continues to reach tenant A's mount
- **AND** the conflict is recorded and observable to an operator

#### Scenario: Conflict does not leak tenant identity

- **WHEN** a tenant's claim cannot take effect because another tenant holds the hostname
- **THEN** the state visible to that tenant does not name the other tenant, their mount, or their account

#### Scenario: Challenger succeeds an incumbent that lapses

- **WHEN** tenant B holds a verified claim for a hostname that is served for tenant A
- **AND** tenant A's claim is removed or its verification lapses
- **THEN** the hostname is served for tenant B without tenant B completing a further challenge
- **AND** the succession is recorded and observable to an operator

### Requirement: Wildcard claims are proved by delegation only

A claim MAY name a wildcard hostname covering the immediate child labels of a parent name. A wildcard claim SHALL be verifiable only by the challenge class that publishes a value in the parent hostname's delegated naming records; the request-served and connection-setup challenge classes SHALL NOT verify a wildcard claim.

A verified wildcard claim SHALL cover only names one label below its parent. It SHALL NOT cover the parent name itself, and it SHALL NOT cover names more than one label below the parent.

A wildcard claim SHALL NOT capture a hostname for which another tenant holds a verified exact claim, whether that exact claim existed before or after the wildcard claim was verified.

#### Scenario: Wildcard cannot be proved by serving a path

- **WHEN** a tenant attempts to verify a wildcard claim by serving the challenge value on the reserved path
- **THEN** verification does not complete
- **AND** the reason names the challenge class as ineligible for a wildcard claim

#### Scenario: Wildcard covers one label only

- **WHEN** a wildcard claim for a parent name is verified
- **AND** a request arrives for a hostname two labels below that parent
- **THEN** the wildcard claim does not match it

#### Scenario: Wildcard does not cover the parent

- **WHEN** a wildcard claim for a parent name is verified
- **AND** a request arrives for the parent name itself
- **THEN** the wildcard claim does not match it

#### Scenario: Exact claim by another tenant is not captured

- **WHEN** tenant A holds a verified wildcard claim for a parent name
- **AND** tenant B holds a verified exact claim for a hostname one label below that parent
- **THEN** requests for that hostname reach tenant B's mount
- **AND** requests for other names under the parent reach tenant A's mount

### Requirement: An exact match takes precedence over a wildcard match

When an incoming hostname matches both an exact claim and a wildcard claim, the exact claim SHALL be selected. This SHALL hold for routing and for certificate selection alike, and SHALL NOT depend on the order in which the claims were created, verified, or loaded.

Where two wildcard claims could match, the one with the more specific parent SHALL be selected. Where selection remains ambiguous, the request SHALL be refused rather than served by an arbitrary choice.

#### Scenario: Exact wins over wildcard for routing

- **WHEN** an exact claim and a covering wildcard claim are both verified
- **AND** a request arrives for the exactly claimed hostname
- **THEN** it is routed to the exact claim's mount

#### Scenario: Exact wins over wildcard for certificate selection

- **WHEN** an exact claim and a covering wildcard claim are both verified and both hold certificates
- **AND** a connection is opened for the exactly claimed hostname
- **THEN** the certificate presented is the one issued for the exact hostname

#### Scenario: Precedence does not depend on load order

- **WHEN** the routing state is rebuilt from persistent storage in a different order
- **THEN** the same hostname resolves to the same mount as before the rebuild

#### Scenario: More specific wildcard wins

- **WHEN** two verified wildcard claims could both match an incoming hostname
- **THEN** the one whose parent has more labels is selected

### Requirement: Certificates are issued only after verification and cover only verified hostnames

Once a claim is verified, the platform SHALL obtain a certificate for that hostname automatically, without further tenant action. A certificate obtained for a claim SHALL name only hostnames that are verified for the tenant holding that claim.

A single certificate SHALL NOT name hostnames belonging to more than one tenant. A certificate request SHALL NOT include a hostname whose verification has lapsed or has not completed.

#### Scenario: Issuance follows verification without tenant action

- **WHEN** a claim's verification completes
- **THEN** a certificate for that hostname is obtained
- **AND** the tenant is not required to take any further step for the hostname to be served over an encrypted connection

#### Scenario: Certificate names no unverified hostname

- **WHEN** a tenant holds one verified claim and one unverified claim
- **THEN** the certificate obtained names only the verified hostname

#### Scenario: Certificates are never shared between tenants

- **WHEN** two tenants each hold verified claims
- **THEN** no certificate names hostnames belonging to both
- **AND** neither tenant's certificate is presented for the other's hostname

### Requirement: Certificates are renewed ahead of expiry

The platform SHALL attempt renewal of every certificate it holds beginning at a configured margin before that certificate's expiry, and SHALL leave enough of that margin for repeated attempts after a failure. Renewal SHALL require the hostname's verification to be current at the time of renewal.

A renewal SHALL NOT interrupt service: the existing certificate SHALL continue to be presented until a replacement is in place, and the replacement SHALL take effect for new connections without restarting the platform or dropping established connections.

#### Scenario: Renewal begins before expiry

- **WHEN** a certificate reaches the configured margin before its expiry
- **THEN** a renewal attempt is made
- **AND** subsequent attempts are made within the remaining margin if the first fails

#### Scenario: Renewal does not interrupt service

- **WHEN** a certificate is renewed while connections for its hostname are being served
- **THEN** requests are served throughout
- **AND** connections established after the renewal are terminated with the replacement certificate

#### Scenario: Renewal requires current verification

- **WHEN** a certificate is due for renewal and the hostname's verification has lapsed
- **THEN** renewal is not attempted
- **AND** the lapse is the reason recorded, distinct from an authority failure

### Requirement: Issuance failure is bounded, backed off, and non-destructive

When a certificate authority refuses, errors, or rate-limits a request, the platform SHALL retain any existing valid certificate for that hostname and continue to serve with it. A failed issuance or renewal SHALL NOT remove a working certificate and SHALL NOT stop the hostname being served while its current certificate remains valid.

Retries SHALL be spaced by an increasing interval with a randomised component, SHALL respect any wait period the authority states, and SHALL be bounded in rate per hostname and in aggregate, so that a systemic failure does not become sustained load against the authority or exhaust an issuance allowance shared across tenants.

Failures SHALL be distinguished in what the platform records: a refusal that will not succeed on retry, a temporary authority failure, an exhausted issuance allowance, and a failure of the hostname's own verification SHALL each be separately identifiable.

#### Scenario: Failed renewal does not remove a valid certificate

- **WHEN** renewal fails and the existing certificate has not yet expired
- **THEN** the existing certificate continues to be presented
- **AND** the hostname continues to be served

#### Scenario: Rate limit is respected

- **WHEN** the authority reports that the platform has exhausted an issuance allowance and states a wait period
- **THEN** no further request for that hostname is made before that period elapses
- **AND** requests for unaffected hostnames are not blocked indefinitely by it

#### Scenario: Retries back off and are jittered

- **WHEN** issuance for a hostname fails repeatedly
- **THEN** each interval between attempts is longer than the one before it, up to a configured ceiling
- **AND** two hostnames whose issuance begins failing at the same moment do not make their subsequent attempts at the same instant
- **AND** the interval does not collapse back to its initial value after a long run of failures

#### Scenario: Failure causes are distinguishable

- **WHEN** issuance fails
- **THEN** the recorded outcome distinguishes a permanent refusal, a temporary authority failure, an exhausted allowance, and a verification failure
- **AND** the record names the hostname

### Requirement: Impending certificate expiry is surfaced before it becomes an outage

The platform SHALL make the certificate state of every served hostname observable, including the time remaining before expiry and the outcome of the most recent issuance or renewal attempt. When renewal has not succeeded and the remaining validity has fallen below a configured threshold, the platform SHALL raise this as an operator-visible condition naming the affected hostnames.

A hostname SHALL NOT reach certificate expiry without that condition having been observable for a preceding period. Expiry SHALL NOT be first learned from client connection failures.

#### Scenario: Unrenewed certificate raises a condition before expiry

- **WHEN** renewal has failed and a certificate's remaining validity falls below the configured threshold
- **THEN** an operator-visible condition names that hostname
- **AND** it is raised before the certificate expires

#### Scenario: Certificate state is enumerable

- **WHEN** an operator inspects the platform's certificate state
- **THEN** every served hostname is listed with its expiry and the outcome of its most recent renewal attempt

#### Scenario: No silent expiry

- **WHEN** a certificate expires
- **THEN** the condition warning of it was observable for a preceding period
- **AND** the expiry itself is recorded as a distinct event

### Requirement: Certificate selection is by requested hostname at connection setup

At connection setup the platform SHALL select the certificate to present using the hostname the client requests for that connection. Where the requested hostname is neither a hostname the platform serves on its own behalf nor a hostname with a verified claim holding a valid certificate, the platform SHALL refuse the connection rather than present a certificate for a different hostname or a default certificate.

Selection SHALL apply exact-over-wildcard precedence. A connection whose requested hostname is absent SHALL be refused, and SHALL NOT be served a tenant's certificate.

A hostname the platform serves on its own behalf — its control surface and its own ingress hostnames — SHALL be served with the platform's own certificate rather than any tenant's. Where a connection-setup verification challenge is outstanding for a hostname, the platform SHALL present the certificate that satisfies that challenge for connections attempting it, and that certificate SHALL NOT be used to serve any request on that connection.

#### Scenario: Matching hostname is served its own certificate

- **WHEN** a connection requests a hostname with a verified claim and a valid certificate
- **THEN** the certificate presented is the one issued for that hostname

#### Scenario: Unknown hostname is refused, not defaulted

- **WHEN** a connection requests a hostname with no verified claim
- **THEN** no tenant certificate is presented
- **AND** the connection is refused

#### Scenario: Requested hostname absent

- **WHEN** a connection is opened without a requested hostname
- **THEN** no tenant certificate is presented
- **AND** the connection is refused

#### Scenario: Expired certificate is not presented

- **WHEN** a hostname's certificate has expired and no replacement exists
- **THEN** the expired certificate is not presented
- **AND** the connection is refused with the cause recorded

#### Scenario: Connection-setup challenge is served its own certificate

- **WHEN** a connection-setup verification challenge is outstanding for a hostname that holds no verified claim
- **AND** a validator opens a connection for that hostname
- **THEN** the certificate satisfying the challenge is presented
- **AND** no request on that connection is routed to any mount

### Requirement: Certificate material is isolated per tenant

A tenant's private key SHALL never be used to terminate a connection for a hostname verified to a different tenant. A tenant's private key SHALL NOT be readable by any tenant, including the tenant it belongs to, through any interface the platform exposes.

Interfaces that expose certificate state SHALL show a tenant only the hostnames, expiries, and issuance outcomes belonging to that tenant. A tenant-facing response for a hostname held by another tenant SHALL be identical in status, error code, and content to the response for a hostname held by no one.

#### Scenario: Key is never cross-presented

- **WHEN** connections are opened for two hostnames verified to different tenants
- **THEN** each is terminated with the certificate and key of its own tenant

#### Scenario: Private key is not exposed

- **WHEN** a tenant retrieves the certificate state for a hostname they hold
- **THEN** the response contains no private key material

#### Scenario: Another tenant's hostnames are not listed

- **WHEN** a tenant enumerates their certificate state
- **THEN** only hostnames verified to that tenant appear

#### Scenario: Held-by-another is indistinguishable from unheld

- **WHEN** a tenant queries the state of a hostname held by another tenant
- **AND** the same tenant queries the state of a hostname held by no one
- **THEN** the two responses carry the same status, the same error code, and the same content

### Requirement: Verification and certificate state is consistent across serving instances

Verification progress and certificate material SHALL be shared state, not state local to whichever instance handled a request. A challenge initiated by one instance SHALL be answerable by any instance that receives the validation request. A certificate obtained by one instance SHALL be presented by every instance serving that hostname.

An instance joining the platform SHALL serve every already-verified hostname with its existing certificate without re-issuing. Issuance for one hostname SHALL be performed once, not once per instance.

An instance that cannot reach the shared state SHALL continue to serve the hostnames and certificates it already holds, SHALL NOT request new certificates, and SHALL NOT treat the unreachable state as evidence that a hostname's verification has lapsed.

#### Scenario: Validation reaches a different instance

- **WHEN** a challenge is initiated by one instance
- **AND** the validation request arrives at another instance
- **THEN** the challenge is answered correctly
- **AND** verification completes

#### Scenario: New instance serves existing certificates

- **WHEN** an instance is added to the platform
- **THEN** it presents the existing certificate for every verified hostname
- **AND** it does not request new certificates for hostnames that already hold valid ones

#### Scenario: Issuance is not duplicated per instance

- **WHEN** several instances observe that a hostname requires issuance at the same time
- **THEN** one certificate request is made for that hostname
- **AND** the issuance allowance is charged once

#### Scenario: Shared state is unreachable

- **WHEN** an instance cannot reach the shared verification and certificate state
- **THEN** it continues to present the certificates it already holds
- **AND** it requests no new certificate
- **AND** no hostname's verification is treated as lapsed on that basis

### Requirement: Application protocol is negotiated at connection setup

The platform SHALL advertise, during connection setup, the set of application protocols it will serve on that connection, and SHALL serve the connection using a protocol from that set. The advertised set SHALL contain only protocols the platform can actually serve for the requested hostname.

Where the client offers no protocol the platform advertises, the platform SHALL refuse the connection rather than proceed on an unnegotiated protocol. The negotiated protocol SHALL be recorded for the connection and SHALL be observable to an operator.

#### Scenario: Client and platform agree

- **WHEN** a client offers two application protocols and the platform advertises one of them
- **THEN** the connection is served using the common protocol
- **AND** the negotiated protocol is recorded

#### Scenario: No common protocol

- **WHEN** a client offers only protocols the platform does not advertise
- **THEN** the connection is refused
- **AND** the refusal is distinguishable from a certificate failure

#### Scenario: Advertisement matches what is served

- **WHEN** the platform advertises an application protocol for a hostname
- **THEN** a client selecting it is served over that protocol
- **AND** the connection is not downgraded to another protocol after negotiation

### Requirement: Alternative protocol endpoints are advertised only where served

Where the platform serves a hostname over an additional transport reachable at a different endpoint, it SHALL advertise that endpoint to clients in a form they can act on, together with the period for which the advertisement is valid.

The platform SHALL NOT advertise an endpoint it does not serve for that hostname. When an advertised endpoint stops being served, the platform SHALL stop emitting the advertisement, and SHALL continue to serve the hostname over the original transport for at least the validity period of the last advertisement it emitted, so that a client acting on a cached advertisement has a working endpoint to return to.

#### Scenario: Alternative endpoint is advertised when available

- **WHEN** a hostname is served over an additional transport at a distinct endpoint
- **THEN** responses for that hostname carry an advertisement naming that endpoint and its validity period

#### Scenario: No advertisement when not served

- **WHEN** a hostname is served over only the primary transport
- **THEN** no alternative endpoint is advertised for it

#### Scenario: Withdrawn endpoint leaves a working primary

- **WHEN** an advertised alternative endpoint stops being served
- **THEN** the advertisement is no longer emitted
- **AND** the hostname continues to be served over the primary transport for at least the validity period of the last advertisement emitted

### Requirement: Traffic on a custom hostname is handled identically to traffic on the platform hostname

A request that reaches a mount by matching a hostname claim SHALL be subject to exactly the same handling as a request that reaches the same mount by any other routing mechanism. The hostname a request arrived on SHALL NOT change which methods, media types, body shapes, or protocols are accepted for it.

No content negotiation, body parsing, method rewriting, content-type restriction, session handling, or other application-level processing SHALL be applied to a request because it arrived on a custom hostname. Hostname-routed traffic SHALL pass through the same single edge pipeline definition that the edge-hygiene capability requires for all mount-destined traffic; this capability SHALL NOT define a pipeline of its own, so that a change to one cannot leave the other behind.

#### Scenario: Media type is not restricted by arrival hostname

- **WHEN** a client sends a request whose media type is not one the platform's own control surface accepts
- **AND** the request arrives on a verified custom hostname
- **THEN** the request reaches the mount unaltered
- **AND** it is not refused on the ground of its media type

#### Scenario: Extension methods survive on a custom hostname

- **WHEN** a client issues a request with an extension method token on a verified custom hostname
- **THEN** the backend receives that method token
- **AND** the outcome is the same as for the identical request routed by path prefix

#### Scenario: Request bodies survive on a custom hostname

- **WHEN** a client sends a request with a body on a verified custom hostname
- **THEN** the backend receives that body in full
- **AND** the octets are identical to those received for the identical request routed by path prefix

#### Scenario: Both routing mechanisms behave identically

- **WHEN** the same request is issued once against a verified custom hostname and once against the path prefix for the same mount
- **THEN** the backend observes the same method, header fields, and body octets in both cases

### Requirement: The claim is selected by the hostname established at connection setup

Where a connection carries a hostname established at connection setup, that hostname SHALL be the one used to select the claim, the mount, and the tenant for every request on that connection. A hostname carried in the request itself SHALL NOT be used to select a different claim.

The comparison of a request's own hostname against the authority established for the connection, and the statuses returned for a mismatch, a missing authority, and a repeated authority, are owned by the edge-hygiene capability and are not restated here. What this capability adds is that claim selection consumes only the established authority: a request whose own hostname is present and does not match SHALL NOT be routed to any mount, and no claim SHALL be consulted for it. A hostname in a form this capability's normalisation rejects SHALL likewise select no claim.

#### Scenario: Request hostname cannot override the connection hostname

- **WHEN** a connection is established for one tenant's verified hostname
- **AND** a request on it carries a different tenant's verified hostname
- **THEN** the request is refused
- **AND** it does not reach either tenant's mount

#### Scenario: Matching hostnames are served

- **WHEN** a request's own hostname matches the hostname the connection was established for
- **THEN** it is routed to that hostname's mount

#### Scenario: Conflicting hostnames in one request

- **WHEN** a request carries two conflicting hostnames
- **THEN** it is refused
- **AND** no claim is selected

#### Scenario: Unencrypted connection reaches no mount

- **WHEN** a connection carries no hostname established at connection setup
- **AND** a request on it names a tenant's verified hostname and a path other than the reserved challenge path
- **THEN** the request is not forwarded to that tenant's mount
- **AND** it is answered by the edge

### Requirement: The unencrypted listener answers challenges and redirects, and reaches no mount

Where the platform accepts unencrypted connections in order to satisfy the request-served verification challenge, that listener SHALL serve exactly two behaviours and no others: it SHALL answer the reserved challenge path as this capability requires, and for every other target it SHALL answer with a permanent redirection to the same target under the secure scheme on the hostname the request named. It SHALL forward nothing to any mount and SHALL generate no tunnel frame.

The redirection SHALL be issued only for a hostname the platform serves — one with a verified claim, or one reserved to the platform itself. For any other hostname the listener SHALL refuse without a redirection, and the refusal SHALL be identical whether the hostname is unclaimed, claimed but unverified, or claimed by another tenant. The redirection SHALL preserve the target's path and query exactly as received, without decoding, normalising, or re-encoding any octet, and SHALL name only the hostname the request named.

The unencrypted listener SHALL NOT read a request body, and SHALL NOT be a route by which any admission bound, cookie, or client-identity value is established for a subsequent secured connection.

#### Scenario: An ordinary unencrypted request is redirected, not proxied

- **WHEN** an unencrypted request arrives for a verified hostname on a path that is not the challenge path
- **THEN** the client receives a permanent redirection to the same target under the secure scheme
- **AND** no mount is matched and no tunnel frame is generated

#### Scenario: The redirection preserves the target verbatim

- **WHEN** an unencrypted request arrives whose path contains a percent-encoded separator and whose query contains repeated keys
- **THEN** the redirection target carries that path and query octet-for-octet as received

#### Scenario: An unserved hostname is refused, not redirected

- **WHEN** an unencrypted request arrives for a hostname with no verified claim
- **THEN** no redirection is issued
- **AND** the response is identical to the response for a hostname claimed but unverified and for one claimed by another tenant

#### Scenario: The challenge path is still answered

- **WHEN** an unencrypted request arrives on the reserved challenge path for a hostname with an outstanding challenge
- **THEN** the edge answers it with the issued value
- **AND** it is not redirected to the secure scheme

#### Scenario: No body is read on the unencrypted listener

- **WHEN** an unencrypted request arrives carrying a body
- **THEN** the redirection or refusal is produced without the body being read
- **AND** no part of the body reaches any mount

### Requirement: Claims and issuance are bounded per tenant

The number of hostname claims a tenant may hold, the rate at which a tenant may create claims, and the rate at which a tenant may cause challenges to be issued SHALL each be subject to a configured bound. These, together with the per-tenant issuance bound below, are standing-resource dimensions this capability contributes to the single closed enumeration of per-tenant bound dimensions the tenancy capability owns, on that enumeration's terms — one configured value per tenant, accounted once, with each tenant's consumption observable; this capability SHALL NOT hold a second value for any of them. A request exceeding a bound SHALL be refused with a reason naming the bound, rather than queued without limit.

Certificate issuance SHALL be bounded per tenant as well as in aggregate, because the issuance allowance of a certificate authority is shared across every tenant on the platform. One tenant SHALL NOT be able to exhaust that allowance for the others. When the aggregate allowance is at risk, the platform SHALL prefer renewal of certificates for hostnames already being served over issuance for new claims.

Every bound SHALL be observable to an operator, including how much of it each tenant is consuming.

#### Scenario: Claim count bound is enforced

- **WHEN** a tenant holding the maximum number of claims creates another
- **THEN** the claim is rejected
- **AND** the reason names the bound that was reached
- **AND** the tenant's existing claims continue to be served

#### Scenario: Challenge issuance is rate bounded

- **WHEN** a tenant requests challenges faster than the configured rate
- **THEN** the excess requests are refused
- **AND** no challenge value is issued for them

#### Scenario: One tenant cannot exhaust the shared allowance

- **WHEN** one tenant verifies hostnames faster than the aggregate issuance allowance permits
- **THEN** issuance for that tenant is deferred once its own bound is reached
- **AND** renewal of certificates for hostnames already being served continues
- **AND** another tenant's first issuance is not blocked indefinitely by it

#### Scenario: Consumption is observable

- **WHEN** an operator inspects issuance state
- **THEN** each tenant's consumption against each bound is reported

### Requirement: A hostname with no verified claim is not served

A request whose hostname matches no verified claim SHALL NOT be routed to any mount. The platform SHALL NOT fall back to a default tenant, to the most recently created claim, or to any mount reachable by another routing mechanism as a consequence of the hostname being unknown.

The response to an unknown hostname SHALL NOT disclose whether a claim for it exists in an unverified state, nor which tenants exist on the platform.

#### Scenario: Unknown hostname reaches no mount

- **WHEN** a request arrives for a hostname with no verified claim
- **THEN** it is refused
- **AND** no tunnel frame is generated for it

#### Scenario: No default tenant fallback

- **WHEN** exactly one tenant has verified hostnames on the platform
- **AND** a request arrives for a hostname none of them match
- **THEN** the request is not routed to that tenant

#### Scenario: Unknown and unverified are indistinguishable to a stranger

- **WHEN** a request arrives for a hostname held only as an unverified claim
- **AND** a request arrives for a hostname no one has claimed
- **THEN** the two responses carry the same status and the same body

### Requirement: The platform's own hostnames are reserved

The hostname on which the platform serves its own control surface SHALL continue to serve that control surface and SHALL NOT be claimable by any tenant. A claim naming it, or naming a hostname that a wildcard claim would cause to cover it, SHALL be rejected.

The reserved set SHALL include, at minimum, the control surface hostname, every hostname on which the platform serves prefix-routed tenant traffic on its own behalf, and every hostname under which the platform issues per-tenant subordinate names. A claim naming a parent of any hostname in the reserved set SHALL be rejected where verifying it would let the claimant obtain a certificate covering a reserved hostname or set cookies scoped to one.

The set of reserved hostnames SHALL be configurable and SHALL be evaluated after normalisation, so that a variant differing only in case, trailing separator, or internationalised encoding is equally reserved.

#### Scenario: Administrative hostname cannot be claimed

- **WHEN** a tenant claims the hostname serving the control surface
- **THEN** the claim is rejected
- **AND** the control surface continues to be served on it

#### Scenario: Normalised variant is equally reserved

- **WHEN** a tenant claims a variant of the administrative hostname differing only in case or trailing separator
- **THEN** the claim is rejected

#### Scenario: Wildcard covering the administrative hostname is rejected

- **WHEN** a tenant claims a wildcard whose coverage would include the administrative hostname
- **THEN** the claim is rejected
- **AND** requests for the administrative hostname continue to reach the control surface

#### Scenario: Reserved hostnames are never resolved through a claim

- **WHEN** a request arrives for a reserved hostname
- **THEN** no hostname claim is consulted for it
- **AND** it is handled by the platform's own routing for that hostname

#### Scenario: Control surface hostname reaches no tunnel

- **WHEN** a request arrives for the control surface hostname
- **THEN** no tunnel frame is generated for it

#### Scenario: The prefix-routing hostname cannot be claimed

- **WHEN** a tenant claims the hostname on which the platform serves prefix-routed tenant traffic
- **THEN** the claim is rejected
- **AND** prefix-routed traffic on that hostname continues to be served

### Requirement: Removal stops service promptly and requires re-verification to return

When a tenant removes a hostname claim, the platform SHALL stop routing that hostname to the tenant's mount within a bounded time, without requiring a restart. Certificate renewal for the hostname SHALL stop, and the certificate SHALL stop being presented once removal takes effect.

A removed hostname SHALL become claimable again, by the same tenant or another, only through a fresh verification. Removal SHALL NOT leave residue that prevents the hostname from being claimed again, and a previously completed verification SHALL NOT be reusable to short-circuit the new claim's verification.

#### Scenario: Service stops within a bounded time

- **WHEN** a tenant removes a verified hostname claim
- **THEN** within the bounded propagation time, requests for that hostname are no longer routed to that mount
- **AND** no restart of the platform is required

#### Scenario: Re-claim requires fresh verification

- **WHEN** a hostname claim is removed and the same tenant claims the hostname again
- **THEN** the new claim is unverified
- **AND** it is served only after completing a new verification challenge

#### Scenario: Removal leaves no residue

- **WHEN** a hostname claim is removed
- **AND** another tenant claims the same hostname and completes verification
- **THEN** the hostname is served for the new tenant
- **AND** the removed claim does not block the new mapping

#### Scenario: Certificate is retired

- **WHEN** a hostname claim is removed
- **THEN** the certificate for that hostname is no longer presented
- **AND** no further renewal is attempted for it
