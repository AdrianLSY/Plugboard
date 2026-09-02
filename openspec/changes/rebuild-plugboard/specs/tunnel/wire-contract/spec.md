## Purpose

Defines the versioned protocol spoken between the proxy and a sidecar over the persistent tunnel: how an HTTP message, a bidirectional stream, and a datagram are represented, how many concurrent exchanges are multiplexed and flow-controlled over one connection, and how a proxy and a sidecar of different versions negotiate what they can do for each other. This is the only artifact in the system that cannot be corrected after release, because sidecars run in tenants' infrastructure and are never force-upgraded. The contract is deliberately blind to the proxy's topology, and that is stated here rather than left to be inferred: the proxy is a multi-instance installation, a tunnel is held by exactly one instance, and nothing on the wire names an instance or reveals how many there are. An exchange a sidecar receives is indistinguishable on the wire whether the instance holding its tunnel admitted it or another instance dispatched it there, and a sidecar SHALL NOT be required to know, to be told, or to be able to infer which instance admitted an exchange. Everything that follows is therefore a property of one tunnel and its exchanges; selecting a sidecar across instances is `tunnel/sidecar-registry`'s.

## ADDED Requirements

### Requirement: Contract version negotiation

The contract SHALL carry a version independent of the version of any software implementing it. Each side SHALL declare the versions it supports as an inclusive lowest and highest pair and SHALL support every version between them. The tunnel SHALL operate at the highest version both sides support. A tunnel with no overlapping version SHALL be refused with a distinguishable error rather than established, and a declaration whose highest is below its lowest SHALL be refused with an enumerated code distinct from that one.

The negotiated version SHALL be carried explicitly in the tunnel establishment declaration and SHALL NOT be derived from any field of the underlying transport's own handshake or from the transport-level protocol version of the underlying connection.

The negotiated version SHALL be fixed for the life of the tunnel connection. A frame kind, field, or construct the contract introduced above the negotiated version SHALL be a tunnel protocol violation with a cause naming version misuse, distinguishable from the stream reset produced by an unimplemented kind at the negotiated version. A version a side does not know SHALL NOT be treated as compatible with any version it does know.

#### Scenario: Overlapping version range

- **WHEN** a sidecar declares support for contract versions 1 through 2 and the proxy supports 2 through 3
- **THEN** the tunnel is established at contract version 2
- **AND** both sides report the negotiated version in their connection telemetry

#### Scenario: No overlapping version

- **WHEN** a sidecar declares support only for contract version 1 and the proxy supports only 3 and above
- **THEN** the tunnel is refused
- **AND** the sidecar receives an error identifying version incompatibility as the cause, distinct from an authentication failure
- **AND** no mount is served by that sidecar

#### Scenario: Version is carried explicitly, not derived from the transport

- **WHEN** two tunnels are established with identical declared version ranges over two different underlying transports
- **THEN** both negotiate the same contract version
- **AND** in each the negotiated version is read from the establishment declaration and from no transport handshake field
- **AND** the same conformance run for that version passes over both

#### Scenario: An inverted version range is refused

- **WHEN** a sidecar declares a highest supported version below its lowest
- **THEN** the tunnel is refused with a code naming a malformed version declaration
- **AND** the refusal is distinct from a refusal for no overlapping version

#### Scenario: A construct from a later version is a violation, not an unknown kind

- **WHEN** a peer emits a frame kind the contract introduced above the negotiated version
- **THEN** the tunnel is failed with a cause naming version misuse
- **AND** the outcome is distinguishable from a stream reset for an unimplemented kind

#### Scenario: An unknown higher version is not assumed compatible

- **WHEN** a peer declares support only for a version above everything the counterpart knows
- **THEN** the tunnel is refused as having no overlapping version
- **AND** it is not established at the counterpart's highest known version

### Requirement: Tunnel establishment is a bounded, ordered exchange

The tunnel establishment declaration SHALL be the first frame each side sends on a tunnel connection, and any frame preceding it SHALL be a tunnel protocol violation. Each side SHALL bound the time it waits for its peer's declaration and SHALL fail the tunnel with a distinguishable cause when that bound elapses.

A declaration SHALL be bounded in total size, in the number of capability names it carries, and in the length of each name. A declaration exceeding any of these SHALL be refused before its contents are retained, and its unrecognised names SHALL NOT be retained or recorded individually. A declaration that is internally inconsistent SHALL be refused with a cause distinguishable from version incompatibility and from authentication failure.

A second declaration on an established tunnel SHALL be a tunnel protocol violation. The authenticated identity bound to a tunnel at establishment SHALL be fixed for that tunnel's lifetime; the contract SHALL define no means of rebinding it on an established tunnel, so a credential changeover takes effect at the next establishment rather than mid-tunnel.

#### Scenario: A silent peer does not hold a connection

- **WHEN** a peer opens a connection and sends no declaration
- **THEN** the tunnel is failed once the declaration bound elapses
- **AND** the cause is distinguishable from version incompatibility

#### Scenario: A frame before the declaration fails the tunnel

- **WHEN** a peer sends a request head before any declaration
- **THEN** the tunnel is failed as a protocol violation
- **AND** no exchange is created

#### Scenario: An oversized declaration is refused before it is recorded

- **WHEN** a declaration carries capability names beyond the bound on their count or length
- **THEN** the tunnel is refused
- **AND** the individual unrecognised names are not retained or recorded

#### Scenario: A declaration cannot be repeated

- **WHEN** a peer sends a second establishment declaration on an established tunnel
- **THEN** it is a tunnel protocol violation
- **AND** the values negotiated at establishment continue to govern

### Requirement: Connection parameters are declared at establishment

Each side SHALL declare, in its tunnel establishment declaration: the largest frame payload it will accept, the greatest number of exchanges it will serve concurrently on that connection, the initial per-stream and whole-tunnel credit it grants, and the greatest header section and trailer section size it will accept. Each parameter SHALL lie between a floor and a ceiling the contract fixes for every version, and the floor SHALL be sufficient to carry a request head and one body frame.

A side that omits a parameter SHALL be treated as declaring the contract's stated minimum for it. A declaration stating a parameter below the contract's floor SHALL be refused with a cause naming that parameter. The value in force in each direction SHALL be the value the receiving side declared, and a sender SHALL NOT emit a frame or a section exceeding it.

Declared parameters SHALL be fixed for the life of the tunnel connection; a side that needs to reduce its load SHALL drain rather than restate a parameter. Every declared parameter SHALL be readable by an operator on an established tunnel, and SHALL be settable in a deployment so that boundary behaviour can be exercised without transferring a large volume.

#### Scenario: Declared frame size is enforced at the boundary

- **WHEN** a peer declares a largest acceptable frame payload and its counterpart emits a frame one octet larger
- **THEN** the receiver reports a tunnel protocol violation naming the exceeded frame size
- **AND** it does not attempt to deliver that frame's payload
- **AND** a frame of exactly the declared size is accepted and carried

#### Scenario: A parameter can be lowered to reach a bound

- **WHEN** an implementation is deployed with a small declared frame payload and a small declared header section size
- **THEN** those are the values it declares at establishment
- **AND** the boundary behaviour can be exercised without transferring a large volume

#### Scenario: Omitted parameter falls back to the stated minimum

- **WHEN** a peer's declaration omits a parameter the contract defines
- **THEN** the counterpart applies the contract's stated minimum for it
- **AND** the tunnel is established rather than refused

#### Scenario: A parameter below the contract floor is refused

- **WHEN** a declaration states a maximum frame payload too small to carry a request head
- **THEN** the tunnel is refused with a cause naming that parameter

#### Scenario: Parameters are observable

- **WHEN** an operator inspects an established tunnel
- **THEN** every parameter each side declared is reported

### Requirement: Capability declaration

The contract SHALL distinguish baseline behaviours, which every implementation of a contract version supports, from optional capabilities, whose availability is declared. Both SHALL be named by stable identifiers published as part of the contract at each version rather than by prose descriptions. A published name SHALL NOT be removed or repurposed; a name MAY be added at any version; and every other capability that names a capability SHALL name it by its published identifier.

Each side SHALL declare a capability set when establishing a tunnel, covering at minimum: opaque octet bodies, ordered repeated header fields, response streaming, request streaming, trailer sections, interim responses, cancellation, flow control, frame-level bidirectional streams, and datagrams. At version 1 the baseline SHALL be: opaque octet bodies, ordered repeated header fields, and cancellation. Framing, stream identifiers, per-stream ordering, credit accounting, and enumerated errors are properties of the encoding rather than declarable capabilities, and are therefore required of every implementation without being declared. Every other name in the list above SHALL be optional at version 1. A declaration marking a baseline behaviour as unsupported SHALL be refused with an enumerated code naming the behaviour, distinct from a refusal for an unsupported optional capability, and the tunnel SHALL NOT be established.

A capability absent from a declaration SHALL be treated as unsupported by that side, and a feature requiring both sides SHALL be available on a tunnel only where both declared it. A declared capability set SHALL be fixed for the life of the tunnel connection. Each side SHALL record its peer's declared set against the established tunnel, and the proxy SHALL make both sets retrievable for every connected sidecar.

A declaration SHALL carry an optional build provenance for the declaring implementation. Where it is absent the receiver SHALL record the provenance as unreported and SHALL still establish the tunnel; where it is present and states that the provenance is unknown, the receiver SHALL record that distinctly.

#### Scenario: Capabilities recorded at join

- **WHEN** a sidecar establishes a tunnel declaring support for response streaming but not trailer sections
- **THEN** the proxy records response streaming as available and trailer sections as unavailable for that sidecar
- **AND** the declared capability set of both sides is retrievable for every connected sidecar

#### Scenario: Unknown capability names are ignored, not fatal

- **WHEN** a sidecar declares a capability name the proxy does not recognise, within the bound on name count and length
- **THEN** the tunnel is established
- **AND** the unrecognised name is ignored for routing decisions
- **AND** the unrecognised name is recorded for diagnostics

#### Scenario: A baseline behaviour cannot be declined

- **WHEN** a sidecar declares opaque octet bodies as unsupported
- **THEN** the tunnel is refused with a code naming that behaviour as baseline
- **AND** the refusal is distinct from a refusal for an unsupported optional capability

#### Scenario: A sidecar learns what the proxy can honour

- **WHEN** a sidecar newer than the proxy establishes a tunnel
- **THEN** it receives the proxy's declared capability set
- **AND** it does not have to discover an unsupported capability by attempting it

#### Scenario: A feature needing both sides is unavailable when one declines it

- **WHEN** a sidecar declares datagram support and the proxy does not
- **THEN** the tunnel is established
- **AND** the datagram capability is reported as unavailable on that tunnel
- **AND** an exchange requiring it is refused with the capability named

#### Scenario: Capability names are one published vocabulary

- **WHEN** an exchange is refused for a missing capability
- **THEN** the name in the refusal, the name recorded at the edge, and the name in the measurement of that refusal are the same published identifier

#### Scenario: Build provenance is optional but distinguishable

- **WHEN** one sidecar establishes a tunnel carrying no provenance and another carries provenance stated as unknown
- **THEN** both tunnels are established
- **AND** the first is recorded as unreported and the second as self-reported unknown
- **AND** the two are distinguishable

### Requirement: Refusal rather than silent degradation

The set of capabilities an exchange requires SHALL be derivable from the request head and the matched route's declared class alone, before the exchange is dispatched. An implementation SHALL either serve an exchange at full fidelity or refuse it with an enumerated code naming each missing capability. No implementation SHALL serve an exchange at reduced fidelity, and none SHALL substitute a partial behaviour for a declared-and-absent one.

The contract SHALL NOT allow the effective fidelity of an exchange to depend on which sidecar was selected. Which of a mount's connected sidecars an exchange is directed to, and the rule by which eligible sidecars are filtered by capability before one is chosen, are owned by the sidecar registry rather than by the contract.

A capability need that becomes apparent only after dispatch SHALL cause the discovering side to reset the stream with an enumerated code naming the capability, and SHALL NOT be served at reduced fidelity or by silently discarding the part that cannot be carried.

#### Scenario: The required capability set is fixed before dispatch

- **WHEN** two requests identical in head and matched route arrive
- **THEN** the set of capabilities each is determined to require is identical
- **AND** each set is determined before any sidecar is selected

#### Scenario: Refusal names the missing capability

- **WHEN** an exchange is refused because no capable counterpart exists for it
- **THEN** the refusal carries an enumerated code naming each missing capability
- **AND** the exchange is not carried over the tunnel at reduced fidelity

#### Scenario: Capability need discovered after dispatch

- **WHEN** a backend emits a trailer section to a sidecar that declared no trailer support
- **THEN** the sidecar resets the stream with a code naming the trailer capability
- **AND** the trailer fields are not merged into the response header section
- **AND** the client observes a truncated response rather than one whose trailers were silently dropped

#### Scenario: Capability loss on reconnect

- **WHEN** a sidecar reconnects declaring fewer capabilities than before
- **THEN** exchanges admitted after the reconnection are evaluated against the newly declared set
- **AND** exchanges requiring a withdrawn capability are refused rather than failing mid-exchange
- **AND** exchanges already in flight on the earlier tunnel are unaffected

### Requirement: A requirement describing an optional capability binds only where it is declared

Several requirements of this contract describe the behaviour of an optional capability — incremental transfer in each direction, trailer sections, interim responses, credit-based backpressure, frame-level bidirectional streams, and datagrams. Each such requirement SHALL bind an implementation only on a tunnel where the corresponding capability was declared by the side the requirement obliges. Where it was not declared, the absence SHALL be resolved by the refusal rule rather than by the requirement being weakened, partially met, or met in a degraded form.

Every normative requirement of this contract SHALL state, in one place per contract version, whether it is baseline or scoped to a named capability, so that no requirement's applicability is a matter of inference. A requirement not so marked SHALL be baseline.

An implementation that has not declared an optional capability SHALL NOT be treated as violating the requirement that describes it, and SHALL NOT be permitted to serve an exchange requiring it. A capability-scoped requirement SHALL NOT be satisfiable by an implementation that declares the capability and then behaves as though it had not.

#### Scenario: An undeclared capability is a refusal, not a violation

- **WHEN** an exchange requiring an optional capability is matched to a tunnel on which that capability was not declared
- **THEN** the exchange is refused with the capability named
- **AND** the counterpart is not reported as violating the requirement that describes that capability

#### Scenario: A declared capability is fully binding

- **WHEN** a side declares an optional capability
- **THEN** every requirement of this contract scoped to that capability binds it in full on that tunnel
- **AND** partial or degraded conformance to that requirement is a violation rather than an absence

#### Scenario: Applicability is published, not inferred

- **WHEN** the contract is published at a version
- **THEN** each of its normative requirements is marked baseline or scoped to a named published capability
- **AND** no requirement's applicability has to be inferred from its wording

### Requirement: The contract defines two roles, and a client-edge speaker occupies one of them

The contract SHALL define exactly two roles for the two ends of a tunnel connection: the **client-facing role**, held by the side an exchange originates at, and the **origin-facing role**, held by the side that originates the exchange against a backend. Every obligation this contract places on "the proxy" SHALL bind whichever component holds the client-facing role on that connection, and every obligation it places on "the sidecar" SHALL bind whichever component holds the origin-facing role. The disjoint stream-identifier allocation sets, the direction consistency rule, and the enumeration of which side may open which frame kind SHALL be stated against the roles rather than against the components, so that a component substituted at either end inherits the same obligations.

Because the edge protocols served to clients are terminated by a component that may be separate from the one holding the origin-facing tunnel — a decision recorded in `design.md` D16 — a component terminating a client-facing protocol on the platform's behalf SHALL speak this contract in the client-facing role toward the component that holds the origin-facing tunnel, over its own connection, with the same version negotiation, the same establishment declaration, the same parameter and capability declaration, the same enumerated errors, and the same refusal-rather-than-degradation rule. It SHALL NOT be reached by the framing the tunnel listener serves to a dialling sidecar, SHALL NOT present a sidecar credential, SHALL NOT be admitted for a mount, and SHALL NOT become a registry entry eligible to serve one; a connection from such a component SHALL be counted, bounded, and attributed separately from both a sidecar tunnel and a client connection.

The facts a client-facing speaker establishes from the client connection — the observed client source, the scheme, the authority established for the connection, the negotiated edge protocol, and the correlation identifier assigned to the exchange — SHALL travel to its counterpart as fields of this contract, and SHALL NOT be re-derived by the counterpart from anything a client supplied. A counterpart SHALL treat such a field as established only where it arrived from a client-facing speaker it authenticated, and SHALL refuse the exchange rather than adopt a value that arrived any other way.

Version skew between the platform's own components is bounded, because the operator deploys both; skew toward a sidecar is not. The contract SHALL NOT therefore relax any additivity or negotiation rule for a client-facing speaker, because the same encoding, the same enumeration, and the same negotiation serve both, and a second relaxed profile would be a second contract.

#### Scenario: Obligations follow the role, not the component

- **WHEN** the client-facing role is held by a component separate from the one serving mount lookup
- **THEN** every obligation this contract states for the originating side binds that component
- **AND** its stream identifiers are drawn from the client-facing allocation set
- **AND** a frame whose direction is inconsistent with that role is a tunnel protocol violation as it would be for any other holder of it

#### Scenario: A client-edge speaker is not a sidecar

- **WHEN** a component terminating a client-facing protocol establishes its contract connection
- **THEN** it presents no sidecar credential and is admitted for no mount
- **AND** no registry entry eligible to serve a mount is created for it
- **AND** its connection is counted separately from sidecar tunnels and from client connections

#### Scenario: Established facts cross as contract fields

- **WHEN** an exchange arrives from an authenticated client-facing speaker
- **THEN** the observed client source, scheme, established authority, negotiated edge protocol, and correlation identifier are read from the contract fields that speaker set
- **AND** none of them is re-derived from a value the client supplied

#### Scenario: The same fields arriving from a client are refused

- **WHEN** a client supplies values resembling the established client source, the established authority, or the correlation identifier
- **THEN** none of them is adopted as an established fact
- **AND** the exchange is served with the values the edge established, or refused

#### Scenario: One negotiation serves both counterparts

- **WHEN** a client-facing speaker and a sidecar each establish a connection declaring version ranges and capability sets
- **THEN** both are negotiated by the same rules and refused by the same rules
- **AND** no additivity, negotiation, or encoding rule is relaxed for either

### Requirement: Method tokens are carried unmodified

The contract SHALL represent an HTTP method as an opaque, case-sensitive token. Neither side SHALL restrict methods to an allowlist, rewrite a method, or fold one method into another. The contract SHALL NOT define a method it refuses to carry; where a proxy refuses a method at its edge that refusal is edge policy, and no tunnel frame SHALL be generated for it.

A method token SHALL be a non-empty sequence of the octets HTTP permits in a token and SHALL be bounded in length by configuration. This is a grammar check, not an allowlist, and its refusal SHALL be distinguishable from a refusal for an unrecognised or disallowed method. A side receiving a token that is empty, exceeds the bound, or contains any other octet SHALL refuse the exchange with an enumerated code for a malformed method and SHALL NOT issue a request to a backend for it.

#### Scenario: Extension method reaches the backend

- **WHEN** a client issues a `PROPFIND` request to a mounted path
- **THEN** the sidecar issues `PROPFIND` to the backend
- **AND** the method is byte-identical to the method received at the edge

#### Scenario: Unregistered method reaches the backend

- **WHEN** a client issues a request whose method token the contract has never seen and which contains only octets HTTP permits in a token
- **THEN** the request is carried and the backend receives that exact token

#### Scenario: Case is not normalised

- **WHEN** a client issues a request whose method token is lowercase
- **THEN** the backend receives that token in lowercase
- **AND** it is neither upcased nor refused for its case

#### Scenario: HEAD is not folded into GET

- **WHEN** a client issues a `HEAD` request to a resource whose backend answers with a non-zero stated content length and no body
- **THEN** the sidecar issues `HEAD` to the backend
- **AND** the client receives the backend's stated length with no body octets
- **AND** the proxy does not issue a `GET` and does not discard a body it fetched

#### Scenario: A method token containing a forbidden octet is not carried

- **WHEN** a client sends a request whose method token contains a space or a line terminator
- **THEN** the request is refused with a code naming a malformed method
- **AND** no tunnel frame is generated for it
- **AND** the backend observes no request
- **AND** the refusal is distinguishable from a method being unrecognised

### Requirement: Header fields are an ordered sequence of pairs

The contract SHALL represent header fields as an ordered sequence of name and value pairs in both directions. It SHALL NOT represent them as a mapping from name to a single value.

Repeated field names SHALL be preserved as separate entries. The relative order of entries sharing a name SHALL be preserved. The received case of field names SHALL be carried. Carrying the received case SHALL NOT be read as licence to emit a name a hop's protocol defines as malformed: where a side re-emits a field on a hop whose protocol requires lowercase field names, it SHALL lowercase on emission.

A field name SHALL be a non-empty sequence of the octets HTTP permits in a field name, and a field value SHALL NOT contain a carriage return, line feed, or null octet. A side receiving a field violating either rule SHALL reset the stream with an enumerated code and SHALL NOT re-emit that field on any hop. The header section SHALL be bounded in total size and in field count by the parameters the receiving side declared, enforced as the section is received, with a code distinguishing the section bound from the frame bound.

The carried header sequence SHALL contain only fields that are properties of the message. A field that describes how a message is delimited on a connection, or that governs the behaviour of a single connection — at minimum a content-length field, a transfer-encoding field, a connection field, and every field a connection field names — SHALL NOT appear in it in either direction. Each side SHALL remove these from what it places on the tunnel and SHALL generate its own on the hop it emits. A receiver finding one in a carried header section SHALL discard it, record it, and SHALL NOT use it to frame anything.

#### Scenario: Multiple Set-Cookie fields survive

- **WHEN** a backend responds with three separate `Set-Cookie` fields
- **THEN** the client receives three separate `Set-Cookie` fields
- **AND** their values are unaltered
- **AND** their relative order is unchanged

#### Scenario: Order within a repeated name is preserved

- **WHEN** a backend emits two `Link` fields in a specific order
- **THEN** the client receives them in that same order

#### Scenario: Repeated request fields survive

- **WHEN** a client sends two `Accept-Encoding` fields
- **THEN** the backend receives two `Accept-Encoding` fields

#### Scenario: Field case is carried

- **WHEN** a client sends a field named `X-Custom-Header`
- **THEN** the received case is available to the sidecar
- **AND** the backend is not required to match a lowercased name

#### Scenario: Carried case is lowercased only where the hop demands it

- **WHEN** a field named with mixed case is carried and the sidecar re-emits it to a backend over a protocol that defines uppercase field names as malformed
- **THEN** the emitted name is lowercased
- **AND** the case as received is still what the sidecar was given over the tunnel

#### Scenario: A value containing a line break is refused

- **WHEN** a header field value contains a carriage return or line feed
- **THEN** the stream is reset with an enumerated code
- **AND** no field derived from it reaches the backend

#### Scenario: Backend framing fields do not enter the tunnel

- **WHEN** a backend responds with a content-length field and a connection field naming a further field
- **THEN** none of those fields appears among the header pairs carried over the tunnel
- **AND** the receiving side determines the extent of the body from the body-completion frame rather than from any carried field
- **AND** the body octets delivered to the client are byte-identical to the backend's

#### Scenario: A header section beyond the declared bound is refused

- **WHEN** a header section exceeds the size or the field count the receiving side declared
- **THEN** the exchange is refused with a code naming the header section bound, distinct from the frame size bound
- **AND** memory held for that message does not grow past the declared bound
- **AND** the tunnel remains established

### Requirement: Bodies are opaque octet streams

The contract SHALL represent request and response bodies as opaque sequences of octets. No side SHALL apply character-set validation, transcoding, replacement of invalid sequences, or any other transformation to a body it is carrying.

A body SHALL be representable across multiple frames, and the octets of a body SHALL be identical at both ends regardless of how the body was divided. A message with a zero-length body and a message with no body SHALL be distinguishable on the wire and SHALL remain distinguishable at both ends. A body data frame carrying no octets SHALL be permitted and SHALL NOT be read as body completion.

Where the contract states an octet count for a body, that count SHALL be the number of payload octets carried after any encoding the contract itself applies has been removed. No side SHALL state a count derived from a transformed form of the body.

#### Scenario: Arbitrary octets survive intact

- **WHEN** a backend responds with a body containing octets that are not valid UTF-8, including a lone `0x80`
- **THEN** the client receives a byte-identical body

#### Scenario: Division into frames does not alter content

- **WHEN** a body is carried in several frames and a multi-octet character sequence spans a frame boundary
- **THEN** the reassembled body is byte-identical to the original
- **AND** no replacement character is introduced

#### Scenario: Request bodies survive intact

- **WHEN** a client sends a request body of arbitrary octets
- **THEN** the backend receives a byte-identical body

#### Scenario: Empty body is not absent body

- **WHEN** a backend responds with a zero-length body
- **THEN** the client receives a response with a zero-length body
- **AND** it is distinguishable at every hop from a response defined to carry no body

#### Scenario: A single body frame is carried as a body

- **WHEN** a body is small enough to fit in one frame
- **THEN** it is delivered in full
- **AND** the outcome is identical in content to the same body split across several frames

#### Scenario: A zero-length body frame is not completion

- **WHEN** a body data frame carries no octets and further body data frames follow
- **THEN** the later octets are delivered
- **AND** the body is not treated as complete at the empty frame

#### Scenario: Declared counts survive an expanding encoding

- **WHEN** a body is carried under an encoding whose octet count on the wire exceeds the body's own
- **THEN** the count the receiving side is given is the body's octet count, not the encoded count
- **AND** the delivered body is byte-identical to the original

### Requirement: Request targets are carried in raw form

The contract SHALL carry the request target as a closed set of components fixed per contract version. At version 1 the set SHALL be: a target form indicator distinguishing origin form, absolute form, authority form and asterisk form; scheme; authority; path; query; and the upgrade protocol name used by extended `CONNECT`, distinct from the method. A fragment SHALL NOT be carried. Each component SHALL be distinguishable when absent from when present and empty, and SHALL be bounded in length by configuration; a target exceeding a bound SHALL be refused with an enumerated code rather than truncated, and a component containing a control octet, a line break, or a null octet SHALL be refused.

The path component SHALL be the mount remainder the routing capability computed — the received path with the matched mount prefix removed and nothing else changed. No component SHALL be normalised, and percent-encoded octets within a path segment SHALL be preserved rather than decoded or treated as separators.

The scheme and authority components SHALL be the values the edge established for the client's connection, SHALL be carried for the backend's information only, and SHALL NOT be used by any implementation to select a connection destination. A sidecar SHALL derive the origin it connects to solely from configuration it holds locally, and SHALL reset the stream with an enumerated code rather than connect to a destination named by a carried component.

#### Scenario: Encoded separator in a path segment is preserved

- **WHEN** a client requests a path containing `%2F` inside a segment
- **THEN** the sidecar receives that segment with `%2F` intact
- **AND** the segment is not split at that position

#### Scenario: Trailing slash is preserved

- **WHEN** a client requests a path with a trailing slash
- **THEN** the backend receives a path with the trailing slash

#### Scenario: Query string is carried verbatim

- **WHEN** a client sends a query string containing repeated keys and encoded characters
- **THEN** the backend receives that query string unaltered

#### Scenario: Empty query is distinguishable from absent query

- **WHEN** one client requests a path followed by `?` with no query characters and another requests the same path with no `?`
- **THEN** the sidecar distinguishes the two
- **AND** the backend receives each target in the form its client sent

#### Scenario: Asterisk-form target is representable

- **WHEN** a client issues `OPTIONS *`
- **THEN** the sidecar receives the asterisk target form
- **AND** it is distinguishable from a request whose path is a single `*` character

#### Scenario: Upgrade protocol name is carried beside the method

- **WHEN** a client issues an extended `CONNECT` naming an upgrade protocol
- **THEN** the sidecar receives the protocol name in the target's protocol component
- **AND** the method token is unchanged
- **AND** the protocol name is not derived from, or present in, the method

#### Scenario: The carried authority never selects a destination

- **WHEN** a request head arrives carrying an authority naming a host the sidecar is not configured for
- **THEN** the sidecar opens no connection to that host
- **AND** the stream is reset with an enumerated code
- **AND** the origin the sidecar would otherwise connect to is unchanged

#### Scenario: A control octet in a target is refused

- **WHEN** a request target component contains a control octet or a line break
- **THEN** the exchange is refused with an enumerated code
- **AND** nothing derived from it reaches the backend

### Requirement: Each exchange names the mount it was matched to

A tunnel SHALL be admitted for exactly one mount, fixed at establishment by the credential that authenticated it. The contract SHALL NOT define a means of admitting a tunnel for a second mount, or of changing the mount an established tunnel serves; a sidecar serving more than one mount SHALL hold one tunnel per mount, each independently authenticated.

The request head SHALL nevertheless carry an identifier for the mount the exchange was matched to, so that the receiving implementation can check the proxy's routing against its own admission rather than trusting it. An implementation receiving a request head naming any mount other than the one it was admitted for SHALL reset that stream with an enumerated code, SHALL NOT issue any backend request for it, and SHALL NOT terminate the tunnel.

#### Scenario: A tunnel serves one mount

- **WHEN** a sidecar establishes a tunnel
- **THEN** exactly one mount is admitted for it
- **AND** the origin it issues requests against is the one configured for that mount

#### Scenario: Serving two mounts takes two tunnels

- **WHEN** a sidecar deployment serves two mounts of the same tenant
- **THEN** it holds one authenticated tunnel per mount
- **AND** the ending of one leaves the other serving

#### Scenario: A request head naming an unadmitted mount is reset

- **WHEN** a request head names a mount the sidecar was not admitted for
- **THEN** the stream is reset with an enumerated code
- **AND** no backend request is issued
- **AND** the tunnel remains established and other exchanges are unaffected

#### Scenario: The mount identifier is not derived from client input

- **WHEN** a client request carries a value resembling a mount identifier in a field, in its target, or in its body
- **THEN** the identifier carried on the request head is the one the proxy's routing determined
- **AND** it is not the client's value

### Requirement: Exchanges carry a correlation identifier distinct from the stream identifier

The request head SHALL carry a correlation identifier assigned by the proxy, opaque to the contract, and bounded in length. It SHALL be distinct from the stream identifier, because a stream identifier is scoped to one tunnel connection and says nothing after that connection ends.

A receiving implementation SHALL carry the correlation identifier unchanged into every signal it produces about that exchange and SHALL make it available for propagation to the backend. An implementation that does not recognise the field SHALL serve the exchange normally.

#### Scenario: One identifier joins both ends of an exchange

- **WHEN** an exchange is served over the tunnel
- **THEN** the records produced at each end for that exchange carry the same correlation identifier
- **AND** it is not the stream identifier the tunnel assigned

#### Scenario: Concurrent exchanges carry distinct identifiers

- **WHEN** many exchanges are in flight concurrently on one tunnel
- **THEN** each carries a distinct correlation identifier

#### Scenario: An older counterpart still serves the exchange

- **WHEN** a counterpart that does not recognise the correlation identifier receives a request head carrying one
- **THEN** it serves the exchange normally
- **AND** it does not refuse or reset the exchange on account of the field

### Requirement: Requests carry an affinity key

The contract SHALL carry an optional affinity key on a request as an opaque octet string, bounded in length by configuration, distinguishable when absent from when present and zero-length. A request whose key exceeds the bound SHALL be refused with an enumerated code rather than truncated.

The key SHALL be derived by the proxy from the request under a policy configured on the matched mount, SHALL be carried unaltered, and SHALL NOT be invented or reinterpreted by a sidecar. Where the matched mount declares no affinity policy, no key SHALL be carried; the absence of a policy SHALL NOT be resolved by deriving a key from a default set of request fields, because a key nothing consumes still binds a session to one counterpart and defeats spreading. It SHALL NOT identify a sidecar, a tunnel, a proxy instance, or a tenant, and no value carried on a request SHALL be capable of naming the counterpart an exchange reaches.

What a key binds to, the scope and lifetime of that binding, its expiry, its interaction with capability filtering and drain, and the observability of its loss are owned by the sidecar registry, not by the contract.

#### Scenario: The key is proxy-derived and names no counterpart

- **WHEN** a client sends a request containing a value it intends as an affinity key
- **THEN** the key carried over the tunnel is the one the mount's policy derives
- **AND** it names no sidecar, tunnel, proxy instance, or tenant
- **AND** no value the client supplied determines which counterpart the exchange reaches

#### Scenario: Identical requests derive identical keys

- **WHEN** two requests identical in the fields the mount's policy reads arrive at that mount
- **THEN** the affinity key carried for each is byte-identical

#### Scenario: A mount with no affinity policy carries no key

- **WHEN** a request is matched to a mount that declares no affinity policy
- **THEN** the request head carries no affinity key
- **AND** no key is derived from a default set of request fields

#### Scenario: Absent key is distinguishable from a zero-length key

- **WHEN** one request carries no affinity key and another carries a zero-length one
- **THEN** the sidecar distinguishes the two

#### Scenario: An oversized key is refused, not truncated

- **WHEN** a request would carry an affinity key longer than the configured bound
- **THEN** the request is refused with an enumerated code
- **AND** no truncated key is carried

### Requirement: Framed exchange with stream identifiers

The unit of transfer on the tunnel SHALL be a frame carrying a stream identifier, not a message carrying a whole request or response. Multiple frames SHALL be permitted per exchange in each direction. An exchange is the work carried on one stream.

Every frame SHALL begin with a fixed-shape header carrying the frame kind, the stream identifier, and the length of the remainder of the frame, laid out so that a receiver that does not recognise the kind can still read all three and advance to the next frame boundary. A frame that is not scoped to a single exchange SHALL carry the reserved tunnel-scoped stream identifier rather than an exchange's identifier.

The contract SHALL define, at version 1, stream-scoped frame kinds for: a request head, body data, body completion including an optional trailer section, an interim response, a response head, a stream reset carrying an application error code, a flow-control credit update, and a datagram. It SHALL further define, at version 1, tunnel-scoped frame kinds for: an establishment declaration and its acceptance or refusal; a flow-control credit update for the tunnel as a whole; a liveness probe and its answer; a drain notice; and a tunnel close carrying an enumerated reason. Every defined frame kind SHALL be reserved at version 1 whether or not it is implemented at version 1.

Every message carried on a stream SHALL be terminated by exactly one body-completion frame, including a message with no body octets. A receiver SHALL treat that frame as the sole indication that a message has ended, SHALL NOT infer completion from any stated length, and SHALL NOT wait for octets after it.

A receiver encountering a frame kind it does not recognise SHALL skip the frame using its declared length, record it, and SHALL NOT terminate the tunnel. A receiver encountering a recognised but unimplemented kind SHALL, where the kind is stream-scoped, reset that stream with an enumerated code naming the kind; where the kind is tunnel-scoped, ignore it, record it, and continue serving; and where it is a datagram, discard it and record it. In none of these cases SHALL the tunnel be terminated or an unrelated stream reset.

#### Scenario: One exchange spans many frames

- **WHEN** a request with a body is carried
- **THEN** the exchange consists of a request head frame followed by one or more body data frames and a body completion frame
- **AND** all frames of that exchange carry the same stream identifier

#### Scenario: Unrecognised frame kind is skipped, not fatal

- **WHEN** a peer sends a frame whose kind the receiver has never been told about, followed by a frame of a kind it implements
- **THEN** the receiver advances past the unrecognised frame using its declared length
- **AND** the following frame is processed normally
- **AND** the unrecognised kind is recorded
- **AND** the tunnel is not terminated

#### Scenario: Reserved but unimplemented datagram frame

- **WHEN** a sidecar at contract version 1 receives a datagram frame it does not implement
- **THEN** it discards the datagram and records it
- **AND** the tunnel remains established
- **AND** no stream is reset by that fact alone

#### Scenario: An unimplemented stream-scoped kind resets one stream

- **WHEN** a peer sends a recognised but unimplemented stream-scoped frame kind
- **THEN** the receiver resets that stream with a code naming the unimplemented kind
- **AND** other in-flight exchanges are unaffected

#### Scenario: A message with no body still ends explicitly

- **WHEN** a response head states a representation length and the sender emits a body-completion frame with no body data frames
- **THEN** the receiver completes the exchange immediately
- **AND** it does not wait for the stated number of octets

### Requirement: Stream identifiers are allocated, scoped and never reused

A stream identifier SHALL be scoped to one tunnel connection. Identifiers the proxy allocates and identifiers the sidecar allocates SHALL be drawn from disjoint sets distinguished by a property of the identifier itself, so that both sides may open exchanges concurrently without collision. Each side SHALL allocate strictly increasing identifiers within a connection and SHALL NOT reuse one for the life of that connection. Exhaustion of a side's identifier space SHALL be handled by draining the connection, never by wrapping.

A frame bearing an identifier the receiver has already released, or an identifier for a stream that has ended, SHALL be discarded and recorded, SHALL NOT be delivered to any exchange, SHALL NOT recreate the stream, and SHALL NOT terminate the tunnel. A frame naming an identifier that has never been opened, other than the frame kind that opens a stream, SHALL reset that identifier's stream without creating it.

A stream-opening frame bearing an identifier already carrying an in-flight exchange, an opening frame bearing an identifier from the receiver's own allocation set, and a frame whose direction is inconsistent with the role of the side that sent it, SHALL each be a tunnel protocol violation with a cause naming stream-identifier misuse.

#### Scenario: Both sides open exchanges concurrently without collision

- **WHEN** the proxy and the sidecar each open a new exchange at the same instant on one tunnel connection
- **THEN** the two exchanges carry different stream identifiers
- **AND** each side can tell from the identifier alone which side allocated it

#### Scenario: A completed identifier is never reused

- **WHEN** an exchange completes and further exchanges are opened on the same connection
- **THEN** every new exchange carries an identifier greater than every identifier used on that connection
- **AND** a frame bearing the completed exchange's identifier is discarded and recorded rather than delivered
- **AND** retained state does not grow as such frames accumulate

#### Scenario: Body data for an unopened stream creates nothing

- **WHEN** a body data frame names an identifier for which no stream-opening frame was received
- **THEN** that stream is reset
- **AND** no exchange is created and no octets are retained

#### Scenario: A duplicate stream-opening frame fails the tunnel

- **WHEN** a second request head arrives bearing an identifier already carrying an in-flight exchange
- **THEN** the tunnel is failed with a cause naming stream-identifier misuse
- **AND** the in-flight exchange is not replaced

#### Scenario: Exhaustion ends the connection rather than wrapping

- **WHEN** a side's identifier space is exhausted
- **THEN** it sends a drain notice
- **AND** it does not reuse a previously allocated identifier

### Requirement: Malformed framing is tunnel-fatal and unusable frames are stream-fatal

The contract SHALL classify every rejection as stream-fatal or tunnel-fatal, and the classification SHALL be part of the contract rather than an implementation choice, so that two implementations do not disagree on whether a given input costs one exchange or the whole tunnel.

A frame that is well formed at the framing layer but cannot be acted on SHALL be stream-fatal: the stream is reset with an enumerated code and the tunnel continues. A frame whose framing itself cannot be trusted — a declared length that does not match the octets present, a truncated frame, an undecodable payload, a nested length overrunning its frame, or content remaining after the declared length — SHALL be tunnel-fatal with an enumerated protocol-violation code, and the tunnel SHALL NOT be continued by resynchronising or skipping octets.

A receiver SHALL NOT reserve memory proportional to a declared length before the corresponding octets have arrived. Every frame a side refuses, discards, or resets SHALL be recorded and attributable to its enumerated cause, distinctly enough that a discard is distinguishable from a delivery, and a rejection that terminates the tunnel SHALL be recorded before the tunnel closes.

#### Scenario: A frame's declared length must match its payload

- **WHEN** a frame declares a payload length differing from the number of payload octets it carries
- **THEN** the receiver fails the tunnel with a protocol violation naming the length mismatch
- **AND** it does not attempt to resynchronise by scanning for the next frame

#### Scenario: An enormous declared length allocates nothing

- **WHEN** a frame declares a length far exceeding the peer's declared maximum frame payload
- **THEN** the tunnel is failed before any memory proportional to that length is reserved

#### Scenario: Undecodable payload does not become a stream reset

- **WHEN** a frame of a known kind carries a payload that cannot be decoded
- **THEN** the tunnel is failed as a protocol violation
- **AND** the outcome is distinguishable from the reset produced by an unimplemented frame kind

#### Scenario: Causes are not conflated

- **WHEN** one frame is refused for exceeding a declared parameter and another for naming a terminated stream
- **THEN** the two increment different recorded causes
- **AND** neither increments a count of delivered frames

#### Scenario: A tunnel-fatal rejection is recorded before the close

- **WHEN** a malformed frame fails the tunnel
- **THEN** the cause is recorded and remains readable after the tunnel has closed

### Requirement: Liveness is a contract-level exchange

The contract SHALL define a liveness probe frame and a matching answer frame, each carrying an opaque token the answer echoes. Either side MAY probe at any time. The answer SHALL be produced by the layer that implements the contract, never by a transport, a library, or an intermediary below it, so that a peer whose connection is open but whose contract logic has stopped fails liveness.

A probe SHALL be answered within a declared bound. Probe and answer frames SHALL NOT consume stream or tunnel credit and SHALL be deliverable while every stream is credit-starved. Each side SHALL bound the number of probes it leaves outstanding and SHALL decline to answer beyond that bound rather than queueing.

#### Scenario: Probe is answered under saturation

- **WHEN** every stream on the tunnel has exhausted its credit and body frames are queued
- **THEN** a liveness probe is answered within the declared bound
- **AND** the tunnel is not torn down for a missed answer

#### Scenario: Echo binds the answer to the probe

- **WHEN** two probes are outstanding with different tokens
- **THEN** each answer carries the token of the probe it answers
- **AND** an answer bearing an unissued token is discarded and recorded

#### Scenario: A frozen peer fails liveness while its connection stays open

- **WHEN** a peer's connection remains open but its contract layer stops processing
- **THEN** its probes go unanswered
- **AND** the tunnel is treated as not alive within the declared bound

#### Scenario: Probe flooding is bounded

- **WHEN** a peer sends probes faster than the outstanding bound allows
- **THEN** probes beyond the bound are not answered and are recorded
- **AND** memory held for outstanding probes remains within the bound

### Requirement: Withdrawal and closure are announced with an enumerated reason

The contract SHALL define a drain notice, sendable by either side, carrying an enumerated reason and the highest stream identifier the sender will still serve. After sending or receiving it, a side SHALL NOT open a new exchange, SHALL carry every exchange at or below the stated identifier to completion, and SHALL reset any exchange above it with a code identifying that it was never served. A drain notice SHALL NOT by itself reset any exchange already in flight.

The contract SHALL define a tunnel close carrying an enumerated reason that distinguishes at minimum: planned withdrawal, a credential no longer valid, liveness failure, version incompatibility, a protocol violation, and an unspecified failure. A peer receiving a credential-no-longer-valid reason SHALL NOT reconnect with the same credential. Losing the underlying connection with no preceding notice or close SHALL be distinguishable, at the surviving end, from an announced ending.

Each side SHALL bound, by configuration, the rate at which a peer may open exchanges that are reset before completion, and SHALL answer a peer exceeding it with a drain notice carrying an enumerated code naming the exceeded bound.

#### Scenario: Announced drain lets in-flight work finish

- **WHEN** a sidecar sends a drain notice naming the highest stream identifier it will still serve while exchanges are in flight
- **THEN** those exchanges complete normally over the same tunnel
- **AND** an exchange opened above that identifier is reset with a code identifying that it was never served
- **AND** no exchange is reset by the arrival of the notice alone

#### Scenario: An unannounced close is distinguishable

- **WHEN** the connection is lost with no drain notice and no tunnel close
- **THEN** the surviving side records an unannounced loss
- **AND** it does not report the outcome as a completed drain

#### Scenario: A revoked credential does not prompt a retry with itself

- **WHEN** a tunnel is closed with the reason naming a credential no longer valid
- **THEN** the sidecar does not re-establish with that credential
- **AND** the reason is distinguishable from a transport failure and from planned withdrawal

#### Scenario: Open-and-reset flooding is bounded

- **WHEN** a peer opens and immediately resets exchanges at a rate above the configured bound
- **THEN** the receiving side sends a drain notice naming the exceeded bound
- **AND** exchanges already in flight are allowed to complete

### Requirement: Each direction of an exchange closes independently

An exchange SHALL consist of two independently closing directions. A direction closes when its body-completion frame is sent, or when the exchange is reset. An exchange terminates, and the state associated with it SHALL be released at both ends, when both directions have closed or when either side has reset it, whichever occurs first.

A final response head SHALL NOT by itself terminate an exchange whose response body has not completed. A side that has closed its own direction SHALL continue to accept frames on the other. A side that has received body completion on a direction SHALL treat any further message frame on that direction as stream-fatal.

An exchange in which one direction has closed and the other has produced nothing SHALL be governed by a configured bound, after which it is reset with a distinguishable code rather than retained.

#### Scenario: Response completes while the request body is still arriving

- **WHEN** a backend rejects a large upload and completes its response while the client is still sending
- **THEN** the response reaches the client in full
- **AND** the request direction is reset rather than left to run to completion
- **AND** state for the exchange is released once both directions have closed

#### Scenario: Request completes long before the response

- **WHEN** a request body completes and the response streams for an extended period
- **THEN** the exchange remains open
- **AND** it is not terminated by the request direction having closed

#### Scenario: A frame after body completion is stream-fatal

- **WHEN** a body data frame arrives on a direction that has already sent body completion
- **THEN** the stream is reset with an enumerated code
- **AND** the octets are not appended to the message

#### Scenario: A half-closed exchange does not accumulate

- **WHEN** many exchanges are left with one direction closed and the other producing nothing
- **THEN** each is reset once the configured bound elapses
- **AND** retained state does not grow with the number of such exchanges

### Requirement: Streams do not survive the connection that carried them

A stream SHALL be carried entirely on the tunnel connection on which it was opened, and a stream identifier SHALL have no meaning on any other connection. When a connection ends, every stream it carried SHALL be terminated at both ends. Where a sidecar holds more than one tunnel connection, each is an independent tunnel with its own stream-identifier space, and an exchange SHALL be assigned to exactly one of them for its whole lifetime.

The contract SHALL NOT define frame acknowledgement, retransmission, or stream resumption at version 1; introducing any of them SHALL be a contract version change gated by a capability. No side SHALL re-send a frame it has already sent, on any connection, and a side that has begun acting on a request head SHALL NOT act on it a second time as a consequence of a reconnection.

#### Scenario: A stream is not resumed on a new connection

- **WHEN** a tunnel connection is lost mid-exchange and a new connection is established
- **THEN** the exchange is not continued on the new connection
- **AND** a frame bearing the old identifier is discarded and recorded as a protocol violation
- **AND** the exchange is not retried by the contract

#### Scenario: A reconnect does not duplicate a backend call

- **WHEN** a request head has been delivered to a sidecar and the connection is lost before the response completes
- **AND** the sidecar re-establishes its tunnel
- **THEN** the backend has received that request exactly once
- **AND** the count is unchanged by the reconnection

#### Scenario: Loss of one connection does not disturb another

- **WHEN** a sidecar holds more than one tunnel connection and one is lost
- **THEN** only the streams that connection carried are terminated, with a cause naming the connection loss
- **AND** streams on the surviving connections continue without interruption

### Requirement: Interim responses precede exactly one final response

The contract SHALL permit zero or more interim responses on a stream before exactly one final response. An interim response SHALL carry a status in the informational class and a header section, and SHALL NOT carry a body or a trailer section. An implementation SHALL NOT treat an interim response as completing the exchange.

The number of interim responses on one stream SHALL be bounded by configuration; exceeding the bound SHALL reset the stream with an enumerated code naming it. A non-informational status delivered as an interim response, an interim response carrying a body or a trailer section, and an interim response delivered after the final response SHALL each be stream-fatal with an enumerated code.

The contract SHALL permit a request head to be carried before any of its body octets exist, so that a counterpart may confirm or reject an expectation before a body is transferred.

#### Scenario: Interim response then final response

- **WHEN** a backend emits an interim response followed by a final response
- **THEN** the client receives the interim response first
- **AND** then receives exactly one final response
- **AND** the exchange is complete only after the final response has completed

#### Scenario: The request head is transferable before any body exists

- **WHEN** a client indicates it expects confirmation before sending a request body
- **THEN** the request head crosses the tunnel before any body octets exist
- **AND** the exchange remains open awaiting either body frames or a reset

#### Scenario: Rejection stops the body transfer

- **WHEN** a client indicates it expects confirmation before sending a request body
- **AND** the counterpart rejects the expectation
- **THEN** the client receives the rejection
- **AND** no further request body octets are forwarded after it is delivered
- **AND** the stream is reset with a code naming the rejected expectation

#### Scenario: Interim responses are bounded

- **WHEN** a backend emits more interim responses on one stream than the configured bound
- **THEN** the stream is reset with a code naming the exceeded bound
- **AND** the interim responses already delivered to the client are not withdrawn
- **AND** other exchanges on the tunnel are unaffected

#### Scenario: An interim carrying a body is refused

- **WHEN** an interim response carries a body or a trailer section, or a status outside the informational class
- **THEN** the stream is reset with an enumerated code
- **AND** no part of it reaches the client

### Requirement: Trailer sections are distinct from header sections

The contract SHALL carry a trailer section as part of body completion, distinct from the header section, in both directions. A trailer section SHALL NOT be merged into the header section of the same message, and SHALL be bounded in size by the parameter the receiving side declared, enforced as it is received.

A trailer section SHALL NOT carry a field that frames the message, that authenticates or authorises it, that determines its routing, that governs its caching, or whose meaning depends on being read before the body. A receiver SHALL discard such a field from a trailer section, record it, and SHALL NOT merge it into the header section, act on it, or re-emit it on any hop.

A trailer section received on a message the contract defines as carrying none SHALL be stream-fatal.

#### Scenario: Response trailers reach the client

- **WHEN** a backend emits a body followed by a trailer section
- **THEN** the trailer fields are delivered to the client as trailers
- **AND** they do not appear among the response header fields

#### Scenario: Status carried only in trailers

- **WHEN** a backend reports the outcome of a call exclusively in a trailer field
- **THEN** that field is delivered to the client
- **AND** the outcome is not lost when the response status is successful

#### Scenario: Trailers without body octets

- **WHEN** a backend emits a response head, no body octets, and a trailer section
- **THEN** the trailer fields are carried and delivered as trailers
- **AND** they do not appear among the response header fields

#### Scenario: No trailers where the message defines none

- **WHEN** a response is one the client's request method or the response status defines as having no body
- **THEN** no trailer section is carried for that response
- **AND** the message is still terminated by a body-completion frame
- **AND** a trailer section arriving for such a message resets the stream with an enumerated code

#### Scenario: A framing or authorisation field in a trailer is discarded

- **WHEN** a backend emits a trailer section containing a content-length field and an authorisation field alongside an ordinary trailer field
- **THEN** the ordinary field is delivered to the client as a trailer
- **AND** neither the content-length nor the authorisation field is delivered as a trailer or appears among the response header fields
- **AND** neither is used to frame or authorise anything
- **AND** both are recorded for diagnostics

### Requirement: Incremental transfer without aggregation

An implementation that declared the response-streaming capability SHALL forward a response head as soon as it is available from the backend, without waiting for the body to complete, and SHALL forward body octets as they arrive. An implementation that declared the request-streaming capability SHALL likewise begin transferring a request body before the client has finished producing it. Neither SHALL require a complete body in order to begin transfer in the direction it declared.

An implementation that declared neither is permitted to aggregate, and SHALL be refused the exchanges that need incremental transfer rather than allowed to hang until a bound expires. This is the case the refusal rule exists for: a counterpart that buffers a whole response does not fail a response that never ends, it holds it, and the client cannot tell the difference from a slow backend.

The contract SHALL NOT make an exchange of unbounded duration unrepresentable, and SHALL NOT make the transfer of a frame conditional on the elapsed duration of its exchange. Bounds on the duration of an exchange are policy owned by the proxy's timeout classes, at least one of which permits an unbounded total; the contract SHALL impose no total-duration bound of its own.

#### Scenario: An aggregating counterpart is refused rather than allowed to hang

- **WHEN** a route whose class carries a response with no determinate end is matched to a tunnel whose counterpart declared no response-streaming capability
- **THEN** the exchange is refused with the response-streaming capability named
- **AND** the exchange is not dispatched and does not run until a bound expires

#### Scenario: Head forwarded before body completes

- **WHEN** a backend emits response headers and then withholds the body for a period
- **THEN** the client receives the response headers during that period
- **AND** the exchange remains open

#### Scenario: Endless response body

- **WHEN** a backend emits a response whose body never ends and continues to emit octets periodically
- **THEN** each group of octets is delivered to the client as it is produced
- **AND** no bound the contract itself imposes ends the exchange
- **AND** the exchange ends only when a party ends it, or a bound the deployment's timeout policy defines is exceeded

#### Scenario: Request body streams before completion

- **WHEN** a client sends a request body larger than any single frame and slower than the tunnel
- **THEN** the backend begins receiving body octets before the client has finished sending
- **AND** no complete copy of the body is required at any hop in order to begin transfer

#### Scenario: Memory held does not grow with body size

- **WHEN** two response bodies are transferred, the second many times larger than the first, over tunnels declaring identical credit
- **THEN** the peak memory attributable to the exchange at each hop stays within the configured buffer bound for both
- **AND** the peak for the larger body does not exceed the peak for the smaller by more than one frame
- **AND** both bodies are delivered byte-identically

### Requirement: Credit-based flow control

The contract SHALL provide flow control by credit, applied per stream and to the tunnel as a whole. A sender SHALL possess both whole-tunnel and per-stream credit for every body octet it emits. Each side SHALL declare its initial per-stream and whole-tunnel credit at establishment, and further credit SHALL be granted only by credit-update frames carrying a strictly positive delta.

Credit accounting is baseline: every implementation SHALL track, respect, and return credit, and SHALL treat an overrun as the violation described below, whatever it declared. The declarable flow-control capability names something narrower — the ability to advertise a bounded initial window and to withhold further credit in response to a slow consumer. A side that does not declare it SHALL advertise an initial window the contract defines as effectively unbounded for its version and SHALL NOT withhold credit; the accounting still applies, but no backpressure results from it. A route whose declared class requires backpressure SHALL be refused a tunnel that did not declare the capability, with the capability named, rather than served without it.

Stream-level credit SHALL be returned as the receiving application consumes octets. Tunnel-level credit SHALL be returned for octets the receiver has received, independently of whether the application has consumed them, so that one stalled stream cannot hold the whole-tunnel window. An implementation SHALL propagate the readiness of its own downstream consumer into the stream credit it grants upstream, so that a slow consumer results in a slow producer rather than in unbounded buffering.

Transferring octets beyond the credit in force, and a credit update that would carry a window beyond its representable maximum, SHALL each be a tunnel-level flow-control violation with an enumerated code; a receiver SHALL NOT absorb the excess, wrap the window, or silently cap it. A credit update naming a stream that has ended SHALL be discarded and recorded.

#### Scenario: Accounting binds a peer that declared no flow-control capability

- **WHEN** a peer that did not declare the flow-control capability establishes a tunnel
- **THEN** the initial window in force is the contract's effectively unbounded value for that version
- **AND** that peer still returns credit for the octets it receives
- **AND** emitting octets beyond the window in force is still a flow-control violation

#### Scenario: A backpressure-requiring route refuses a peer that cannot withhold credit

- **WHEN** a route whose class requires backpressure is matched to a tunnel whose counterpart did not declare the flow-control capability
- **THEN** the exchange is refused with the flow-control capability named
- **AND** it is not served with an unbounded window

#### Scenario: Slow client throttles the backend

- **WHEN** a client reads a large response more slowly than the backend produces it
- **THEN** the rate at which the proxy grants further credit to the sidecar falls to the rate the client consumes
- **AND** the sidecar's rate of reading from the backend falls with it
- **AND** octets buffered at each hop for that exchange stay within the credit that hop's receiver advertised, plus at most one frame

#### Scenario: Credit exhaustion pauses rather than fails

- **WHEN** available credit for a stream reaches zero
- **THEN** transfer on that stream pauses
- **AND** the exchange is not reset
- **AND** transfer resumes when credit is granted

#### Scenario: A stalled stream does not consume the tunnel window

- **WHEN** one stream's application stops consuming and its stream credit reaches zero
- **AND** octets for that stream have been received and buffered within its window
- **THEN** tunnel-level credit for those octets has been returned
- **AND** other streams on the same tunnel continue to transfer at their own rate

#### Scenario: Tunnel credit binds independently of stream credit

- **WHEN** a stream has ample credit and the whole-tunnel window is exhausted
- **THEN** no body octet is emitted on that stream
- **AND** transfer resumes when tunnel credit is granted

#### Scenario: A sender exceeding its credit fails the tunnel

- **WHEN** a peer emits more body octets on a stream than the credit granted to it
- **THEN** the tunnel is failed with a flow-control-violation code
- **AND** the excess octets are not buffered or delivered

#### Scenario: A credit update that would overflow the window

- **WHEN** a credit update would carry a window beyond its representable maximum
- **THEN** the tunnel is failed as a flow-control violation
- **AND** the window is neither wrapped nor silently capped

### Requirement: Cancellation propagates in both directions

The contract SHALL provide a stream reset carrying a stream identifier and an application error code, sendable by either side at any point in an exchange. Receipt of a reset SHALL cancel the work associated with that stream.

A proxy SHALL reset a stream when the client that originated it is no longer able to receive the response. A sidecar SHALL cancel its backend request upon receiving a reset.

A reset for a stream the receiver has already reset SHALL be discarded, and a frame arriving for a stream already released SHALL be discarded without a tunnel-level error and without a further reset.

#### Scenario: Client disconnect cancels backend work

- **WHEN** a client disconnects while a response is being transferred
- **THEN** the proxy resets that stream
- **AND** the sidecar cancels the corresponding backend request
- **AND** the backend stops producing for that request

#### Scenario: Backend failure after headers are committed

- **WHEN** a backend fails after its response headers have already been delivered to the client
- **THEN** the sidecar resets that stream with an error code distinguishing failure after commitment
- **AND** the client observes a truncated response rather than a complete one

#### Scenario: Reset returns the tunnel to its pre-exchange accounting

- **WHEN** a large number of exchanges are opened and reset in sequence on one tunnel
- **THEN** the count of open exchanges each side reports returns to its pre-test value
- **AND** each side's outstanding credit returns to its initial value
- **AND** memory attributable to that tunnel returns to within its pre-test level plus the configured buffer bound

#### Scenario: Frames arriving after a reset are discarded

- **WHEN** both sides reset the same stream at the same instant and further frames for it are already in flight
- **THEN** each side discards the frames it receives for that stream
- **AND** neither emits a further reset for it
- **AND** the tunnel remains established and other exchanges are unaffected

#### Scenario: Reset does not affect other streams

- **WHEN** one stream is reset
- **THEN** other in-flight exchanges on the same tunnel are unaffected

### Requirement: Multiplexing without head-of-line blocking

Every frame SHALL be bounded in size by the maximum payload the receiving side declared. The number of exchanges in flight concurrently SHALL be bounded by the maximum the receiving side declared; an exchange opened beyond that maximum SHALL be reset with an enumerated code naming the exceeded maximum rather than terminating the tunnel.

An implementation SHALL interleave frames belonging to different streams such that, while any stream has frames ready to send and credit to send them, no stream is starved of transmission for longer than a declared bound, regardless of the volume other streams have ready.

Tunnel-scoped control frames SHALL make progress regardless of the volume of data in flight on other streams.

#### Scenario: Large transfer does not block a small request

- **WHEN** a very large response is transferring on one stream
- **AND** a short request arrives on the same tunnel
- **THEN** the short request completes without waiting for the large transfer to finish

#### Scenario: A saturating stream does not starve a peer stream

- **WHEN** one stream always has frames ready and ample credit, and a second stream has one small frame ready
- **THEN** the second stream's frame is transmitted within the declared starvation bound
- **AND** the first stream does not transmit indefinitely before it

#### Scenario: Control frames survive saturation

- **WHEN** the tunnel is saturated with body frames
- **THEN** liveness probes continue to be answered within the declared bound
- **AND** the tunnel is not torn down for a missed answer

#### Scenario: A body of any size respects the value in force

- **WHEN** a body many times the declared maximum frame payload is transferred
- **THEN** every frame carrying it has a payload no larger than the value the receiving side declared
- **AND** the reassembled body is byte-identical to the original

#### Scenario: Exceeding declared concurrency is a stream error, not a tunnel error

- **WHEN** a peer opens one more concurrent exchange than the receiver declared it would serve
- **THEN** that exchange is reset with a code naming the exceeded maximum
- **AND** every exchange already in flight continues
- **AND** the tunnel remains established

### Requirement: Per-stream ordering is guaranteed

The contract SHALL guarantee that frames belonging to one stream are delivered to the receiving application in the order they were sent. The contract SHALL NOT guarantee ordering between separate streams.

The guarantee is one of observable delivery order, not of internal processing: however a side processes frames, the order in which it delivers them to the receiving application SHALL be the order in which they were sent.

#### Scenario: Body octets arrive in order

- **WHEN** a body is sent as many frames
- **THEN** the receiving side reassembles them in the order sent

#### Scenario: Bidirectional stream messages arrive in order

- **WHEN** a client sends several messages in sequence on a bidirectional stream
- **THEN** the backend receives them in that same sequence

#### Scenario: Concurrent internal processing does not reorder delivery

- **WHEN** a receiver processes the frames of one stream on more than one worker
- **THEN** the frames are delivered to the receiving application in the order they were sent
- **AND** no reordering is observable at either end

#### Scenario: A stream does not span tunnel connections

- **WHEN** a sidecar holds more than one tunnel connection and an exchange is in flight on one of them
- **THEN** every frame of that exchange is carried on that same connection
- **AND** a frame bearing that stream identifier arriving on another connection is discarded and recorded as a protocol violation
- **AND** the exchange is unaffected

### Requirement: Bidirectional stream exchanges carry the backend handshake

The contract SHALL represent the establishment of a bidirectional stream as an exchange that returns the response the backend actually gave: its status, its header section less the fields that are properties of the sidecar-to-backend connection, and its body if any. An implementation SHALL NOT probe the backend in a separate preliminary exchange in order to decide whether to accept the client.

A non-accepting backend response SHALL be carried over the tunnel rather than collapsed into a generic error. What the client is then shown, and whether an accepting response carrying a value the client did not offer is admitted at all, are owned by the bidirectional-stream edge capability rather than by the contract.

#### Scenario: Successful establishment relays the real response

- **WHEN** a backend accepts a bidirectional stream and its accepting response carries a negotiated subprotocol and a cookie field
- **THEN** the response carried over the tunnel carries that same negotiated subprotocol and cookie field

#### Scenario: Backend refuses with an authentication challenge

- **WHEN** a backend refuses to establish a bidirectional stream and responds with an authentication challenge
- **THEN** the challenge status and its header fields are carried over the tunnel
- **AND** they are not replaced by a generic gateway error

#### Scenario: No preliminary probe is issued

- **WHEN** a client requests a bidirectional stream
- **THEN** exactly one establishment exchange reaches the backend
- **AND** the backend does not observe an additional connection that is opened and immediately closed

#### Scenario: Connection-scoped handshake fields do not cross the tunnel

- **WHEN** a backend's accepting response carries upgrade and connection tokens belonging to the sidecar-to-backend hop
- **THEN** those fields are not present in the response head carried over the tunnel
- **AND** every other field of the response is present in the order received

### Requirement: Bidirectional stream frames preserve their structure

The contract SHALL deliver each frame of a bidirectional stream with its finality indicator, its frame type, its reserved bits and its payload octets exactly as the sending side constructed them, so that fragmented messages remain fragmented and control frames remain distinguishable from data frames. This is faithful carriage of what a sender constructs, not an assertion that a tunnel frame equals a hop frame.

Reserved bits on a tunnel frame describe the tunnel frame alone. A hop that terminates a frame-transforming extension SHALL resolve that extension before constructing the tunnel frame, placing the untransformed payload on the tunnel with that extension's bits clear; the receiving hop SHALL construct the frame its own hop's negotiation calls for. At version 1 every reserved bit on a tunnel frame SHALL be zero, and a receiver finding a reserved bit set that the negotiated contract version does not define SHALL reset that stream with an enumerated code.

The contract SHALL enumerate, per contract version, which control frame types cross the tunnel and which are answered by the hop that receives them. At version 1 the close frame SHALL cross the tunnel; liveness probe and probe-response frames SHALL be answered by the receiving hop and SHALL NOT cross it. Any per-hop payload obfuscation the stream protocol applies SHALL be removed before a frame is placed on the tunnel and applied afresh by the hop that emits it.

Because a probe never crosses the tunnel, no probe answered on one hop is evidence about the other, and the tunnel's own liveness mechanism proves only that the counterpart's contract layer is running — not that a particular stream's far endpoint still is. Liveness of a bidirectional stream is therefore composed rather than end to end: each hop SHALL operate its own probe against the endpoint it terminates against, SHALL bound the time it waits for an answer, and on expiry SHALL reset that stream over the tunnel with the enumerated code for a counterpart that stopped answering on an established bidirectional stream. A hop SHALL NOT hold a stream open on the strength of the liveness of the other hop, and SHALL NOT report a stream as alive on the strength of the tunnel being alive.

Close information SHALL carry the originating code and reason unaltered, including every code in the application-defined range. A code outside the range the stream protocol permits on the wire SHALL NOT be relayed: the hop that received it SHALL treat it as a protocol violation of that hop and record it, and the vocabulary of any close that hop then originates is owned by the bidirectional-stream edge capability rather than by the contract.

#### Scenario: A hop's own probe is what detects its endpoint

- **WHEN** the endpoint a hop terminates against stops answering that hop's probes on an established bidirectional stream
- **THEN** that hop resets the stream over the tunnel within its declared bound
- **AND** the reset carries the enumerated code for a counterpart that stopped answering
- **AND** the tunnel remains established and its other streams are unaffected

#### Scenario: Tunnel liveness is not stream liveness

- **WHEN** the tunnel's own liveness probes continue to be answered while a bidirectional stream's far endpoint has stopped answering that hop's probes
- **THEN** the stream is still reset within the declared bound
- **AND** the tunnel remaining alive is not treated as evidence that the stream's endpoint is

#### Scenario: Fragmented message stays fragmented

- **WHEN** a client sends one message split across a first frame and continuation frames
- **THEN** the backend receives the same sequence of frames with the same finality indicators
- **AND** the backend is not given a single coalesced message

#### Scenario: Application close code is preserved

- **WHEN** a backend closes a bidirectional stream with an application-defined code and a reason
- **THEN** the client receives that same code and reason
- **AND** the code is not replaced with a protocol-level code

#### Scenario: Binary and text frames remain distinct

- **WHEN** a backend sends a binary frame and a text frame
- **THEN** the client receives one binary frame and one text frame
- **AND** neither is reinterpreted as the other

#### Scenario: A per-hop extension bit does not cross the tunnel

- **WHEN** a hop that negotiated a frame-transforming extension receives a frame with that extension's indicator set
- **THEN** the frame it places on the tunnel carries the untransformed payload with every reserved bit zero
- **AND** the finality indicator and the frame type are unchanged
- **AND** what the receiving hop emits is determined by that hop's own negotiation

#### Scenario: A liveness probe is answered at the hop that receives it

- **WHEN** a client sends a liveness probe on an established bidirectional stream
- **THEN** the proxy answers it
- **AND** no frame for that probe reaches the backend
- **AND** whether the backend is still reachable is reported by the tunnel's own liveness mechanism

#### Scenario: Out-of-range close code is not relayed

- **WHEN** a close code outside the range the stream protocol permits on the wire is received from a backend
- **THEN** the receiving hop treats it as a protocol violation of that hop
- **AND** the invalid code is not carried over the tunnel
- **AND** the condition is recorded for diagnostics

### Requirement: Datagram class is defined and reserved

The contract SHALL define a datagram frame kind whose delivery is not guaranteed and which does not participate in credit-based flow control. A datagram SHALL carry the identifier of the bidirectional stream whose session it belongs to, SHALL NOT be fragmented, and SHALL NOT exceed the maximum frame payload in force. A receiver SHALL discard a datagram bearing an identifier for which no such session exists.

A receiver SHALL be permitted to discard a datagram it has no capacity to buffer, and to discard a buffered datagram rather than deliver it late. The bounds on what a receiver buffers are enforced at the receiving hop under the per-tenant dimensions the isolation capability owns; the contract SHALL NOT fix them. Every discard SHALL be recorded and attributable to its cause, distinguishing a capacity discard, an age discard, and a discard for an unknown session.

At contract version 1 the datagram frame kind SHALL be reserved and MAY be unimplemented. An implementation that does not implement it SHALL declare the datagram capability as unsupported.

#### Scenario: Datagram capability undeclared at version 1

- **WHEN** a sidecar at contract version 1 establishes a tunnel without declaring datagram support
- **THEN** the tunnel is established
- **AND** exchanges requiring datagrams are refused with the datagram capability named

#### Scenario: Datagrams are discarded rather than queued without bound

- **WHEN** an implementation declaring the datagram capability receives datagrams faster than it consumes them
- **THEN** it discards those in excess of its configured bound
- **AND** memory held for datagrams stays within that bound
- **AND** its count of capacity discards increases
- **AND** no stream is reset

#### Scenario: Stale datagrams are dropped, not delivered late

- **WHEN** an implementation declaring the datagram capability holds a datagram past its configured maximum age
- **THEN** it discards it rather than delivering it
- **AND** its count of age discards increases
- **AND** the discard is distinguishable from one made for want of capacity

#### Scenario: A datagram naming an unknown session

- **WHEN** a datagram names a stream identifier for which no bidirectional stream session exists
- **THEN** it is discarded and recorded
- **AND** no stream is created and no stream is reset

### Requirement: Errors are machine-readable

Every error the contract conveys SHALL carry a stable, enumerated code, together with an optional human-readable description. An implementation SHALL NOT convey an error as a rendering of a host-language value. Stream reset codes and tunnel error codes SHALL be drawn from one code space.

The contract SHALL publish its enumeration with each version and SHALL partition it into named classes, with the class of a code derivable from the code itself without recognising the code, so that an unrecognised code is still actionable. The enumeration at version 1 SHALL cover at minimum: version incompatibility; a malformed version declaration; authentication or authorisation failure; a credential no longer valid; an undeclared or baseline-violating capability; an unimplemented or unrecognised frame kind; a tunnel protocol violation; a flow-control violation; a declared parameter exceeded; a mount the receiver was not admitted for; a destination the receiver refuses to originate against; a malformed method, field, or target; cancellation by the originator; an exchange abandoned because the tunnel ended; drain in progress; and an unspecified failure.

Because the far hop of an exchange is reached by one side alone, the enumeration SHALL additionally distinguish, at version 1, each way that hop can fail, so that the side that did not reach it can attribute the failure without a second vocabulary: the configured origin's host could not be resolved; the connection was refused; the connection attempt exceeded the originating side's own bound; the origin's identity could not be verified where the configured origin requires it; no response head arrived within the originating side's own bound; the body went idle beyond that side's own bound; the origin failed or closed after its response head; the origin stopped answering on an established bidirectional stream; and a protocol violation of the originating side's own hop. Where a version of the contract admits a translation between framings performed at one hop, the enumeration SHALL likewise distinguish each way that translation can fail — a malformed frame in the carried body, a frame declaring a length beyond the configured bound, a section exceeding its configured maximum, a field the target framing cannot express, and an origin that ended without the section the framing requires — so that a translation failure is never conveyed as an origin failure or a transport failure. Every enumerated cause a capability of this system conveys over the tunnel SHALL be a code of this enumeration; a capability SHALL NOT convey a cause of its own devising in a description field, because a description is diagnostic text no receiver may branch on.

Adding a code SHALL NOT be a breaking change; a code SHALL NOT change class or meaning across versions, and a retired code SHALL NOT be reassigned.

Every code in this enumeration SHALL be an entry in the single published registry of enumerated causes the observability capability owns, mapping each to exactly one outcome value. This contract SHALL NOT maintain a second mapping, and where a component records or measures a condition this enumeration covers it SHALL use this code rather than a separately invented equivalent.

A description SHALL be bounded in length by configuration, SHALL be diagnostic text about the failure, and SHALL NOT carry any part of a message body, header value, or request target, any credential material, or anything attributable to a tenancy other than the one the tunnel is authenticated for. A receiver SHALL treat a description, and any unrecognised name a peer sends, as untrusted data: it SHALL bound them before retaining them, SHALL record them as a single bounded value that cannot alter the structure of a record, and SHALL bound the total it retains for unrecognised values on one tunnel.

#### Scenario: Failure carries an enumerated code

- **WHEN** a sidecar cannot reach its backend
- **THEN** the error conveyed names the enumerated condition for an unreachable backend
- **AND** it does not contain a host-language representation of an internal value

#### Scenario: An unrecognised code is still classified

- **WHEN** a receiver is given an error code introduced in a later contract version
- **THEN** it reports the class the code belongs to
- **AND** it takes the action its policy assigns to that class rather than one default for all unknown codes
- **AND** it records the unrecognised code
- **AND** it does not terminate the tunnel

#### Scenario: One condition carries one code everywhere

- **WHEN** a condition the contract enumerates is recorded at the edge, conveyed over the tunnel, and measured
- **THEN** all three carry the same published contract code

#### Scenario: Each way the far hop fails carries its own code

- **WHEN** the far hop of an exchange in turn cannot be resolved, refuses the connection, exceeds the connect bound, presents an unverifiable identity, returns no response head within the bound, goes idle mid-body, and fails after its response head
- **THEN** each is conveyed with a different code of this enumeration
- **AND** none is conveyed as the unspecified failure
- **AND** none is distinguished only by its description

#### Scenario: A translation failure is not an origin failure

- **WHEN** a hop performing a translation cannot complete it
- **THEN** the code conveyed is the one this enumeration defines for that translation failure
- **AND** it is distinguishable from every origin-failure code and from every transport failure

#### Scenario: An oversized description is bounded before it is retained

- **WHEN** a peer conveys an error whose description exceeds the configured bound
- **THEN** the description is bounded before it is retained or recorded
- **AND** memory held for it does not exceed the bound

#### Scenario: A description carries no payload and cannot restructure a record

- **WHEN** an error is conveyed for an exchange whose body and header values contain distinctive content, and the description contains the delimiters of the receiver's record format
- **THEN** none of the exchange's content appears in the description
- **AND** the description appears as one field value of one record

### Requirement: The wire encoding is normatively specified and binary-safe

The encoding specification SHALL define, for every frame kind at every contract version: the octet layout, the order of fields, the width and byte order of every integer, the length delimitation of every variable-length field, and the treatment of a field whose stated length exceeds the frame. It SHALL make an absent optional field distinguishable from one present with an empty value, for every optional field the contract defines. It SHALL be versioned together with the contract.

The specification SHALL state, for every field it defines, the receiver's behaviour when that field is absent, out of range, or inconsistent with another field, and SHALL classify each such behaviour as stream-fatal or tunnel-fatal. An input the specification does not admit SHALL have exactly one defined outcome, so two conforming implementations produce the same classification and the same enumerated cause for it.

The contract SHALL publish, for every frame kind, encode-decode vectors pairing a described frame with its exact octets. The encoding SHALL carry arbitrary octet sequences in body and datagram payloads without transformation.

#### Scenario: Published vectors are reproduced byte for byte

- **WHEN** an implementation encodes the described frame of each published vector
- **THEN** its output is byte-identical to that vector's octets
- **AND** decoding each vector's octets yields the described frame
- **AND** a vector whose frame kind it does not implement is reported as unimplemented rather than encoded differently

#### Scenario: Encoding carries arbitrary octets

- **WHEN** a body containing octets not valid in any character encoding is carried
- **THEN** the encoding conveys them without alteration

#### Scenario: Two implementations agree on malformed input

- **WHEN** the same malformed frame is presented to two independently written conforming implementations
- **THEN** both produce the same classification and the same enumerated cause

#### Scenario: A nested length overrunning its frame

- **WHEN** a length inside a header section declares more octets than remain in the frame
- **THEN** the tunnel is failed as a protocol violation
- **AND** octets from the following frame are not consumed as part of the section

#### Scenario: Encoding change is a contract version change

- **WHEN** the encoding changes in a way that an existing implementation cannot parse
- **THEN** the contract version is incremented
- **AND** version negotiation prevents an incompatible pairing from being established

### Requirement: Contract changes are additive by default

A contract version SHALL declare support for every version released within the contract's declared support window and SHALL serve them. Withdrawing support for a version SHALL be announced in the version preceding the one that withdraws it and SHALL NOT take effect before the support window has elapsed. Introducing a field, a frame kind, an error code, or a capability name SHALL NOT require existing implementations to change.

An implementation encountering a field, frame kind, capability name, or error code it does not recognise SHALL NOT act on it and SHALL record it; where it is relaying a contract frame onward it SHALL carry the unrecognised item unchanged. Tolerance of the unknown SHALL NOT extend to the known: a field the negotiated version defines, carrying a value outside the range that version defines for it, SHALL be rejected with an enumerated cause and SHALL NOT be ignored, defaulted, or clamped.

A change that cannot be made additively SHALL require a new contract version, a capability flag distinguishing the behaviours, and a documented period during which both are served. The contract SHALL record, per version, which counterpart versions remain compatible.

#### Scenario: New optional field ignored by an older implementation

- **WHEN** a newer counterpart includes a field an older implementation does not know
- **THEN** the older implementation serves the exchange normally
- **AND** it ignores the unknown field and records it

#### Scenario: An unknown field survives relay

- **WHEN** a contract frame carrying an unrecognised field is relayed onward by an implementation that speaks the contract on both sides
- **THEN** the field reaches the far end unchanged
- **AND** the relaying implementation did not act on it
- **AND** it recorded it

#### Scenario: An invalid known value is rejected, not ignored

- **WHEN** a frame carries both an unknown field and a defined field whose value is outside the range the negotiated version defines
- **THEN** the unknown field is ignored
- **AND** the frame is still rejected with an enumerated cause for the out-of-range value
- **AND** that value is not defaulted or clamped

#### Scenario: Support reaches back across the whole window

- **WHEN** a proxy at the newest contract version meets a sidecar at the oldest version still inside the support window
- **THEN** the tunnel is established at that older version
- **AND** it is refused only for a version released before the window began

#### Scenario: Breaking change is gated by a capability

- **WHEN** a behaviour changes incompatibly between contract versions
- **THEN** the new behaviour is reachable only when both sides declare the corresponding capability
- **AND** an implementation that does not declare it receives the prior behaviour

#### Scenario: Compatibility is documented per version

- **WHEN** a contract version is released
- **THEN** its documentation states which counterpart versions remain compatible
- **AND** it states which prior behaviours are deprecated and the earliest version that may remove them

### Requirement: A version claim is backed by conformance

The contract SHALL identify each of its normative requirements by a stable identifier that does not change across contract versions and that stays attached to a requirement whose wording changes.

An implementation SHALL declare support for a contract version only where a conformance result exists for that version and for the capability set it declares. This is an obligation on the party that releases an implementation, discharged before release; it is not a runtime check. The contract SHALL NOT define a conformance attestation carried on the wire, and a peer SHALL NOT refuse a tunnel on the ground that it has not seen a conformance result — the proxy cannot evaluate the provenance of a result for a sidecar built by someone it does not control, and a refusal on that ground would make every third-party implementation unserviceable.

The composition of the conformance suite, its coverage obligations, its execution and the form of its results are owned by the conformance capability rather than defined here; every requirement of this contract, including every rejection and every declared bound it defines, SHALL be within that coverage.

#### Scenario: Conformance gates a version claim

- **WHEN** an implementation does not pass the conformance suite for a contract version at the capability set it declares
- **THEN** it does not declare support for that version

#### Scenario: A version claim is not checked on the wire

- **WHEN** a sidecar establishes a tunnel declaring a contract version and a capability set
- **THEN** no conformance result is requested, carried, or evaluated during establishment
- **AND** the tunnel is neither refused nor established on the strength of one
- **AND** the enumeration of contract errors contains no code for a missing conformance result

#### Scenario: Requirement identifiers survive rewording

- **WHEN** a normative requirement's wording changes without changing its meaning
- **THEN** its identifier is unchanged
- **AND** conformance results recorded against the earlier wording still name the same requirement

#### Scenario: A new contract requirement is uncovered until a case exists

- **WHEN** a requirement is added to this contract and no conformance case references it
- **THEN** the coverage report names it as uncovered
- **AND** no implementation is reported as conformant for that version
