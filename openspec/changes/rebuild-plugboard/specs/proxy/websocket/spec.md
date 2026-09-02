## Purpose

Defines what the proxy owes the client when a bidirectional frame stream is established through a mount point: how an upgrade is admitted at the edge and withheld until the backend has accepted, which handshake concerns are per-hop and therefore never relayed, and the policies the proxy alone owns — origin and concurrency admission, compression bounds, liveness, idle and lifetime bounds, backpressure on the client hop, a close vocabulary that does not collide with the tenant application's own, cleanup on every disconnect source, and drain. The wire contract already fixes what crosses the tunnel; this capability fixes what the client observes and what a shared proxy is protected from.

## ADDED Requirements

### Requirement: An upgrade is never accepted before the backend has accepted

The proxy SHALL NOT emit a successful upgrade response to a client until the establishment exchange has returned an accepting response from the backend. A client SHALL NOT observe a completed upgrade to a stream that the backend refused, that no sidecar could carry, or that failed before the backend was reached.

Where establishment cannot proceed, the client SHALL receive an ordinary response on the unupgraded connection, carrying a status and reason that distinguish a backend refusal, an absent or unreachable sidecar, a sidecar that has not declared the capability the stream needs, and an edge-side rejection from one another.

#### Scenario: Backend refuses the stream

- **WHEN** a client requests a bidirectional stream and the backend answers with a non-accepting response
- **THEN** the client's connection is never upgraded
- **AND** the client receives the backend's response on the unupgraded connection
- **AND** the client does not observe an accepted stream followed by an immediate close

#### Scenario: No sidecar can carry the stream

- **WHEN** a client requests a bidirectional stream against a mount with no connected sidecar
- **THEN** the client's connection is never upgraded
- **AND** the client receives a response whose reason identifies the absence of a sidecar
- **AND** that reason is distinguishable from a refusal by the backend

#### Scenario: Client abandons the request during establishment

- **WHEN** a client disconnects after requesting a bidirectional stream and before the backend has answered
- **THEN** the establishment exchange is reset toward the sidecar
- **AND** the sidecar abandons the establishment against the backend, so no accepted stream is left open at the backend
- **AND** no state for that stream remains at the proxy

#### Scenario: Selected sidecar cannot carry frame-level streams

- **WHEN** a client requests a bidirectional stream against a mount whose only connected sidecar has not declared frame-level bidirectional stream support
- **THEN** the client's connection is never upgraded
- **AND** the client receives a response whose reason names the missing capability
- **AND** that reason is distinguishable from a refusal by the backend and from the absence of a sidecar

### Requirement: Establishment requests are recognised in every form the edge accepts

The proxy SHALL recognise a request to establish a bidirectional stream in each form its client-facing protocols define, including an upgrade on a request/response connection and an extended connect request naming the stream protocol in a dedicated field, and SHALL produce the same establishment exchange for each. The form in which the request arrived SHALL NOT change what the backend observes.

Where an edge protocol version cannot carry a form the client used, the proxy SHALL refuse the request with a reason naming the unsupported form. It SHALL NOT treat such a request as an ordinary request and forward it as one.

#### Scenario: Same exchange from either request form

- **WHEN** the same client request is made once as a connection upgrade and once as an extended connect naming the stream protocol
- **THEN** in both cases the backend observes the same request target, the same offered subprotocol list, and the same forwarded header fields
- **AND** in both cases the same frames sent by the client are delivered to the backend

#### Scenario: Unsupported establishment form is named

- **WHEN** a client uses an establishment form the edge cannot serve
- **THEN** the request is refused with a reason naming the unsupported form
- **AND** the request is not forwarded as an ordinary request
- **AND** the backend does not observe a request for that resource

### Requirement: Establishment requests are validated at the edge before any tunnel exchange

The proxy SHALL reject a malformed establishment request at the edge, before any frame crosses the tunnel. A request that declares an upgrade but omits a field the edge protocol requires, or that names a stream protocol version the proxy does not implement, SHALL be answered with a client-error response; where the protocol defines a way to advertise the versions the proxy does implement, the response SHALL carry it.

An edge-side rejection SHALL be distinguishable in the proxy's own records from a rejection originating at the backend.

#### Scenario: Malformed upgrade never reaches the tunnel

- **WHEN** a client sends an establishment request missing a required handshake field
- **THEN** the client receives a client-error response
- **AND** no establishment exchange is created on the tunnel
- **AND** no sidecar is selected

#### Scenario: Unsupported stream protocol version

- **WHEN** a client requests a stream protocol version the proxy does not implement
- **THEN** the request is refused
- **AND** the response advertises the versions the proxy does implement

#### Scenario: Edge rejection is attributable

- **WHEN** an establishment request is rejected at the edge
- **THEN** the recorded outcome attributes the rejection to the edge
- **AND** it is not reported as a backend or sidecar failure

### Requirement: Subprotocol negotiation is performed by the backend, not the proxy

The proxy SHALL carry the client's complete ordered list of offered subprotocols into the establishment exchange. The proxy SHALL NOT select, reorder, filter, or substitute a subprotocol on the backend's behalf.

The backend's selection, which is at most one value, SHALL be the value the client receives. A backend that selects nothing SHALL be honoured: the stream is established and the client is told that no subprotocol was selected. A backend that selects a value the client did not offer SHALL cause establishment to fail with a distinguishable reason, and the client SHALL NOT be given an accepted stream.

#### Scenario: Whole offered list reaches the backend

- **WHEN** a client offers three subprotocols in a stated order
- **THEN** the backend receives all three in that order
- **AND** none is removed by the proxy

#### Scenario: Backend selection reaches the client

- **WHEN** the backend selects the second of the client's three offered subprotocols
- **THEN** the client's accepting response names exactly that subprotocol
- **AND** it names no other

#### Scenario: Backend selects nothing

- **WHEN** a client offers subprotocols and the backend accepts without selecting one
- **THEN** the stream is established
- **AND** the client's accepting response carries no selected subprotocol

#### Scenario: Backend selects a value the client did not offer

- **WHEN** the backend accepts and names a subprotocol absent from the client's offer
- **THEN** establishment fails
- **AND** the client does not receive an accepted stream
- **AND** the failure reason identifies an invalid subprotocol selection, distinct from a backend refusal

### Requirement: Per-hop handshake fields are regenerated, never relayed

The handshake challenge and its derived acceptance value, the fields that declare the upgrade and its connection tokens, and the stream protocol version field are properties of a single connection. The proxy SHALL generate its own values for each hop and SHALL NOT relay the client's values to the backend or the backend's values to the client.

Not every establishment form defines every one of these. Where the client's protocol defines a challenge, the acceptance value the client receives SHALL be derived from the challenge that client sent, and a backend-supplied acceptance value SHALL never appear in the client's response. Where the client's protocol defines no challenge — the extended connect form, in which the stream is established by the response status alone — the proxy SHALL neither expect, require, generate, nor emit one, and their absence SHALL NOT be treated as a malformed handshake or as a missing required field. The proxy SHALL nevertheless generate whatever the backend hop's own protocol requires, including a challenge the client never sent, because the two hops are negotiated independently.

Which fields a given establishment form defines as required SHALL be a property of that form, and the edge SHALL NOT apply one form's required set to another. A field one form requires and another does not SHALL be absent from the exchange carried for the form that does not define it, rather than synthesised to make the two look alike.

#### Scenario: Challenge does not cross the tunnel

- **WHEN** a client sends a handshake challenge
- **THEN** the backend does not observe that challenge value
- **AND** the backend's own hop uses a challenge generated for it

#### Scenario: A form defining no challenge is not refused for lacking one

- **WHEN** a client establishes a stream by the extended connect form, which defines no handshake challenge
- **THEN** the request is not refused for a missing challenge
- **AND** no acceptance value is emitted to that client
- **AND** the backend hop still carries whatever its own protocol requires, including a challenge the client never sent

#### Scenario: One form's required set is not applied to another

- **WHEN** the same stream is established once by each form the edge accepts
- **THEN** each is validated against the fields its own form defines as required
- **AND** a field one form requires is neither demanded of nor synthesised for the form that does not define it
- **AND** the backend observes the same target, offered subprotocols, and forwarded fields in both cases

#### Scenario: Acceptance value is computed for the client

- **WHEN** the backend accepts and its response carries an acceptance value
- **THEN** the client receives an acceptance value derived from the client's own challenge
- **AND** the backend's acceptance value is not present in the client's response

#### Scenario: Connection-scoped tokens are stripped in both directions

- **WHEN** an establishment request and its response carry upgrade and connection tokens
- **THEN** those tokens are consumed at each hop
- **AND** neither set is relayed to the other hop

### Requirement: Frame masking is a property of a hop

The proxy SHALL unmask frames received from the client and SHALL carry only the unmasked payload over the tunnel. Masking state SHALL NOT be relayed. Frames the proxy sends to a client SHALL be masked or unmasked as that hop's role requires, independently of how the frame arrived.

A client frame that violates the masking rules of the edge protocol SHALL be treated as a protocol violation: the client hop is closed with the defined close code for a protocol error and the offending frame is not carried over the tunnel.

#### Scenario: Payload survives unmasking

- **WHEN** a client sends a masked frame whose payload is arbitrary octets
- **THEN** the backend receives a byte-identical payload
- **AND** no mask value accompanies it

#### Scenario: Improperly masked client frame is a protocol error

- **WHEN** a client sends a frame that violates the edge protocol's masking rules
- **THEN** the client hop is closed with the defined close code for a protocol error
- **AND** the frame is not delivered to the backend
- **AND** other streams on the same tunnel are unaffected

### Requirement: Compression is negotiated per hop and does not exist end to end

Compression of stream frames SHALL be negotiated independently on the client hop and on the backend hop. The proxy SHALL NOT relay a client's compression offer to the backend, and SHALL NOT relay the backend's selected compression parameters to the client. Octets crossing the tunnel SHALL be uncompressed with respect to the stream protocol's compression extension.

The outcome on one hop SHALL NOT constrain the outcome on the other: a compressed client hop with an uncompressed backend hop, and the reverse, SHALL both carry messages faithfully.

The tunnel preserves the structure of every frame it is given, including its reserved bits. The proxy SHALL therefore not hand it a frame still marked as compressed: on receiving a compressed frame the proxy SHALL decompress it and construct, for the tunnel, a frame whose payload is the decompressed octets and whose compression indicator is clear. In the other direction the proxy SHALL construct the frame the receiving hop's own negotiation calls for, setting the indicator only where that hop negotiated compression. A frame arriving on a hop with that indicator set where compression was not negotiated on that hop SHALL be treated as a protocol violation.

#### Scenario: Client compression offer stops at the proxy

- **WHEN** a client offers the compression extension during establishment
- **THEN** the backend's establishment request carries no compression offer derived from the client's
- **AND** the compression parameters the client and proxy agree are not visible to the backend

#### Scenario: Compressed client hop with uncompressed backend hop

- **WHEN** compression is negotiated on the client hop and not on the backend hop
- **THEN** every message is delivered in both directions with identical payload octets
- **AND** neither hop closes the stream

#### Scenario: Backend compression parameters are not imposed on the client

- **WHEN** the backend hop negotiates compression parameters
- **THEN** the client's negotiated parameters are unchanged by that outcome

#### Scenario: Compression indicator does not cross the tunnel

- **WHEN** compression is negotiated on the client hop and a client sends a compressed frame
- **THEN** the frame the proxy constructs for the tunnel carries the decompressed octets with the compression indicator clear
- **AND** the tunnel delivers that frame's finality indicator, reserved bits, and type unaltered
- **AND** the backend, whose hop negotiated no compression, receives an ordinary uncompressed frame

#### Scenario: Compressed frame without negotiated compression is a protocol error

- **WHEN** a client sends a frame carrying the compression indicator on a hop where compression was not negotiated
- **THEN** the client hop is closed with the close defined for a protocol error
- **AND** the frame is not carried over the tunnel

### Requirement: Frame payloads are opaque and are not validated as text

The proxy SHALL treat the payload of every data frame as opaque octets. It SHALL NOT transcode a payload, validate its character encoding, substitute a replacement octet, normalise it, or refuse a frame on account of its content. A payload that is not valid in any character encoding SHALL be carried byte-identically in both directions, and a frame typed as text SHALL be carried as text whatever its octets contain.

Where the edge protocol obliges a sender to emit only valid sequences in a text frame, a payload arriving from the backend that violates that obligation is a fault of the backend, not of the client. The proxy SHALL record it, attributed to the tenancy, and SHALL either carry it or close the client hop with the close defined for a protocol error of that hop; it SHALL NOT repair the payload, substitute octets into it, or silently drop the frame. Whichever it does SHALL be the same for every stream on a mount rather than decided per frame.

The proxy SHALL bound the payload size of a single frame on the client hop, independently of the bound on a whole message and independently of the maximum frame payload the tunnel's counterpart declared. A frame exceeding it SHALL close that stream with the close defined for an oversized message.

#### Scenario: Invalid sequences survive in both directions

- **WHEN** a client sends a binary frame whose payload contains a lone octet that is valid in no character encoding
- **THEN** the backend receives a byte-identical payload
- **AND** no replacement octet is introduced

#### Scenario: A text frame is not validated into a failure

- **WHEN** a client sends a text frame whose payload is not valid in the encoding the edge protocol names
- **THEN** the proxy does not repair the payload and does not substitute octets into it
- **AND** the outcome is the one the mount's configured behaviour states, applied identically to every stream on that mount

#### Scenario: A backend-side violation is attributed to the backend

- **WHEN** a backend emits a text frame whose payload violates the edge protocol's encoding obligation
- **THEN** the condition is recorded and attributed to that tenancy
- **AND** it is not recorded as a fault of the client

#### Scenario: A single oversized frame is bounded independently of the message bound

- **WHEN** a client sends one frame larger than the configured per-frame bound while remaining within the whole-message bound
- **THEN** the stream is closed with the close defined for an oversized message
- **AND** other streams on the same tunnel are unaffected

### Requirement: Fragmentation and control frames follow the edge protocol's interleaving rules

A message may be fragmented across an initial frame and continuation frames, and control frames may be interleaved between those fragments. The proxy SHALL carry each fragment and each interleaved control frame in the order received, SHALL NOT coalesce fragments into one frame, SHALL NOT reorder a control frame relative to the fragments around it, and SHALL NOT begin a second fragmented message on a stream before the first has been completed.

The proxy SHALL treat as a protocol error of the hop that produced it: a continuation frame with no fragmented message in progress; a new non-control frame arriving while a fragmented message is in progress; a control frame that is itself fragmented; and a control frame whose payload exceeds what the edge protocol permits. Each SHALL close that hop with the close defined for a protocol error, and SHALL NOT be carried over the tunnel.

A fragmented message SHALL be subject to the whole-message bound across its fragments taken together, and SHALL NOT be able to exceed that bound by arriving in many small fragments.

#### Scenario: Control frames interleave without reordering

- **WHEN** a client sends the first fragment of a message, then a control frame, then the remaining fragments
- **THEN** the backend observes that same sequence in that same order
- **AND** the fragments are not coalesced and the control frame is not moved

#### Scenario: A continuation with nothing in progress is a protocol error

- **WHEN** a continuation frame arrives on a stream with no fragmented message in progress
- **THEN** that hop is closed with the close defined for a protocol error
- **AND** the frame is not carried over the tunnel

#### Scenario: A second message cannot start mid-fragment

- **WHEN** a new non-control frame arrives while a fragmented message is still in progress
- **THEN** that hop is closed with the close defined for a protocol error
- **AND** the partially received message is discarded rather than delivered

#### Scenario: A fragmented control frame is refused

- **WHEN** a control frame arrives marked as fragmented, or carrying a payload larger than the edge protocol permits for a control frame
- **THEN** that hop is closed with the close defined for a protocol error

#### Scenario: Many small fragments cannot exceed the message bound

- **WHEN** a message arrives as a large number of small fragments whose total exceeds the whole-message bound
- **THEN** the stream is closed with the close defined for an oversized message
- **AND** the octets held for that message never exceed the bound

### Requirement: Message size after decompression is bounded

The proxy SHALL enforce a configured bound on the size of any single message after any decompression it performs, and SHALL enforce it incrementally so that memory held for a message never exceeds the bound regardless of how small the compressed form was. This bound exists to contain one tenant's stream, not to conserve bandwidth.

Exceeding the bound SHALL close that stream with the close defined for an oversized message, distinguishable from an idle close, a lifetime close, a drain close, and a protocol error. Other streams on the same tunnel and the tunnel itself SHALL be unaffected.

#### Scenario: Small compressed frame that inflates past the bound

- **WHEN** a client sends a compressed message far smaller than the bound whose decompressed size greatly exceeds it
- **THEN** decompression stops once the bound is reached
- **AND** memory held for that message never exceeds the bound
- **AND** the stream is closed with the close defined for an oversized message

#### Scenario: One oversized message does not affect neighbours

- **WHEN** a stream is closed for an oversized message
- **THEN** other bidirectional streams on the same tunnel continue to carry frames
- **AND** the tunnel is not torn down

#### Scenario: Message within the bound is delivered

- **WHEN** a compressed message decompresses to a size within the bound
- **THEN** it is delivered in full
- **AND** its payload is byte-identical to what was sent

### Requirement: Liveness is established per hop and end to end

Keepalive control frames are answered by the receiving hop below the application in mainstream implementations, and the wire contract accordingly does not carry them across the tunnel. The proxy SHALL NOT treat a client's answered keepalive as evidence that the backend or the sidecar is alive, and SHALL NOT treat backend-hop keepalive as evidence that the client is alive.

No probe can span both hops, so liveness of a session is composed of three independent facts, each proved by its own mechanism and none substituting for another: the client hop is proved by the proxy's own keepalive against the client; the tunnel is proved by the contract's liveness exchange; and the backend hop is proved by the sidecar's keepalive against the backend, whose expiry the contract requires the sidecar to report as a reset carrying the enumerated code for a counterpart that stopped answering. The proxy SHALL detect an unresponsive client within a configured bound and reset the stream toward the sidecar, SHALL treat that contract reset as the backend having stopped answering, and SHALL close the client with the close defined for a lost backend. The proxy SHALL NOT attempt to prove the backend hop by any probe of its own, because nothing beyond the far hop's protocol layer will answer one.

#### Scenario: Unresponsive client is detected

- **WHEN** a client stops answering keepalive on an otherwise idle stream
- **THEN** within the configured bound the stream is reset toward the sidecar
- **AND** the backend request for that stream is cancelled
- **AND** the sidecar's tunnel remains established and its other streams are unaffected

#### Scenario: Client keepalive does not vouch for the backend

- **WHEN** the backend has stopped answering the sidecar's keepalive while the client continues to answer the proxy's
- **THEN** the sidecar resets the stream over the tunnel with the enumerated code for a counterpart that stopped answering
- **AND** within the configured bound the client is closed with the close defined for a lost backend
- **AND** the stream is not held open on the strength of the client hop's keepalive alone

#### Scenario: A live tunnel does not vouch for the backend

- **WHEN** the sidecar's tunnel continues to answer the contract's liveness exchange while one session's backend has stopped answering
- **THEN** only that session is closed
- **AND** the sidecar's other sessions and its tunnel are unaffected
- **AND** the tunnel being alive is not treated as evidence about that session's backend

#### Scenario: Keepalive is answered at the hop that received it

- **WHEN** a client sends a keepalive probe
- **THEN** the answer the client receives is generated at the hop that received the probe
- **AND** no frame crosses the tunnel as a result of that probe

### Requirement: Idle and lifetime bounds are separate from request bounds

A bidirectional stream SHALL be governed by an idle bound and a lifetime bound that are configurable separately from the bounds governing request/response exchanges. At least one configuration SHALL permit an unbounded lifetime, so that a long-lived session is not terminated by elapsed wall-clock time alone.

The idle bound SHALL be measured on application frames only. Keepalive traffic generated by the proxy or by either peer's protocol layer SHALL NOT reset the idle bound. Reaching a bound SHALL close the stream with the close defined for that bound, and the close for an idle stream SHALL be distinguishable from the close for an exhausted lifetime.

#### Scenario: Idle bound closes a silent stream

- **WHEN** no application frame crosses a stream for longer than the idle bound
- **THEN** the stream is closed with the close defined for an idle stream
- **AND** the backend request is cancelled

#### Scenario: Keepalive alone does not keep a stream alive

- **WHEN** keepalive traffic continues on an otherwise silent stream for longer than the idle bound
- **THEN** the stream is still closed for idleness

#### Scenario: Unbounded lifetime is configurable

- **WHEN** a mount is configured with an unbounded lifetime and an active stream continues to carry frames
- **THEN** the stream remains open past any bound that governs a request/response exchange
- **AND** it is closed only by a party, by the idle bound, or by another stated cause

#### Scenario: Lifetime and idle closes are distinguishable

- **WHEN** one stream reaches the lifetime bound and another reaches the idle bound
- **THEN** each peer receives the close defined for its own cause
- **AND** the two closes differ, so a client can tell which bound ended its stream

### Requirement: Backpressure is applied at the client hop

The bidirectional stream protocol carries no flow control of its own, so the proxy SHALL translate the client connection's write readiness into the credit it grants over the tunnel for that stream. Octets buffered for a client that is not reading SHALL be bounded per stream.

When the bound is exceeded, the proxy SHALL close that stream with the close defined for a peer that cannot keep up, distinguishable from an oversized message and from an idle close. The proxy SHALL NOT allow one slow client to grow unbounded memory or to stall other streams on the same tunnel.

#### Scenario: Slow client slows the backend

- **WHEN** a client reads frames more slowly than the backend produces them
- **THEN** the credit the proxy grants over the tunnel for that stream decreases
- **AND** octets buffered for that client remain within the configured bound

#### Scenario: Client that never reads is closed

- **WHEN** a client stops reading entirely and buffered octets reach the configured bound
- **THEN** the stream is closed with the close defined for a peer that cannot keep up
- **AND** buffered memory for that stream is released
- **AND** the stream is reset toward the sidecar so the backend stops producing for it

#### Scenario: A stalled client does not stall its neighbours

- **WHEN** one client on a tunnel stops reading
- **THEN** other bidirectional streams on that tunnel continue to deliver frames at their own rate

### Requirement: Frames arriving before the client hop is joined are buffered within a bound on both axes

Because the accepting response is withheld until the backend has accepted, a client can begin sending frames before the proxy has finished joining the client hop to the tunnel stream. Frames received in that window SHALL be buffered and then delivered in the order received, ahead of every frame the client sends afterwards. Every protocol in this family has a mandatory opening message, so losing or reordering the first frames breaks the session rather than degrading it.

The buffer SHALL be bounded on both the number of frames and their total octets, and both bounds SHALL be configurable. Exceeding either bound SHALL close the stream with the close defined for exceeded buffering, and the recorded reason SHALL state which of the two bounds was reached. If the join never completes because the stream ends first, buffered frames SHALL be discarded, SHALL NOT be delivered anywhere, and the memory they occupied SHALL be released.

#### Scenario: Early frames are delivered in order

- **WHEN** a client sends several frames immediately after receiving the accepting response and before the client hop is joined to the tunnel stream
- **THEN** the backend receives those frames in the order sent
- **AND** it receives them before any frame the client sent afterwards

#### Scenario: Frame-count bound is reached

- **WHEN** a client sends more frames before the join completes than the configured frame-count bound allows
- **THEN** the stream is closed with the close defined for exceeded buffering
- **AND** the recorded reason identifies the frame-count bound rather than the octet bound

#### Scenario: Octet bound is reached

- **WHEN** the frames a client sends before the join completes exceed the configured total-octet bound while remaining within the frame-count bound
- **THEN** the stream is closed with the close defined for exceeded buffering
- **AND** the recorded reason identifies the octet bound rather than the frame-count bound

#### Scenario: Buffered frames are discarded when the stream ends first

- **WHEN** frames have been buffered and the stream ends before the join completes
- **THEN** the buffered frames are discarded
- **AND** no buffered frame is delivered to any backend
- **AND** the memory they occupied is released

### Requirement: Establishment is evaluated against the mount's origin policy

Bidirectional streams carry no same-origin protection of their own, so a browser on any site can establish one against a mount a tenant intended for its own pages, carrying that user's ambient credentials. The proxy SHALL evaluate an establishment request against an origin policy configured for the mount it matched, before any frame crosses the tunnel.

The origin policy SHALL be one of the attributes a mount is required to carry before it serves traffic, contributed to the set the mount-point capability assembles, so that a mount cannot be created without one and discovered to have none only when the first establishment request arrives. The policy SHALL state explicitly how a request bearing no origin is treated, rather than leaving it to a default that varies by deployment or by instance. A refusal on origin grounds SHALL be an unupgraded response whose reason is distinguishable from a backend refusal, from an absent sidecar, and from a malformed request. The origin policy configured for one tenant's mount SHALL have no effect on the evaluation of a request matching another tenant's mount.

#### Scenario: Disallowed origin is refused at the edge

- **WHEN** an establishment request arrives bearing an origin the mount's policy does not permit
- **THEN** the client's connection is not upgraded
- **AND** no establishment exchange is created on the tunnel
- **AND** the refusal reason identifies the origin policy

#### Scenario: Permitted origin establishes normally

- **WHEN** an establishment request bears an origin the mount's policy permits
- **THEN** the establishment exchange is created on the tunnel
- **AND** on acceptance the stream carries frames in both directions

#### Scenario: A request with no origin follows the declared policy

- **WHEN** an establishment request arrives with no origin
- **THEN** the outcome is the one the mount's policy declares for that case
- **AND** the outcome does not depend on which proxy instance served the request

#### Scenario: Origin policy is scoped to its mount

- **WHEN** one tenant's mount declares a restrictive origin policy
- **THEN** establishment against another tenant's mount is unaffected

### Requirement: New streams are admitted against a concurrency bound

A bidirectional stream holds a client connection, a tunnel stream, timers and buffer memory for as long as the session lasts, which may be hours. Bounding the rate at which requests are admitted therefore does not bound what a tenant consumes. The proxy SHALL bound the number of bidirectional streams concurrently established for a mount and for a tenant, and SHALL evaluate those bounds before creating an establishment exchange.

The per-tenant dimensions these bounds are drawn on are those the tenancy capability enumerates; this capability enforces the long-lived-stream and buffered-octet dimensions at establishment and SHALL NOT define a parallel set of its own. Because a client's establishment request arrives at whichever proxy instance the load balancer chose while the streams a tenant already holds may be spread over every instance, the bound evaluated at establishment SHALL be the tenant's total across the installation on that capability's terms, not the number of streams the admitting instance itself holds. Where the admitting instance cannot account that total, the discipline the tenancy capability requires the installation to declare governs whether the establishment is refused or admitted to a local share, and a refusal on that ground SHALL be distinguishable from a refusal caused by the tenant actually reaching the bound.

An establishment request that would exceed a bound SHALL be refused on the unupgraded connection with a reason identifying the bound reached, distinguishable from a backend refusal and from an absent sidecar. Streams already established SHALL NOT be closed to make room for a new one. Capacity SHALL be returned when a stream ends, by whatever cause.

#### Scenario: Bound reached refuses without upgrading

- **WHEN** a mount is at its configured concurrent-stream bound and a further establishment request arrives
- **THEN** the client's connection is not upgraded
- **AND** no establishment exchange is created on the tunnel
- **AND** the refusal reason identifies the concurrency bound

#### Scenario: Established streams are not evicted

- **WHEN** an establishment request is refused for exceeding a bound
- **THEN** every stream already established on that mount continues to carry frames

#### Scenario: Streams spread across instances count once

- **WHEN** a tenant holds established streams on several proxy instances totalling its configured bound
- **AND** a further establishment request for that tenant arrives at any instance, including one holding none of them
- **THEN** it is refused with the reason identifying the concurrency bound
- **AND** the tenant's total established streams across the installation do not exceed the configured bound

#### Scenario: A degraded-accounting refusal is distinguishable

- **WHEN** an establishment request is refused because the admitting instance could not account the tenant's total across the installation
- **THEN** the reason is distinguishable from the tenant having reached the configured bound
- **AND** the condition is observable to an operator while it holds

#### Scenario: One tenant's exhaustion does not affect another

- **WHEN** one tenant is at its concurrent-stream bound
- **THEN** establishment against another tenant's mount is admitted normally

#### Scenario: Capacity is returned when a stream ends

- **WHEN** a mount is at its bound and an established stream ends
- **THEN** a subsequent establishment request for that mount is admitted

### Requirement: Proxy-originated closes come from a documented vocabulary

Every close the proxy originates SHALL carry a code drawn from a documented, stable vocabulary together with a reason naming the cause. The vocabulary SHALL exclude the code range the stream protocol reserves for application use: tenant applications encode their own error taxonomies in that range, and a proxy-generated code landing inside it is indistinguishable to a client from an error its own backend raised.

Each cause this capability defines SHALL map to exactly one code-and-reason pair, and no two causes SHALL map to the same pair. The mapping SHALL be stable across releases, because clients branch on it. A close originating at a peer SHALL be relayed with the peer's own code and SHALL be recorded as peer-originated rather than proxy-originated.

#### Scenario: Proxy close avoids the application range

- **WHEN** the proxy closes a stream for a cause it detected itself
- **THEN** the close code lies outside the range the stream protocol reserves for application use
- **AND** the close carries the reason defined for that cause

#### Scenario: Each cause is separately identifiable

- **WHEN** streams are ended by each cause this capability defines
- **THEN** each close carries the code and reason defined for its own cause
- **AND** no two causes produce the same code-and-reason pair

#### Scenario: A peer's application close code is not attributed to the proxy

- **WHEN** a backend closes a stream with a code in the application-reserved range
- **AND** the client receives that code unchanged
- **THEN** the proxy records the close as originating at the backend
- **AND** it is not recorded as any of the proxy's own causes

### Requirement: Every disconnect source produces a defined close and complete cleanup

The proxy SHALL define a close for each cause by which a bidirectional stream can end without the peers agreeing to close it: the client going away, the backend going away, the sidecar's tunnel being lost, and the proxy instance shutting down. The surviving end SHALL receive the close defined for the cause that occurred, and no two of these causes SHALL produce the same close.

In every case the proxy SHALL release all state associated with the stream — buffered octets, registrations, and any timer — and SHALL cancel the corresponding work at the other end. A peer that does not complete the closing handshake SHALL be released within a configured bound rather than held indefinitely.

#### Scenario: Client goes away

- **WHEN** a client connection is lost
- **THEN** the stream is reset toward the sidecar
- **AND** the backend request for that stream is cancelled
- **AND** no state for that stream remains at the proxy

#### Scenario: Backend goes away

- **WHEN** the backend closes or fails while the sidecar's tunnel remains connected
- **THEN** the client is closed with the close defined for a lost backend
- **AND** that close differs from the one used when the sidecar's tunnel is lost
- **AND** the sidecar's other streams remain open

#### Scenario: Sidecar tunnel is lost

- **WHEN** a sidecar's tunnel disconnects while it is carrying several bidirectional streams
- **THEN** every client on those streams is closed with the close defined for a lost sidecar
- **AND** each is closed rather than left waiting for an idle bound to expire
- **AND** the count of streams affected is recorded

#### Scenario: Proxy instance shuts down

- **WHEN** a proxy instance terminates while carrying bidirectional streams
- **THEN** each client is closed with the close defined for the proxy going away
- **AND** the corresponding streams are reset toward their sidecars

#### Scenario: Peer never completes the closing handshake

- **WHEN** the proxy has sent a close and the peer neither answers nor disconnects
- **THEN** the connection is dropped within the configured bound
- **AND** the stream's state is released

### Requirement: Planned restarts drain rather than disconnect en masse

When a proxy instance is shutting down in a planned manner, or a sidecar signals that it is draining, the proxy SHALL close the affected bidirectional streams progressively over a configured window rather than simultaneously, so that clients do not all reconnect at the same instant. A planned drain SHALL use a close code distinguishable from an abrupt loss of the same component.

The window and the deadline referred to here are those of the single withdrawal lifecycle the sidecar-registry capability owns, applied to this capability's subject. This capability SHALL NOT introduce a second ordering of phases or a second deadline; what it adds is which close each affected client receives and that the closings are spread rather than simultaneous.

A draining proxy instance SHALL admit no new bidirectional streams, and a draining sidecar SHALL be excluded from selection for new streams while its existing streams continue. Drain SHALL complete as soon as no affected stream remains, without waiting out the remainder of the window.

#### Scenario: Closes are spread across the drain window

- **WHEN** a proxy instance carrying many bidirectional streams begins a planned drain
- **THEN** the streams are closed progressively across the configured window
- **AND** they are not all closed within a single instant

#### Scenario: Planned drain is distinguishable from abrupt loss

- **WHEN** a client's stream is ended by a planned drain
- **THEN** the close code differs from the one used when the same component is lost abruptly
- **AND** the close carries the reason defined for a planned drain

#### Scenario: Draining components take no new streams

- **WHEN** a proxy instance or a sidecar is draining
- **AND** a new establishment request arrives for a mount it serves
- **THEN** that proxy instance or sidecar is not chosen for the new stream
- **AND** the request is served by another if one is available

#### Scenario: Drain ends early when nothing is left

- **WHEN** every affected stream has ended before the drain window elapses
- **THEN** the drain completes immediately
- **AND** shutdown does not wait for the remainder of the window
