## Purpose

Defines what the proxy owns at the client boundary and never delegates to the tunnel or to a sidecar: how each hop determines message framing, which fields are removed or replaced before a message is carried, how the client's identity and the request's authority are established rather than believed, how proxied traffic is kept out of the reach of ordinary application request processing, and how the difference between a tenant's mount and the backend's own root is reconciled in responses. The behaviours here are decided from what the edge itself observed on the connection in front of it, and are never inferred from a field the client supplied or from state the tunnel carries.

## ADDED Requirements

### Requirement: These obligations bind whichever component terminates the client connection

More than one client-facing protocol is served in the first release — including one that multiplexes concurrent exchanges over a single connection and carries its own per-stream flow control — and the consequence recorded in `design.md` D16 is that the component terminating client-facing protocols may be a separate one from the component that matches mounts and holds the tunnel to a sidecar. Every obligation of this capability is stated against "the proxy" and SHALL bind whichever component terminates the client connection, whether that is one component or two. There SHALL be no obligation here that is met by neither because each expected the other to hold it.

Where the termination is a separate component, it SHALL hold the obligations that can only be discharged from the connection itself — framing determination and rejection, request-line and field-section syntax, the request-line and field-section bounds, hop-by-hop removal, establishment of the client identity and of the connection's authority, the per-protocol malformed-message rules, and the closing of a connection whose message boundaries have become unknown — and SHALL convey what it established to its counterpart as fields of the wire contract, in the client-facing role that contract defines. The counterpart SHALL hold the obligations that require the matched mount — reserved dispatch, mount-boundary rewriting, cookie scoping, and admission keyed on the matched tenant and mount — and SHALL NOT re-derive an established value from anything a client supplied.

The single pipeline definition this capability requires for mount-destined traffic SHALL span that boundary: there SHALL be one definition, not one per component, and a request SHALL traverse the same enumerated stages whichever component terminated it. A behaviour this capability requires SHALL produce the same observable outcome whether the edge is one component or two, and the component that produced an edge-generated response SHALL be identifiable to an operator without that changing what the client observes.

Where the terminating component is unavailable, the requests it would have terminated SHALL be refused rather than served by a path that omits these obligations, and no request SHALL reach a mount without having passed them.

A separate terminating component is a component of the installation for every obligation stated of one: it SHALL validate its configuration in the single pass, report its build provenance, answer liveness and readiness, contribute its degraded conditions to the one inventory, and deliver its signals to a configured destination, all as the observability capability requires of any component. It SHALL withdraw under the single ordered withdrawal lifecycle the sidecar-registry capability owns, governed by that one deadline, and SHALL NOT introduce a second ordering or a second deadline for the client connections it holds. Its own surfaces SHALL be separated from tenant traffic and its identifiers reserved on the same terms as any other, so that adding it does not add an unreserved surface.

It is equally a member of the enumeration of separately deployed components `operability/packaging` owns, and SHALL be released as its own artifact under every obligation that capability places on one — a self-contained artifact whose declared configuration is generated from the schema its startup validation reads, whose provenance is fixed at build time, whose contract version range is readable from it while stopped, that carries no secret and no material the component does not run on, and that has passed every release gate. No packaging obligation SHALL be waived for it on the ground that the operator builds and deploys it itself.

#### Scenario: The terminating component is operable like any other

- **WHEN** a deployment whose edge is a separate component is inspected
- **THEN** that component reports its build provenance, answers liveness and readiness, and lists its degraded conditions
- **AND** a missing configuration item refuses its start in one pass naming every failing item
- **AND** its signals arrive at a configured destination

#### Scenario: The terminating component is packaged like any other

- **WHEN** the release for a version whose edge is a separate component is examined
- **THEN** that component has an artifact of its own with a recorded outcome for every release gate
- **AND** its declared contract range is readable from that artifact without starting it
- **AND** no gate is recorded as waived because the operator deploys it itself

#### Scenario: It withdraws under the one lifecycle

- **WHEN** a deployment whose edge is a separate component withdraws that component while it holds client connections and in-flight exchanges
- **THEN** it withdraws readiness, stops admitting, allows in-flight work the configured period, spreads what remains, and exits, in that order
- **AND** it applies the one configured withdrawal deadline rather than a deadline of its own

#### Scenario: The same outcome from either topology

- **WHEN** the same set of malformed, over-large, ambiguously framed, and authority-mismatched requests is sent to a deployment whose edge is one component and to one whose edge is two
- **THEN** each request receives the same status and the same enumerated reason in both
- **AND** no request that is refused in one topology is forwarded in the other

#### Scenario: What the edge established crosses explicitly

- **WHEN** a separate terminating component forwards a request it has validated
- **THEN** the client identity, the scheme, and the authority established for the connection reach the counterpart as contract fields that component set
- **AND** the counterpart derives none of them from a field the client supplied

#### Scenario: No obligation falls between the two

- **WHEN** every obligation of this capability is enumerated against a deployment whose edge is a separate component
- **THEN** each is held by exactly one of the two components
- **AND** none is held by neither

#### Scenario: One pipeline definition, not one per component

- **WHEN** a stage is added to the mount-destined pipeline
- **THEN** it takes effect for every route to a mount in both topologies
- **AND** neither component carries a pipeline definition of its own that the other does not

#### Scenario: An unavailable terminator refuses rather than bypasses

- **WHEN** the component that terminates a client protocol is unavailable
- **THEN** requests in that protocol are refused
- **AND** no request reaches a mount by a path that omitted the obligations of this capability

#### Scenario: The generating component is identifiable without being disclosed

- **WHEN** an edge-generated response is produced by the terminating component and, separately, by its counterpart
- **THEN** an operator can tell which produced each
- **AND** the client observes no difference beyond the status and enumerated reason

### Requirement: The terminating component is an independently scaled tier, not one per proxy instance

The proxy is a multi-instance installation, and where the edge is a separate component that component is a tier of its own: the number of terminating instances SHALL NOT be required to equal the number of proxy instances, and a terminating instance SHALL NOT be bound to one particular proxy instance. Adding, removing, or replacing an instance of either tier SHALL NOT require a change to the other tier's configuration, SHALL NOT require a sidecar to reconnect, and SHALL NOT require a client to reconnect to reach a mount it could reach before.

A request terminated at one instance MAY therefore be dispatched by any proxy instance, including one that holds no tunnel for the matched mount, and the outcome SHALL be the one the registry capability requires for a request arriving at any instance. A terminating instance SHALL NOT be required to reach the proxy instance holding the tunnel for a mount in order for that mount to be served, and SHALL NOT be required to know which proxy instance holds it.

Each instance of either tier SHALL identify itself in the signals it produces, as `operability/observability` requires of any component instance, and a record for an exchange SHALL name the terminating instance as well as the proxy instances that admitted and dispatched it, so that a fault confined to one terminating instance is distinguishable from one affecting the tier and from one in the proxy tier. A terminating instance's readiness SHALL describe only itself: it SHALL NOT report ready because another terminating instance is ready, and SHALL NOT withhold readiness because one is not. Losing its connection to one proxy instance SHALL NOT withdraw its readiness while it can still reach another that can serve.

Where a terminating instance refuses a request under this capability before any proxy instance is involved, the refusal SHALL still be attributable: it SHALL carry a correlation identifier assigned on the terms `operability/observability` states, and the records for it SHALL be retrievable by that identifier without the operator knowing which instance of either tier handled it.

#### Scenario: The two tiers scale independently

- **WHEN** terminating instances are added and removed while the number of proxy instances is unchanged, and then the reverse
- **THEN** no configuration of the other tier is changed
- **AND** no sidecar reconnects and no client is required to reconnect to reach a mount it could reach before

#### Scenario: A terminated request is dispatched by any proxy instance

- **WHEN** a request terminated at one terminating instance is dispatched by a proxy instance that holds no tunnel for the matched mount
- **THEN** it is served by the sidecar whose tunnel is held by another proxy instance
- **AND** the terminating instance was not required to reach the proxy instance holding that tunnel

#### Scenario: A fault in one terminating instance is not the tier's fault

- **WHEN** one terminating instance is failing while the others serve
- **THEN** the records and signals name the terminating instance that produced them
- **AND** an operator can tell that condition apart from the same condition on every terminating instance
- **AND** the readiness of the other terminating instances continues to report success

#### Scenario: Losing one proxy instance does not idle a terminating instance

- **WHEN** a terminating instance loses its contract connection to one proxy instance while another it can reach is ready
- **THEN** it continues to report ready
- **AND** requests it terminates continue to be served

#### Scenario: A refusal before dispatch is still traceable

- **WHEN** a terminating instance refuses a request for malformed framing before any proxy instance is involved
- **THEN** the refusal carries a correlation identifier
- **AND** presenting that identifier retrieves the records for it without naming an instance of either tier

### Requirement: Message framing is generated per hop and never relayed

`Content-Length` and `Transfer-Encoding` describe how a body is delimited on one connection. They are properties of that connection, not of the message. The proxy SHALL determine the framing of an inbound message from the fields present on the connection it arrived on, SHALL remove those fields before the message is carried over the tunnel, and SHALL generate its own framing for each message it emits from the explicitly framed data it actually holds or forwards.

The proxy SHALL NOT copy a received `Content-Length` or `Transfer-Encoding` value onto a message it emits. Any length the proxy states SHALL be the count of octets it actually transfers on that hop.

#### Scenario: Received framing fields are not relayed onto the tunnel

- **WHEN** a client sends a request declaring `Content-Length`
- **THEN** no `Content-Length` and no `Transfer-Encoding` entry appears in the header pairs carried over the tunnel
- **AND** the body octets carried are byte-identical to those the client sent

#### Scenario: Emitted length matches octets emitted

- **WHEN** a backend response is delivered to a client with a stated `Content-Length`
- **THEN** the stated value equals the number of body octets the client receives
- **AND** the stated value is not a copy of the value the backend supplied

#### Scenario: Length is regenerated after the body is altered

- **WHEN** a response body is altered at the edge, so that its octet count differs from the backend's
- **THEN** the framing the client receives describes the altered body
- **AND** the client reads exactly the octets that were emitted and no more

#### Scenario: Framing choice is independent per direction

- **WHEN** a request arrives with a body of known length and the backend response body length is unknown when its head is emitted
- **THEN** the response is delivered under a framing mechanism that does not require the length in advance
- **AND** the response carries no `Content-Length`
- **AND** the request's framing mechanism does not determine the response's

### Requirement: Conflicting or ambiguous framing is rejected, not reconciled

A message whose framing indications disagree SHALL be rejected with 400 (Bad Request) carrying an enumerated reason for malformed framing, and SHALL NOT be forwarded, normalised, or reconciled by preferring one indication over another. This is the request-smuggling surface: two hops that reconcile the same ambiguity differently will disagree about where one message ends and the next begins.

The proxy SHALL reject at minimum: a message carrying both `Content-Length` and `Transfer-Encoding`; a message carrying more than one `Content-Length` field line, whether or not the values agree; a `Content-Length` value that is not a single sequence of digits, or a single field line carrying a list of values; a `Transfer-Encoding` list in which `chunked` is not the final coding, appears more than once, or names an unrecognised coding; and a chunked body whose chunk framing is itself malformed.

Where message boundaries on a connection are derived from these fields, the proxy SHALL NOT read a subsequent message from that connection after such a rejection and SHALL close it, because the position of the next boundary is unknown. Where the transport delimits messages independently of them, the proxy SHALL terminate only the affected exchange.

#### Scenario: Length and transfer coding both present

- **WHEN** a request arrives carrying both `Content-Length` and `Transfer-Encoding`
- **THEN** the request is rejected with 400 and the malformed-framing reason
- **AND** no tunnel frame is generated for that request
- **AND** the connection is closed rather than reused for a subsequent request

#### Scenario: Two length fields disagree

- **WHEN** a request arrives with two `Content-Length` field lines whose values differ
- **THEN** the request is rejected with 400
- **AND** neither value is used

#### Scenario: Duplicate length fields carrying the same value are still rejected

- **WHEN** a request arrives with two `Content-Length` field lines carrying an identical value
- **THEN** the request is rejected with 400
- **AND** the message is not collapsed to a single field line and forwarded

#### Scenario: Chunked is not the final coding

- **WHEN** a request arrives whose `Transfer-Encoding` list places `chunked` before another coding
- **THEN** the request is rejected with 400 and the malformed-framing reason

#### Scenario: Malformed chunk framing mid-body

- **WHEN** a chunked request body contains a chunk header that is not a valid chunk size
- **THEN** the exchange is terminated
- **AND** the connection is closed
- **AND** the already-forwarded portion of that exchange is reset over the tunnel rather than completed

#### Scenario: Backend framing indications carried over the tunnel are discarded, not acted on

- **WHEN** a response arriving from the tunnel carries framing indications among its header pairs, whether or not they conflict
- **THEN** the client receives none of them
- **AND** the proxy frames the response from the octets it actually received, determining the body's extent from the body-completion frame
- **AND** the presence of those fields is recorded
- **AND** the exchange is not failed on that ground

### Requirement: Malformed request lines and field sections are rejected at the edge

The proxy SHALL validate the syntax of the request line and every field line before any part of the request is forwarded. A message failing validation SHALL be rejected with 400 (Bad Request) and SHALL NOT reach a sidecar.

The rules below are those of a client protocol that carries a request line and delimits its field section by line breaks. They SHALL be applied to every message arriving on such a protocol. A client protocol that carries no request line and does not delimit fields by line breaks SHALL be validated against its own malformed-message rules instead, as the following requirement states; the absence of a construct that protocol does not define SHALL NOT be treated as a validation failure, and no such message SHALL be admitted merely because these rules do not describe it.

The proxy SHALL reject at minimum: a field name containing a character not permitted in a field name; whitespace between a field name and its colon; a field line continued onto a following line by leading whitespace, which is obsolete and SHALL NOT be unfolded into a single value; a bare carriage return or line feed within the field section; and a field value containing control characters other than horizontal tab.

#### Scenario: Obsolete line folding is refused, not unfolded

- **WHEN** a request arrives with a field value continued on the next line by leading whitespace
- **THEN** the request is rejected with 400
- **AND** the folded value is not joined into a single field value and forwarded

#### Scenario: Invalid field name character

- **WHEN** a request arrives with a field name containing a space or a separator character
- **THEN** the request is rejected with 400
- **AND** no tunnel frame is generated

#### Scenario: Whitespace before the field separator

- **WHEN** a request arrives with a space between a field name and its colon
- **THEN** the request is rejected with 400

#### Scenario: A construct a protocol does not define is not a failure

- **WHEN** a request arrives on a client protocol that carries no request line and does not delimit its field section by line breaks
- **THEN** it is not rejected for lacking a request line or a line-break-delimited field section
- **AND** it is validated against that protocol's own malformed-message rules
- **AND** it is not admitted merely because the rules of this requirement do not describe it

#### Scenario: Validation precedes routing and reveals nothing about it

- **WHEN** the same malformed request is sent twice, once naming a path that matches a mount and once naming a path that matches none
- **THEN** both are rejected with 400 and the same enumerated syntax reason
- **AND** the two responses are indistinguishable to the client
- **AND** no mount lookup result influences either response

### Requirement: Each client protocol's own malformed-message rules are applied

The rules of the preceding requirement are those of a protocol carrying a request line and a field section delimited by line breaks. More than one client protocol is served, and each defines its own set of messages that are malformed, which the other's rules do not describe. The proxy SHALL apply, for each client protocol it serves, that protocol's own malformed-message rules in addition to the ones common to all of them, and SHALL NOT admit a message on one protocol that the other's rules would have refused merely because the rule was written for the other.

For a client protocol whose field names are defined to be lowercase, a field name carrying an uppercase octet SHALL be refused. For a client protocol that delimits messages independently of the framing fields, the presence of a field that governs a single connection — a connection field, a keep-alive field, a transfer-coding field, an upgrade field, or a field the connection field names — SHALL cause the message to be refused rather than the field merely removed, and a transfer-coding negotiation field carrying any value other than the one that requests trailers SHALL likewise be refused. A stated body length inconsistent with the octets the protocol actually delimited SHALL be refused. A message whose protocol-defined leading fields are absent, repeated, out of order, or present after an ordinary field SHALL be refused.

Each such refusal SHALL carry an enumerated reason distinguishing the rule that was violated, and SHALL be counted separately from the common syntax rejections, so that a protocol whose rules are being violated is identifiable. A refusal SHALL end the exchange concerned; it SHALL end the connection only where the protocol's message boundaries have become unknown, as the framing requirement states.

#### Scenario: An uppercase field name is refused where the protocol forbids it

- **WHEN** a request arrives on a client protocol defining field names as lowercase, carrying a field name with an uppercase octet
- **THEN** the request is refused with an enumerated reason naming that rule
- **AND** the name is not lowercased and forwarded

#### Scenario: A connection-governing field is refused, not stripped

- **WHEN** a request arrives on a client protocol that delimits messages independently of the framing fields, carrying a connection field or a transfer-coding field
- **THEN** the request is refused
- **AND** the field is not merely removed and the request forwarded
- **AND** the reason is distinguishable from the reason for conflicting framing

#### Scenario: The trailers negotiation value is the only one admitted

- **WHEN** one request carries a transfer-coding negotiation field requesting trailers and another carries any other value in it
- **THEN** the first is forwarded and the second is refused
- **AND** the refusal names that rule

#### Scenario: A stated length inconsistent with the delimited octets is refused

- **WHEN** a request states a body length differing from the number of octets the protocol delimited for it
- **THEN** the request is refused
- **AND** neither value is used to frame anything

#### Scenario: Misplaced or repeated leading fields are refused

- **WHEN** a request arrives whose protocol-defined leading fields are absent, repeated, out of order, or placed after an ordinary field
- **THEN** the request is refused
- **AND** the reason names that rule

#### Scenario: One protocol's rules do not admit what another refuses

- **WHEN** the same semantic request is expressed on each client protocol served, in a form each protocol's own rules define as malformed
- **THEN** it is refused on every one of them
- **AND** no protocol admits it because the rule was written for another

#### Scenario: A refusal costs one exchange where boundaries remain known

- **WHEN** a request is refused under this requirement on a protocol that delimits messages independently of the framing fields
- **THEN** only that exchange is terminated
- **AND** other exchanges on the same connection continue

### Requirement: The request line and field section are bounded

The proxy SHALL enforce a configured bound on the length of the request target, on the total octet size of the field section, and on the number of field lines in a request. A request exceeding a bound SHALL be rejected before its body is read and before it is forwarded, with 414 (URI Too Long) for an over-long target and 431 (Request Header Fields Too Large) for an over-large or over-numerous field section.

These bounds SHALL be enforced independently of any bound the tunnel or the sidecar applies, and each rejection SHALL be counted for the tenant whose mount was addressed where one was matched, and against the connection's established client identity otherwise.

#### Scenario: Over-large field section

- **WHEN** a request arrives whose field section exceeds the configured bound
- **THEN** the request is rejected with 431
- **AND** the body is not read
- **AND** no tunnel frame is generated

#### Scenario: Over-long request target

- **WHEN** a request arrives whose target exceeds the configured bound
- **THEN** the request is rejected with 414
- **AND** the rejection is distinguishable from a field-section rejection

#### Scenario: Field count bound

- **WHEN** a request arrives with more field lines than the configured bound, none of which is individually over-large
- **THEN** the request is rejected with 431
- **AND** the event is counted for the tenant whose mount was addressed, if one was matched

#### Scenario: A request just inside every bound is served

- **WHEN** a request arrives whose target, field-section size, and field count are each exactly at the configured bound
- **THEN** the request is forwarded
- **AND** no bound-exceeded event is recorded

### Requirement: Hop-by-hop fields are removed, including those Connection names

The proxy SHALL remove hop-by-hop fields from every message in both directions before it is carried further. Removal SHALL cover both the fields that are hop-by-hop by definition — `Connection`, `Keep-Alive`, `Proxy-Authenticate`, `Proxy-Authorization`, `TE`, `Trailer`, `Transfer-Encoding`, and `Upgrade` — and every field named as a token within the `Connection` field of that same message.

The proxy SHALL NOT rely on the fixed list alone. Tokens in `Connection` SHALL be matched against field names case-insensitively.

Naming a framing field in `Connection` SHALL NOT change how framing was determined: framing is determined and validated first, and a message whose framing was rejected stays rejected.

#### Scenario: A field named in Connection is removed

- **WHEN** a request arrives whose `Connection` field names a custom field, and that custom field is present
- **THEN** neither `Connection` nor the named custom field is carried over the tunnel
- **AND** the backend does not receive the named custom field

#### Scenario: Case-insensitive matching of named tokens

- **WHEN** `Connection` names a field using different letter case than the field line uses
- **THEN** the named field is still removed

#### Scenario: Hop-by-hop removal applies to responses

- **WHEN** a backend response carries `Keep-Alive` and `Connection`
- **THEN** neither reaches the client
- **AND** the remaining response fields reach the client unchanged in value, in relative order, and in number

#### Scenario: Naming a framing field does not defeat framing authority

- **WHEN** a request arrives carrying both `Content-Length` and `Transfer-Encoding`, and its `Connection` field names `Content-Length`
- **THEN** the request is still rejected with 400 for conflicting framing
- **AND** the message is not reframed as though `Content-Length` were absent

#### Scenario: End-to-end fields are not removed

- **WHEN** a request carries `Authorization`, `Content-Type`, and custom application fields not named in `Connection`
- **THEN** all of them reach the backend unaltered

### Requirement: Tunnelling and reflecting methods are answered at the edge, never forwarded

The wire contract carries any method token a client sends and defines no method it refuses; refusing one is edge policy, and this capability holds that policy so that no other capability maintains a second version of it. The policy SHALL be a closed enumeration, and every method outside it SHALL be forwarded unaltered.

A request whose method asks the proxy to become a tunnel to an arbitrary destination SHALL be refused at the edge with an enumerated reason, SHALL NOT be matched to a mount, and SHALL NOT produce a tunnel frame. The proxy is not a forward proxy: honouring such a method in a multi-tenant edge is an open relay and a path to every address the proxy's own network can reach. This SHALL NOT affect the extended form of that method used to establish a bidirectional stream, which names an upgrade protocol in a dedicated field and is an ordinary mount-destined request handled by the bidirectional-stream capability.

A request whose method asks the proxy to reflect the received message back to the sender SHALL be answered by the proxy itself according to the forwarding-count rule its protocol defines, or refused with the status for a method that is not allowed; it SHALL NOT be forwarded. Forwarding it would return to the caller every field the proxy added on the way through, including the client identity the proxy established and any field it uses to authenticate itself to an intermediary.

#### Scenario: The tunnelling method is refused, not forwarded

- **WHEN** a client sends a request whose method asks the proxy to open a tunnel to a named destination
- **THEN** the request is refused with an enumerated reason
- **AND** no name resolution is performed and no connection is opened toward the named destination
- **AND** no mount is matched and no tunnel frame is generated

#### Scenario: The extended form is not caught by the refusal

- **WHEN** a client sends the extended form of that method naming an upgrade protocol in its dedicated field, addressed to a mount
- **THEN** the request is not refused by this policy
- **AND** it is handled as an establishment request for a bidirectional stream

#### Scenario: The reflecting method is answered, not forwarded

- **WHEN** a client sends a request whose method asks for the message to be reflected
- **THEN** the proxy answers it itself or refuses it with the status for a method that is not allowed
- **AND** the backend observes no request
- **AND** no field the proxy added, including the established client identity, is returned to the client

#### Scenario: Every other method is forwarded

- **WHEN** a client sends a request whose method token is outside this policy's enumeration, including one the proxy has never seen
- **THEN** the request is forwarded
- **AND** the method token reaches the backend byte-identically

### Requirement: The proxy records itself in the message path and refuses loops

The proxy SHALL add its own intermediary identity to each message it forwards in both directions, so that a backend and an operator can see that the message traversed it. That identity SHALL consist only of a configured public identifier and SHALL NOT disclose the proxy's software version, build, internal hostname, or instance name.

If a request arrives already bearing this proxy's own intermediary identity, the proxy SHALL refuse it with a status dedicated to loop detection, distinct from the status used for any other gateway failure, and SHALL NOT forward it. Without this, a tenant backend configured to call back through the proxy recurses until a resource bound is reached.

Intermediary identities contributed by other hops SHALL be preserved in the order received and SHALL NOT by themselves cause refusal.

#### Scenario: Intermediary identity is added

- **WHEN** a request is forwarded to a backend
- **THEN** the backend observes an intermediary identity naming this proxy
- **AND** any intermediary identities already present are preserved, in order, ahead of it

#### Scenario: Loop is refused

- **WHEN** a request arrives already naming this proxy as an intermediary
- **THEN** the request is refused with the loop-detection status and an enumerated loop reason
- **AND** it is not forwarded to any sidecar
- **AND** the refusal is distinguishable from the response given when no sidecar is connected

#### Scenario: A foreign intermediary identity is not a loop

- **WHEN** a request arrives naming an intermediary that is not this proxy
- **THEN** the request is forwarded
- **AND** the foreign identity reaches the backend unaltered

#### Scenario: Identity does not disclose internals

- **WHEN** a client inspects the intermediary identity on a response
- **THEN** it contains only the configured public identifier
- **AND** it contains no build version, internal hostname, or instance name

### Requirement: Client identity is established by the proxy, never accepted from the client

The proxy SHALL convey to the backend, in one defined and documented form, the client's network address, the scheme the client used, and the authority the client addressed. Every one of those values SHALL be derived from the connection the request arrived on — its peer address, whether it was secured, and the authority established for it — and never from a field in the request.

Any client-identity or forwarding field present in a request received from an untrusted peer SHALL be removed and replaced by the proxy's own values. This SHALL cover both the standard forwarding field and the legacy per-value fields. The proxy SHALL NOT append its value to a client-supplied one, and SHALL NOT forward a client-supplied one alongside its own.

A peer SHALL be treated as untrusted unless it is a member of a configured set of trusted upstream intermediaries. Where the immediate peer is trusted, the proxy MAY extend the existing chain rather than replace it, up to a configured bound on chain length; the entry the proxy contributes SHALL always be the address the proxy itself observed, and a chain exceeding the bound SHALL be truncated to the entries the proxy can vouch for.

This requirement is the single definition of how the system establishes a peer's source from a connection, and of when a conveyed source may be honoured. It SHALL apply, against the one configured intermediary set, wherever the system accepts a connection — the client edge and the tunnel accept path alike — and no capability SHALL maintain a second intermediary set, a second parsing rule, or a second name for the value. A surface that accepts connections from parties with no authenticated identity behind them SHALL apply this rule and MAY add conditions of its own on top of it, as the tunnel-listener capability does; it SHALL NOT relax it.

#### Scenario: One intermediary set serves every accepting surface

- **WHEN** the configured set of trusted upstream intermediaries is changed
- **THEN** the change governs both the client edge and the tunnel accept path
- **AND** no surface continues to honour a conveyed source from a peer the change removed
- **AND** no second set exists to be configured separately

#### Scenario: Forged forwarding field is discarded

- **WHEN** a client connects directly and sends a forwarding field naming an address of its choosing
- **AND** no trusted upstream is configured for that peer
- **THEN** the backend receives exactly one client-address value
- **AND** that value is the peer address of the client's connection
- **AND** the client-supplied value appears nowhere in the forwarded request

#### Scenario: Multiple forged fields are all discarded

- **WHEN** a request from an untrusted peer carries several forwarding fields, in both the standard and the legacy form
- **THEN** all of them are removed
- **AND** the backend receives only the proxy-established values

#### Scenario: Trusted upstream chain is extended, not believed

- **WHEN** a request arrives from a peer that is a configured trusted intermediary and carries an existing chain
- **THEN** the chain the backend receives ends with the address the proxy observed for that peer
- **AND** the chain does not exceed the configured bound on length

#### Scenario: Scheme and authority are established, not read

- **WHEN** a request arrives over a secured connection carrying a forwarding field that claims an unsecured scheme and a different authority
- **THEN** the backend is told the scheme was secured
- **AND** the backend is told the authority established for the connection
- **AND** neither claimed value reaches the backend

#### Scenario: The conveyed form round-trips

- **WHEN** requests arrive over connections whose peer addresses belong to different address families
- **THEN** each conveyed value, parsed by the single documented rule, yields exactly the peer address the proxy observed
- **AND** the same rule parses every value without knowing the family in advance

### Requirement: The proxy's own decisions use the identity it established

Rate limiting, throttling, admission control, audit records, access logging, and any other proxy decision that depends on who the client is SHALL use the identity the proxy established from the connection. No such decision SHALL read a value supplied in a request field.

Where a proxy decision is recorded for an operator, the record SHALL state the established value, and SHALL NOT substitute a client-supplied value for it.

#### Scenario: Client-supplied field does not influence limiting

- **WHEN** a client sends a stream of requests, varying a forwarding field on every request
- **THEN** every request counts against the same limiter bucket
- **AND** the limit is reached at the same request count as when no such field is sent

#### Scenario: Access records carry the established value

- **WHEN** a request carrying a forged client-identity field is logged
- **THEN** the record states the peer address of the connection
- **AND** the forged value is either absent from the record or labelled as client-supplied

### Requirement: The request authority is bound to the authority established by the connection

Every connection SHALL have exactly one established authority, fixed when the connection was accepted: for a secured connection, the name negotiated in the handshake; for an unsecured connection, the authority the listener is configured to serve. The proxy SHALL compare the authority named in a request against that established authority, and SHALL reject a mismatch with 421 (Misdirected Request), distinguishable both from the response given for an authority that matches no tenant and from an authorisation failure.

A request carrying no authority, or carrying more than one authority field line, SHALL be rejected with 400. Mount selection and tenant selection SHALL use the authority established for the connection, never an unvalidated field value.

#### Scenario: Authority mismatch is refused distinguishably

- **WHEN** a connection is established for one tenant's hostname and the request names a different tenant's hostname
- **THEN** the request is rejected with 421
- **AND** the rejection is distinguishable from the response given for a hostname that matches no tenant
- **AND** no tunnel frame is generated

#### Scenario: Missing authority

- **WHEN** a request arrives with no authority field and no authority in its target
- **THEN** the request is rejected with 400

#### Scenario: Repeated authority fields

- **WHEN** a request arrives with two authority field lines, whether or not their values agree
- **THEN** the request is rejected with 400
- **AND** neither value is used for routing

#### Scenario: A reused connection cannot change authority

- **WHEN** a client reuses one connection to send a second request naming an authority other than the one established for that connection
- **THEN** the second request is rejected with 421
- **AND** the first request's outcome is unaffected

#### Scenario: Routing does not follow the field

- **WHEN** a request arrives whose authority field names a tenant other than the one the connection was established for
- **THEN** no mount belonging to the named tenant is selected
- **AND** the tenant named in the field observes no traffic from that request

### Requirement: Authority-bearing request targets are resolved explicitly

When a request target carries its own authority, the proxy SHALL treat that authority as the request's authority and SHALL require it to match the authority established by the connection, rejecting a mismatch with 421 as it would an authority-field mismatch. Where both a target authority and an authority field are present and disagree, the request SHALL be rejected with 400 rather than one being preferred.

An authority in a request target SHALL NEVER cause the proxy to open a connection toward the named host or to select a destination outside the configured mounts. The proxy is not a forward proxy.

#### Scenario: Absolute-form target matching the connection

- **WHEN** a request target carries the same authority the connection established
- **THEN** the request is routed exactly as if the authority had been supplied in the authority field
- **AND** the target carried over the tunnel retains its components as received

#### Scenario: Absolute-form target naming a foreign host

- **WHEN** a request target carries an authority for a host the proxy does not serve
- **THEN** the request is refused with 421
- **AND** the proxy performs no name resolution and opens no connection toward the named host

#### Scenario: Target authority and authority field disagree

- **WHEN** a request carries an authority in its target and a different authority in its authority field
- **THEN** the request is rejected with 400
- **AND** neither authority is used for routing

### Requirement: Route selection does not alter the forwarded target

The proxy SHALL derive the mount selection and the forwarded target from the same received octets. Any normalisation the proxy performs in order to match a mount SHALL be applied to a working copy only; the target carried over the tunnel SHALL remain in the form received, less the mount prefix the mount definition specifies.

A request whose target, after the normalisation used for matching, refers to a position outside the matched mount SHALL be rejected rather than forwarded, and SHALL NOT be re-matched against a different mount. Two targets that differ only in how a path separator is encoded SHALL NOT select different mounts.

#### Scenario: Matching normalisation is not forwarded

- **WHEN** a request target contains `%2F` inside a path segment
- **THEN** the mount match is computed without splitting that segment
- **AND** the target carried over the tunnel still contains `%2F` undecoded

#### Scenario: Escape above the mount is refused

- **WHEN** a request target uses relative path segments that resolve above the matched mount's prefix
- **THEN** the request is rejected
- **AND** no mount other than the originally matched one is consulted
- **AND** no tunnel frame is generated

#### Scenario: Encoded and literal separators cannot select different mounts

- **WHEN** one request's target contains a literal separator between two path segments
- **AND** a second request's target contains the percent-encoded form of that separator at the same position
- **THEN** the two requests do not select different mounts
- **AND** either both are served by the same mount or the encoded one is rejected

### Requirement: The proxy's own endpoints are unreachable as tenant traffic

The set of paths the proxy serves itself is the reserved enumeration owned by the mount-point capability; this capability does not maintain a second one. The edge SHALL dispatch a request whose target falls under a reserved prefix to the proxy's own handling, and SHALL do so before any mount is looked up, so that no mount definition, however it came to exist, can cause a reserved target to be forwarded. Without this, a tenant can mount over the tunnel endpoint and cause the sidecar's own connection to be proxied through the proxy.

Reserved dispatch SHALL NOT exempt a request from the framing, syntax, size, and authority checks this capability defines: those SHALL be applied first, and a request rejected by them SHALL be rejected whether or not its target is reserved.

#### Scenario: A request under a reserved prefix is not proxied

- **WHEN** a request arrives for a target under a reserved prefix while a mount exists whose prefix would otherwise match it
- **THEN** the proxy serves the request itself
- **AND** no tunnel frame is generated
- **AND** no sidecar observes the request

#### Scenario: Reserved dispatch precedes mount lookup

- **WHEN** a request arrives for a target under a reserved prefix
- **THEN** it is dispatched to the proxy's own handling before any mount lookup is performed
- **AND** the outcome is the same whether or not a mount exists whose prefix would otherwise match

#### Scenario: A reserved path is still subject to edge validation

- **WHEN** a request for a target under a reserved prefix arrives carrying conflicting framing indications
- **THEN** it is rejected with 400 and the malformed-framing reason
- **AND** it is not answered by the proxy's own handling of that target

#### Scenario: A target merely resembling a reserved prefix is proxied normally

- **WHEN** a request arrives for a target that shares a leading portion with a reserved prefix but does not fall under one at a segment boundary
- **THEN** the request is matched against mounts as ordinary traffic
- **AND** it is forwarded to the sidecar for the matched mount

### Requirement: Proxied traffic bypasses application request processing

Traffic destined for a mount SHALL be handled by a pipeline in which no application-level request processing runs. Observably, for a request that matches a mount: the request body SHALL NOT be read, parsed, or consumed before it is forwarded; the method SHALL NOT be overridden by a body or query parameter; no content negotiation SHALL be applied and no request SHALL be refused by the proxy for its media type or its stated acceptable media types; no session SHALL be established, read, or written; and no cross-site-request protection SHALL be applied.

The test of this requirement is that a request bearing any media type and any method token reaches the backend with its method, fields, target, and body octets unaltered, by every route that reaches that mount. Method fidelity itself is specified by the wire contract; what this requires is that no edge pipeline stage exists that could violate it. The sole methods exempt are the two this capability's closed method policy answers at the edge; no other method, and no media type, is a reason for the proxy to refuse or alter a mount-destined request.

This pipeline SHALL have a single definition, used by every means of reaching a mount, so that no capability can specify a second one and leave the two to drift. The exemption SHALL be bounded to traffic destined for a mount: a request to an endpoint the proxy serves on its own behalf SHALL retain the ordinary request processing that endpoint requires.

#### Scenario: A form-encoded body is not consumed

- **WHEN** a client sends a request whose media type is one an application body parser would normally claim, with a non-empty body
- **THEN** the backend receives that body byte-for-byte
- **AND** the body is not empty at the backend

#### Scenario: Structured request bodies survive

- **WHEN** a client sends a structured document body and a multipart body in separate requests
- **THEN** the backend receives each body byte-for-byte
- **AND** no boundary, ordering, or whitespace within either body is altered

#### Scenario: Method override is not honoured

- **WHEN** a client sends a request whose body or query contains a parameter that an application convention would treat as a method override
- **THEN** the backend receives the method that was on the request line
- **AND** the parameter is forwarded as ordinary data

#### Scenario: Media type is never a reason for refusal

- **WHEN** a client sends a request with an unusual media type, and separately one whose acceptable-media-type field names only types the proxy does not produce
- **THEN** both requests are forwarded
- **AND** neither is refused with a not-acceptable or unsupported-media-type status generated by the proxy

#### Scenario: No cross-site protection applies

- **WHEN** a client sends a state-changing request to a mount carrying no token an application convention would require
- **THEN** the backend receives the request
- **AND** the proxy generates no rejection of its own

#### Scenario: The rule holds on every route to a mount

- **WHEN** the same request is sent to one mount by path prefix under a shared hostname and by that tenant's own hostname
- **THEN** the backend receives the same method, the same field sequence, the same target below the mount, and byte-identical body octets in both cases
- **AND** neither route refuses a request the other forwards

#### Scenario: The exemption does not spread beyond proxied traffic

- **WHEN** a request arrives for an endpoint the proxy serves on its own behalf, such as an administrative or authentication endpoint
- **THEN** the ordinary request processing for that endpoint still applies, including its body parsing and its cross-site protection
- **AND** the exemption granted to mount-destined traffic does not disable it

### Requirement: The proxy adds nothing to a proxied response beyond an enumerated set

A response the proxy relays SHALL carry the backend's fields, in the order received, less the hop-by-hop fields removed by this capability, and altered only in the ways this capability enumerates: the framing the proxy generated, the proxy's intermediary identity, references rewritten by the mount-boundary policy, and cookie scope constrained by the tenant-cookie requirement.

The proxy SHALL NOT add a session field, a caching directive, a content coding, a security policy field, or any other field of its own to a proxied response. The proxy SHALL NOT decompress, recompress, or otherwise re-code a response body.

#### Scenario: Response field set is accountable

- **WHEN** a backend returns a response with a known set of fields
- **THEN** every field the client receives is either one the backend sent or a member of the enumerated set
- **AND** no field outside that accounting is present

#### Scenario: No session is attached

- **WHEN** a client makes several requests to a mount
- **THEN** no cookie originating from the proxy is set on any response
- **AND** the client is not required to carry proxy state between requests

#### Scenario: Content coding is passed through

- **WHEN** a backend returns a body with a content coding applied
- **THEN** the client receives the coded octets and the coding declaration unchanged
- **AND** the proxy neither decodes the body nor applies an additional coding

#### Scenario: An uncoded body is not coded

- **WHEN** a client offers a content coding and the backend returns an uncoded body
- **THEN** the client receives the uncoded octets
- **AND** the proxy does not compress the response on the backend's behalf

### Requirement: Mount-boundary rewriting has an explicit per-content-type policy

A mount means the backend's root is not the client's root, so an absolute reference the backend emits points outside the tenant's namespace. The proxy SHALL rewrite such references so that they resolve within the mount, and the set of references it rewrites SHALL be an explicit policy stated per content type and per field, with a named owner, rather than a heuristic scan.

The policy SHALL cover, at minimum: `Location`; `Link` targets, including relations used to advertise session resources; `Destination`; the `href` elements inside multi-status response bodies; and the resource references inside media playlist documents. Rewriting SHALL apply only to references whose authority and path place them within the tenant's own backend namespace; a reference naming a third-party authority SHALL be left unchanged.

A relative reference SHALL be left unchanged, because a client resolves it against a request target that already carries the mount prefix.

#### Scenario: Absolute location is brought inside the mount

- **WHEN** a backend responds to a creation request with a `Location` naming an absolute path at the backend's root
- **THEN** the client receives a `Location` whose path begins with the mount's prefix
- **AND** a subsequent request to that location reaches the same backend resource

#### Scenario: Relative location is left alone

- **WHEN** a backend responds with a `Location` containing a relative reference
- **THEN** the client receives that reference unchanged

#### Scenario: Typed link fields are rewritten

- **WHEN** a backend emits several `Link` fields with different relations, one of which names an absolute path at the backend's root
- **THEN** the absolute one is rewritten into the mount
- **AND** the number, order, relations, and remaining parameters of the `Link` fields are unchanged

#### Scenario: References inside a multi-status body are rewritten

- **WHEN** a backend returns a multi-status response whose body contains `href` elements naming absolute paths at the backend's root
- **THEN** each `href` the client receives names a path inside the mount
- **AND** no other element of the document is altered

#### Scenario: Playlist resource references are rewritten

- **WHEN** a backend returns a media playlist containing absolute resource references
- **THEN** the client receives references that resolve inside the mount
- **AND** a client fetching each reference reaches the intended segment

#### Scenario: Third-party references are untouched

- **WHEN** a backend emits a reference naming an authority the proxy does not serve
- **THEN** the reference is forwarded unchanged

#### Scenario: A host-routed mount consumes no prefix, so nothing is rewritten

- **WHEN** a mount reached by a resolved hostname, which consumes no path prefix, returns an absolute reference at the backend's root
- **THEN** the reference is forwarded unchanged
- **AND** no prefix is inserted into it, because the backend's root and the client's root are the same position

#### Scenario: A reference already inside the mount is not rewritten twice

- **WHEN** a backend emits an absolute reference whose path already begins with the mount's prefix
- **THEN** the client receives that reference unchanged
- **AND** the prefix does not appear twice

### Requirement: Content outside the rewriting policy passes through unchanged

Content whose type is not named in the rewriting policy SHALL be forwarded byte-for-byte. The proxy SHALL NOT infer references, scan bodies of unknown type, or apply a rewrite because a body resembles a covered type.

Where a covered content type is declared but the body cannot be parsed as that type, the proxy SHALL forward it unchanged and SHALL record that rewriting was skipped, rather than emitting a partially rewritten body.

#### Scenario: Unknown content type is untouched

- **WHEN** a backend returns a body of a content type the policy does not name, containing text that resembles an absolute reference
- **THEN** the client receives the body byte-for-byte
- **AND** no octet of it has been altered

#### Scenario: Markup bodies are not scanned

- **WHEN** a backend returns a markup document containing absolute links at the backend's root
- **AND** that content type is not named in the policy
- **THEN** the document is forwarded byte-for-byte
- **AND** none of its links is rewritten

#### Scenario: Unparsable covered type passes through rather than partially rewriting

- **WHEN** a backend returns a body declaring a covered content type but whose content is not well-formed for that type
- **THEN** the body is forwarded byte-for-byte
- **AND** the skipped rewrite is recorded for an operator
- **AND** the client never receives a body that was rewritten in part

### Requirement: Rewriting is bounded and does not defeat incremental transfer

Body rewriting SHALL be subject to a configured bound on the number of octets the proxy will hold in order to perform it. A body exceeding that bound SHALL be forwarded unrewritten with the omission recorded, rather than buffered without limit.

Rewriting SHALL NOT be applied to a response that must be delivered incrementally. The decision whether to rewrite SHALL be made before the response head is emitted to the client, and a response whose head has already been forwarded SHALL NOT be retroactively rewritten.

#### Scenario: Oversized body is forwarded unrewritten

- **WHEN** a response of a covered content type exceeds the configured rewriting bound
- **THEN** the body is forwarded unrewritten
- **AND** the octets the proxy holds for that response stay within the bound
- **AND** the omission is recorded

#### Scenario: Streaming response is never buffered to rewrite

- **WHEN** a backend emits a response head and then produces body octets over a long period
- **THEN** the head is forwarded to the client before the body completes
- **AND** the body octets are forwarded as they arrive
- **AND** no rewriting is attempted on that response

#### Scenario: Rewriting changes framing consistently

- **WHEN** a rewritten body differs in length from the backend's body
- **THEN** the framing the client receives describes the rewritten body
- **AND** the client reads the whole rewritten body and no more

### Requirement: Cookies a backend sets are scoped to that tenant's mount

Where more than one tenant is reachable under one hostname, the proxy SHALL ensure that a cookie set by one tenant's backend is not transmitted by the client to another tenant's mount. The proxy SHALL constrain the path scope of each `Set-Cookie` a backend emits so that it lies within the mount that produced it, and SHALL remove or narrow a domain scope that would widen the cookie beyond the hostname the request arrived on, including one naming a suffix at or above the registrable-domain boundary of that hostname.

Each `Set-Cookie` field line SHALL be treated individually; the presence of several SHALL NOT cause any of them to be merged, dropped, or reordered.

Where a mount is reached on a hostname dedicated to a single tenant, the proxy SHALL leave cookie scope unmodified, because no other tenant shares the hostname.

#### Scenario: Cookie set at the backend root does not leak across tenants

- **WHEN** a backend behind tenant A's mount on a shared hostname sets a cookie scoped to the root path
- **AND** the client subsequently requests tenant B's mount on the same hostname
- **THEN** tenant B's backend does not receive that cookie

#### Scenario: The cookie still works for its own tenant

- **WHEN** the same client subsequently requests any path within tenant A's mount
- **THEN** tenant A's backend receives that cookie
- **AND** its name, value, and remaining attributes are unaltered

#### Scenario: Domain widening is refused

- **WHEN** a backend sets a cookie naming a domain broader than the hostname the request arrived on
- **THEN** the widened scope is not transmitted to the client
- **AND** the outcome is recorded for the tenant

#### Scenario: A registry-level domain scope is refused

- **WHEN** a backend sets a cookie whose domain names a suffix at or above the registrable-domain boundary of the request hostname
- **THEN** that domain scope is not transmitted to the client
- **AND** the cookie, if transmitted at all, is scoped no wider than the hostname the request arrived on

#### Scenario: Several cookie fields are each handled

- **WHEN** a backend sets three cookies in one response
- **THEN** the client receives three `Set-Cookie` field lines
- **AND** each is scoped independently
- **AND** their order is unchanged

#### Scenario: A dedicated hostname is left alone

- **WHEN** a mount is reached on a hostname serving only that tenant
- **AND** its backend sets a cookie scoped to the root path
- **THEN** the client receives the cookie exactly as the backend set it

### Requirement: Cookies a client presents are filtered to the matched mount

Where more than one tenant is reachable under one hostname, the proxy SHALL forward to a backend only those cookies whose scope covers the matched mount. A cookie whose scope belongs to another tenant's mount on the same hostname SHALL NOT be forwarded, and SHALL NOT appear anywhere in the forwarded request.

Where the client presents its cookies split across more than one field line, the proxy SHALL recombine them using the separator the cookie format requires, which is not the separator used for ordinary repeated fields.

Where a mount is reached on a hostname dedicated to a single tenant, the proxy SHALL forward the client's cookies unfiltered.

#### Scenario: Foreign cookies are withheld

- **WHEN** a client holds cookies set by two tenants sharing a hostname and requests one tenant's mount
- **THEN** the backend receives only the cookies scoped to that mount
- **AND** the other tenant's cookie names and values are absent from the forwarded request

#### Scenario: Split cookie fields are recombined correctly

- **WHEN** a client's cookies arrive split across several field lines
- **THEN** the backend receives them joined by the cookie separator
- **AND** no cookie name or value is altered by the joining

#### Scenario: A dedicated hostname forwards everything

- **WHEN** a client presents several cookies to a mount on a hostname serving only that tenant
- **THEN** the backend receives all of them
- **AND** none is withheld or rewritten

### Requirement: Admission limits are keyed on values the client cannot forge

The proxy SHALL apply admission limits keyed on values it established itself — at minimum the client identity established for the connection, the matched tenant, and the matched mount. A limiter key SHALL NOT be derived from any request field, because a client can vary such a field per request and obtain a fresh allowance each time.

The per-tenant dimensions these limits are drawn on are those the tenancy capability enumerates; this capability holds the arrival-rate dimension at the edge and SHALL NOT define a parallel per-tenant dimension of its own. What it adds is the key the limit is applied under and the response a limited client receives.

A limited request SHALL be refused with 429 (Too Many Requests), SHALL carry the applicable limit, the remaining allowance, and when the client may retry, and SHALL NOT be forwarded. Limits SHALL be accounted per tenant, so that one tenant exhausting its allowance does not consume another's.

The edge is a multi-instance tier, so the scope over which a limit is counted SHALL be stated rather than left to be discovered. The limit keyed on the matched tenant is an entry in the tenancy capability's enumeration and is therefore accounted for the installation on that capability's terms: a tenant's arrivals SHALL be counted once across every instance that admits them, a tenant whose traffic all reaches one instance SHALL be able to consume its whole configured allowance there, and adding instances SHALL NOT multiply any tenant's allowance. The value reported to a limited client SHALL be the configured limit, never a per-instance share of it. Where accounting is degraded, the discipline the tenancy capability requires the installation to declare governs what is admitted, and the refusal SHALL be distinguishable from a refusal caused by the tenant actually reaching its configured limit.

The limit keyed on a client identity the proxy established from a connection, applied before the arrival has been attributed to a tenancy, SHALL be accounted per accepting instance under the closed exception the tenancy capability states, for the reason stated there: an installation-wide count taken on every arrival is coordination work any unidentified party could cause at an instance it never connected to. That accounting SHALL be declared as per-instance wherever the bounds in force are retrieved, SHALL be observable per instance, SHALL NOT be attributed to any tenancy, and SHALL NOT be the means by which the per-tenant arrival-rate limit is enforced.

Limiter state SHALL itself be bounded per instance: the number of keys an instance retains SHALL be subject to a configured bound, and keys SHALL be reclaimed by age, so that traffic from many distinct clients cannot grow it without limit. That bound SHALL NOT be relied on as a bound on any tenant's arrival rate.

#### Scenario: Rotating a request field does not defeat the limit

- **WHEN** a client sends requests beyond the configured allowance, sending a distinct value in a credential-shaped field on each request
- **THEN** requests beyond the allowance are refused with 429
- **AND** the refusal occurs at the same request count as when no such field is sent

#### Scenario: Refusal is informative and terminal at the edge

- **WHEN** a request is refused for exceeding an allowance
- **THEN** the response carries the applicable limit, the remaining allowance, and a retry time
- **AND** no tunnel frame is generated for that request
- **AND** the sidecar observes no corresponding exchange

#### Scenario: Tenants do not share an allowance

- **WHEN** one tenant's mount is saturated to its limit
- **THEN** requests to another tenant's mount are admitted normally

#### Scenario: A tenant's allowance is not multiplied by the instances it reaches

- **WHEN** one tenant distributes its clients across every instance of the edge until its arrivals reach the configured limit in total
- **THEN** a further request for that tenant is refused with 429 at whichever instance it arrives
- **AND** the total admitted does not exceed the configured limit
- **AND** adding further instances does not admit more

#### Scenario: One instance can serve the whole allowance

- **WHEN** every request for a tenant arrives at a single instance while accounting is not degraded
- **THEN** the tenant is admitted up to its whole configured limit at that instance
- **AND** the limit reported in a 429 is the configured limit rather than a share of it

#### Scenario: A degraded-accounting refusal is distinguishable

- **WHEN** an instance cannot account the arrival-rate dimension installation-wide and refuses a request under the declared discipline
- **THEN** the refusal is distinguishable, to an operator, from a refusal caused by the tenant reaching its configured limit
- **AND** the condition is observable while it holds

#### Scenario: The pre-attribution limit is declared per instance and charged to no tenant

- **WHEN** an operator retrieves the bounds in force at the edge
- **THEN** the limit keyed on an established client identity before attribution to a tenancy is identified as accounted per accepting instance
- **AND** its consumption is retrievable per instance
- **AND** reaching it is not recorded as a per-tenant bound refusal and is attributed to no tenancy

#### Scenario: Allowance recovers

- **WHEN** a limited client waits until the retry time it was given
- **THEN** its next request is admitted

#### Scenario: Limiter state cannot be grown without bound

- **WHEN** requests arrive from more distinct client identities than the configured key bound
- **THEN** the number of retained limiter keys stays within that bound
- **AND** keys are reclaimed by age rather than accumulating
- **AND** limits continue to be enforced for clients still sending traffic

### Requirement: Edge-generated responses are identifiable and never reflect input unsafely

A response the proxy generates itself SHALL be distinguishable, to an operator, from a response relayed from a backend, even where the two carry the same status. Every edge rejection SHALL carry a stable machine-readable reason drawn from an enumerated set, and SHALL NOT convey a rendering of a host-language value.

An edge-generated response SHALL NOT disclose internal state: no backend address, no sidecar identity, no internal host or process reference, and no indication of whether a mount exists beyond what the status itself conveys. Where an edge-generated response includes any value taken from the request, that value SHALL be escaped for the media type in which it is rendered, and the escaping SHALL be ordered so that no escaped sequence can be re-interpreted as markup.

#### Scenario: Edge rejection is attributable

- **WHEN** the edge rejects a request for malformed framing and, separately, a backend returns the same status
- **THEN** an operator can distinguish the two in the recorded telemetry
- **AND** each carries a distinct machine-readable reason

#### Scenario: Reflected input is escaped

- **WHEN** a rejected request contains markup characters in a value the error page displays
- **THEN** the rendered page contains only the escaped form
- **AND** it contains no unescaped markup delimiter from the request
- **AND** no escaped sequence decodes to markup when read once by the client

#### Scenario: No internal detail leaks

- **WHEN** a request fails because no sidecar is connected for the matched mount
- **THEN** the client receives a gateway status and an enumerated reason
- **AND** the response names no backend address, sidecar identity, or internal process reference

#### Scenario: The reason vocabulary is closed

- **WHEN** any edge rejection specified by this capability occurs
- **THEN** the reason it carries is a member of the enumerated set
- **AND** no rejection conveys a free-form or host-language-rendered reason
