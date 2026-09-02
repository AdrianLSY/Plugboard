## Purpose

Defines the hierarchy of registered paths, the invariant that a mount point is terminal, and the rule by which an inbound request is matched to exactly one mount with a forwarded remainder. The terminal-mount invariant is what makes longest-prefix matching provably unambiguous, so it is stated here as an obligation rather than left as a convention. This capability also defines the namespace the proxy reserves for itself, the lifecycle of a mount through rename, deletion and recovery, and the consistency and staleness properties of the lookup surface that serves matching on the request path. Throughout this capability a *node* is an entry in the path hierarchy, never a running process, as `tenancy/isolation` fixes the term for the whole system; a running proxy process is an *instance*, and the *installation* is the whole set of them. The proxy is a multi-instance installation, so every instance that matches requests holds a lookup surface of its own and a request for one path may be matched by any of them; the consistency properties below are therefore stated for the installation and not only for the instance through which a change was made.

## ADDED Requirements

### Requirement: Paths form a single-parent hierarchy

The system SHALL model registered routing locations as nodes, each with at most one parent and each belonging to exactly one tenant. A node with no parent SHALL be a root-level node. A node SHALL NOT be its own ancestor, and a parent change SHALL NOT create a cycle.

A node SHALL carry a flag indicating whether it is a mount point. Only a mount point SHALL be eligible to receive proxied traffic; a node that exists but is not a mount point SHALL NOT be reachable by any request.

#### Scenario: Non-mount node is not routable

- **WHEN** a node exists at a path and is not marked as a mount point
- **AND** a request arrives whose path equals that node's path
- **THEN** the request does not match any mount
- **AND** no sidecar is selected and no tunnel exchange is started

#### Scenario: Cycle is refused

- **WHEN** an operation would make a node a descendant of itself
- **THEN** the operation is refused
- **AND** the stored hierarchy is unchanged

#### Scenario: Nodes belong to one tenant

- **WHEN** a node is created under a parent
- **THEN** it belongs to the same tenant as its parent
- **AND** it cannot be reparented under a node belonging to a different tenant

#### Scenario: Creating under another tenant's node is refused

- **WHEN** a caller acting for one tenant creates a node whose parent belongs to a different tenant
- **THEN** the creation is refused
- **AND** no node is created
- **AND** the refusal does not disclose whether that parent exists

### Requirement: Mount points are terminal

A mount point SHALL have no children. This obligation SHALL be enforced from both directions, and each direction SHALL be enforced independently of the other:

- A node SHALL NOT be created or reparented such that its parent is a mount point.
- A node that has at least one live child SHALL NOT be marked as a mount point.

Enforcement SHALL be a property of the durable store rather than of any single code path that writes to it, so that a write reaching the store by a path that omitted the check is still refused. Soft-deleted children SHALL NOT count toward the child test, and a mount point that has only soft-deleted children SHALL remain a valid mount point.

#### Scenario: Child under a mount is refused

- **WHEN** a caller attempts to create a node whose parent is a mount point
- **THEN** the creation is refused
- **AND** no node is created
- **AND** the mount point is unchanged

#### Scenario: Reparenting under a mount is refused

- **WHEN** an existing node is moved so that its new parent is a mount point
- **THEN** the move is refused
- **AND** the node retains its original parent and full path

#### Scenario: Marking a parent as a mount is refused

- **WHEN** a caller attempts to mark a node that has a live child as a mount point
- **THEN** the operation is refused
- **AND** the node remains a non-mount node

#### Scenario: Soft-deleted children do not block a mount

- **WHEN** every child of a node has been soft-deleted
- **AND** a caller marks that node as a mount point
- **THEN** the operation succeeds
- **AND** the node is a mount point

#### Scenario: Enforcement survives a bypassed write path

- **WHEN** a write that would create a child under a mount point reaches the durable store without passing through the ordinary validation path
- **THEN** the store refuses the write
- **AND** the invariant holds over the stored data

### Requirement: Hierarchy invariants hold under genuine concurrency

For any two operations executed concurrently that would together violate the terminal-mount invariant or a uniqueness obligation of this capability, at most one SHALL be reported as successful, and the durable state observed after both have completed SHALL satisfy the invariant. This SHALL hold when the two operations are issued from genuinely independent sessions, and SHALL NOT depend on the two operations being serialised by a session they share.

The failing operation SHALL fail with the same error it would produce had it been executed second in a serial order. It SHALL NOT fail with a deadlock, a timeout, or an unclassified fault presented to the caller.

#### Scenario: Concurrent create-child and mark-mount

- **WHEN** one session creates a child under a node
- **AND** another session concurrently marks that same node as a mount point
- **AND** both sessions commit
- **THEN** exactly one of the two operations is reported successful
- **AND** the stored state either has a mount point with no children or a non-mount node with one child
- **AND** the failing operation reports the terminal-mount violation

#### Scenario: Concurrent marks on parent and child

- **WHEN** one session marks a node as a mount point
- **AND** another session concurrently marks that node's child as a mount point
- **THEN** the resulting state contains no mount point that is an ancestor of another mount point

#### Scenario: Concurrent creation of the same sibling segment

- **WHEN** two independent sessions concurrently create a node with the same segment under the same parent
- **AND** both sessions commit
- **THEN** exactly one creation is reported successful
- **AND** the other is refused with the uniqueness error
- **AND** the parent has exactly one live child bearing that segment

#### Scenario: Losing operation returns a usable error

- **WHEN** an operation loses a concurrent race against the invariant
- **THEN** the caller receives the same classified error as in the serial case
- **AND** the caller does not receive a lock, deadlock, or timeout condition

### Requirement: Invariant and constraint violations are reported as field-level errors

Every refusal defined by this capability — a terminal-mount violation in either direction, a segment validation failure, a uniqueness collision, a depth or length bound, a cycle, a reserved-prefix collision, and the omission of any attribute another capability requires a mount to carry before it may serve traffic — SHALL be reported to the caller as a structured error that names the attribute responsible and carries a stable machine-readable code. The two directions of the terminal-mount invariant SHALL carry distinct codes.

The set of attributes a mount must carry before it serves traffic SHALL be assembled from every capability that requires one, so that a mount cannot be created lacking one and discovered only when a request arrives.

A refusal SHALL NOT reach the caller as an unhandled fault, a generic internal error, or a rendering of a store-level diagnostic. An interface that presents a form SHALL be able to attach every such error to the input that caused it without parsing a human-readable message.

#### Scenario: Child-under-mount error is attributable

- **WHEN** a caller attempts to create a node under a mount point
- **THEN** the error names the parent attribute
- **AND** the error carries a stable code distinct from every other refusal code in this capability
- **AND** the error is not an unhandled fault

#### Scenario: Mount-with-children error is attributable

- **WHEN** a caller attempts to mark a node with live children as a mount point
- **THEN** the error names the mount attribute
- **AND** its code differs from the child-under-mount code

#### Scenario: Store-level enforcement is translated

- **WHEN** a refusal originates in the durable store rather than in a prior check
- **THEN** the caller still receives a structured, attributed error
- **AND** the response is not a generic server error

#### Scenario: Refusal codes do not collide

- **WHEN** each refusal defined by this capability is provoked in turn
- **THEN** each produces a stable code
- **AND** no two distinct refusals produce the same code
- **AND** each error names the attribute it applies to

#### Scenario: A mount missing a required serving attribute is refused at creation

- **WHEN** a mount point is created omitting an attribute another capability requires before it may serve traffic, such as the timeout class governing exchanges on it
- **THEN** the creation is refused with an attributed, stably coded error naming that attribute
- **AND** every other omitted required attribute is named in the same refusal
- **AND** no mount is created that would be discovered to be unserveable only when a request arrives

### Requirement: A request matches at most one mount by longest prefix

The system SHALL match a request path to the mount point whose path is the longest prefix of the request path at a segment boundary. Matching SHALL terminate in exactly one of two outcomes: a single matched mount, or no match.

Because a mount point has no descendants, at most one mount point can be a prefix of any request path. The matching rule therefore SHALL require no ordering, no priority field, and no tie-break rule, and an implementation SHALL NOT introduce one. If two mount points are ever found such that one is a prefix of the other, that SHALL be reported as an integrity violation rather than resolved by preference.

A mount identified by other means, such as a resolved host name, SHALL be subject to the same terminal-mount and uniqueness guarantees; the rules for resolving a host name to a mount are outside this capability.

#### Scenario: Longest prefix wins with no ancestor mount possible

- **WHEN** a mount point exists at a two-segment path
- **AND** a request arrives for a four-segment path beginning with those two segments
- **THEN** the two-segment mount is matched
- **AND** no other mount is a candidate

#### Scenario: Prefix must end at a segment boundary

- **WHEN** a mount point exists at a path ending in a segment
- **AND** a request arrives whose corresponding segment merely begins with that segment's characters and continues with more
- **THEN** the request does not match that mount

#### Scenario: Matching is case-sensitive

- **WHEN** a mount point exists at a path
- **AND** a request arrives for the same path with the case of one segment altered
- **THEN** the request does not match that mount
- **AND** the result is an explicit no-match

#### Scenario: A request shorter than a mount path does not match it

- **WHEN** a mount point exists at a three-segment path
- **AND** a request arrives for the two-segment prefix of that path
- **THEN** the request does not match that mount
- **AND** an ancestor node at that two-segment path, if one exists, is not treated as a mount

#### Scenario: No match is a distinct outcome

- **WHEN** a request arrives for a path with no mount point at any prefix
- **THEN** the result is an explicit no-match
- **AND** no mount is selected, no remainder is computed, and no tunnel exchange is started

#### Scenario: Two overlapping mounts are an integrity violation

- **WHEN** the lookup surface is presented with two mount points where one path is a prefix of the other at a segment boundary
- **THEN** the condition is reported as an integrity violation
- **AND** it is not resolved by choosing either one

#### Scenario: Match cost is bounded by path depth, not by mount count

- **WHEN** the same request path is matched against an installation holding a small number of mounts and against one holding a very large number
- **THEN** the number of lookups performed against the lookup surface is the same in both cases
- **AND** that number is bounded by the count of segments in the request path
- **AND** no lookup enumerates, scans, or sorts the set of mounts

### Requirement: The proxy's own namespace is not mountable

This capability SHALL hold the single reserved-path enumeration for the installation. Every other capability that needs a path served by the proxy itself rather than by a mount SHALL contribute its prefix to this enumeration rather than maintaining a set of its own.

On any hostname where the proxy serves endpoints of its own, the system SHALL maintain a set of reserved path prefixes covering at minimum: the endpoint a sidecar uses to establish a tunnel; any operator or administrative interface exposed there; the liveness, readiness and diagnostic surfaces exposed there; and the path on which hostname-ownership challenges are answered. The set SHALL be a closed enumeration, observable to an operator, and SHALL NOT be extendable by a tenant. A request whose path falls under a reserved prefix at a segment boundary SHALL be served by the proxy itself and SHALL NOT be matched to any mount.

Each reserved prefix SHALL be the narrowest prefix the endpoint it protects requires. Reserving a prefix SHALL NOT reserve the siblings of the protected endpoint under a shared ancestor, because a tenant's own well-known resources live there.

Creating a mount point, marking a node as a mount point, or moving one, such that its full path equals or falls under a reserved prefix, SHALL be refused with an attributed error. On such a hostname the root path SHALL NOT be mountable, because a mount there would shadow every reserved prefix.

Reservation SHALL apply at segment boundaries only, so a path that merely begins with the characters of a reserved prefix remains matchable.

#### Scenario: The tunnel endpoint is not proxied to a mount

- **WHEN** a request arrives for the path a sidecar uses to establish its tunnel
- **THEN** the proxy serves it
- **AND** no mount is matched
- **AND** no tunnel exchange is started on behalf of that request

#### Scenario: Mounting a reserved prefix is refused

- **WHEN** a caller attempts to create a mount point whose full path falls under a reserved prefix
- **THEN** the operation is refused with an error naming the offending attribute
- **AND** no node is created

#### Scenario: Moving a mount under a reserved prefix is refused

- **WHEN** an existing mount point is moved so that its full path would fall under a reserved prefix
- **THEN** the move is refused
- **AND** the mount remains matchable at its original path

#### Scenario: A root mount is refused where reserved prefixes exist

- **WHEN** a caller attempts to mark the root path as a mount point on a hostname carrying reserved prefixes
- **THEN** the operation is refused

#### Scenario: A similar prefix is still matchable

- **WHEN** a mount point exists at a path whose first segment begins with the characters of a reserved prefix's first segment but is longer
- **AND** a request arrives for that mount
- **THEN** the request matches the mount
- **AND** it is not diverted to a proxy-served endpoint

#### Scenario: A sibling under a shared ancestor is not reserved

- **WHEN** a reserved prefix and a path a tenant's backend serves share an ancestor segment
- **AND** a request arrives for the tenant's path
- **THEN** the request is matched against mounts as ordinary traffic
- **AND** it is not diverted to a proxy-served endpoint

#### Scenario: The reserved set is a closed enumeration

- **WHEN** an operator retrieves the reserved path prefixes in force
- **THEN** the enumeration includes the tunnel-establishment endpoint, the administrative interface, the operational probe surfaces, and the hostname-challenge path where each is exposed on that hostname
- **AND** no request path outside the enumeration is diverted from mount matching

### Requirement: The forwarded remainder is the request target minus the mount prefix

When a request matches a mount, the system SHALL compute a remainder consisting of the request path with exactly the matched mount path removed from its front. A remainder that would be empty SHALL be the root path. A trailing slash present in the request path SHALL be present in the remainder.

The remainder SHALL be derived by removal only; the system SHALL NOT collapse, reorder, decode, re-encode, case-fold, or otherwise rewrite the retained segments. The query component SHALL NOT participate in matching and SHALL NOT be consumed or altered by remainder computation.

A request whose path is exactly the mount path, and a request whose path is the mount path followed by a single separator, SHALL both yield the root path as the remainder. This is the only case in which a trailing slash is not distinguishable in the remainder.

Where a mount is identified by a means that consumes no path prefix, such as a resolved host name, the remainder SHALL be the entire received path.

#### Scenario: Request equal to the mount path

- **WHEN** a request path is exactly the matched mount path
- **THEN** the remainder is the root path

#### Scenario: Remainder retains its segments

- **WHEN** a request path extends the matched mount path by two segments
- **THEN** the remainder is those two segments with a leading separator
- **AND** no other characters are added or removed

#### Scenario: Trailing slash is retained in the remainder

- **WHEN** a request path extends the matched mount path and ends with a trailing slash
- **THEN** the remainder ends with a trailing slash
- **AND** a collection target is distinguishable from a non-collection target of the same name

#### Scenario: Mount path followed by a separator

- **WHEN** a request path is the matched mount path followed by a single separator
- **THEN** the remainder is the root path

#### Scenario: A host-identified mount consumes no prefix

- **WHEN** a request is matched to a mount by a resolved host name rather than by a path prefix
- **THEN** the remainder is the entire received path
- **AND** no leading segment is removed from it

#### Scenario: Query is not part of matching

- **WHEN** a request carries a query component whose value resembles a mount path
- **THEN** the query does not affect which mount is matched
- **AND** the query is not consumed by remainder computation

### Requirement: Matching operates on undecoded segment boundaries

The system SHALL determine segment boundaries for matching using only the separators literally present in the received request path. A percent-encoded octet within a segment SHALL NOT be decoded for the purpose of matching and SHALL NOT be treated as a separator.

The path used for matching SHALL be the path as received. The only adjustment this capability permits before matching is treating an absent or empty path as the root path. The system SHALL NOT resolve relative segments, collapse repeated separators, add or strip a trailing separator, decode any octet, or change the case of any character in order to produce a matchable path.

#### Scenario: Encoded separator does not split a segment

- **WHEN** a request path contains a percent-encoded separator inside a single segment
- **THEN** that segment is treated as one segment for matching
- **AND** the encoded octet is still encoded in the computed remainder

#### Scenario: Encoded and literal separators are distinguished

- **WHEN** two requests arrive, one with a literal separator and one with the encoded form at the same position
- **THEN** they are not treated as the same path
- **AND** they may match different mounts or none

#### Scenario: Repeated separators are not collapsed

- **WHEN** a request path contains two consecutive separators
- **THEN** the path is matched as received rather than rewritten to remove the empty segment
- **AND** the remainder retains both separators

#### Scenario: An empty path is the root path

- **WHEN** a request arrives with an absent or empty path
- **THEN** it is matched as the root path
- **AND** no other adjustment is applied

### Requirement: Path segments have a bounded character set and length

A stored path segment SHALL consist only of ASCII letters, digits, hyphen, underscore, and full stop. It SHALL NOT be empty and SHALL NOT contain a path separator, a null octet, or whitespace. A stored path segment SHALL NOT exceed a configured maximum length measured in octets.

These bounds SHALL be enforced by the durable store as well as by the interface that accepts the input, so that a segment violating them cannot be stored by any route.

This character set constrains stored segments only. It SHALL NOT be applied to the portion of a request path beyond the matched mount prefix, which carries whatever a tenant's backend addresses and is not a namespace this system allocates.

#### Scenario: A segment at the maximum length is accepted

- **WHEN** a caller creates a node whose segment is exactly the configured maximum length in octets
- **THEN** the node is created

#### Scenario: A segment one octet over the maximum is rejected

- **WHEN** a caller creates a node whose segment is one octet longer than the configured maximum
- **THEN** the creation is refused with an error naming the segment attribute
- **AND** no node is created

#### Scenario: A separator inside a segment is rejected

- **WHEN** a caller supplies a segment containing a path separator
- **THEN** the creation is refused
- **AND** the input is not split into two nodes

#### Scenario: Characters outside the permitted set are rejected

- **WHEN** a caller supplies a segment containing a character outside the permitted set
- **THEN** the creation is refused with an error naming the segment attribute

#### Scenario: An empty segment is rejected

- **WHEN** a caller supplies an empty segment
- **THEN** the creation is refused

#### Scenario: The remainder is not constrained by the stored character set

- **WHEN** a request extends a matched mount path with a segment containing characters outside the permitted stored set, such as a space, a tilde, or a percent-encoded non-ASCII octet
- **THEN** the request is not rejected on character-set grounds
- **AND** the remainder carries that segment exactly as received

### Requirement: Request paths are bounded in depth and total length

Before matching, the system SHALL reject a request whose path exceeds a configured maximum number of segments, whose individual segment exceeds a configured maximum length in octets, or whose path in total exceeds a configured maximum length in octets. A rejected request SHALL receive a client error naming the bound that was exceeded, and SHALL NOT reach any mount.

The hierarchy SHALL likewise refuse a node whose resulting depth would exceed a configured maximum. The bound on stored hierarchy depth SHALL be configured separately from the bound on request path depth, and the request bound SHALL exceed it, so that a mount created at the maximum permitted hierarchy depth can still receive requests carrying a non-empty remainder.

#### Scenario: A path at the maximum depth is matched

- **WHEN** a request arrives whose path has exactly the configured maximum number of segments
- **THEN** the request is not rejected for depth
- **AND** matching proceeds normally

#### Scenario: A path one segment over the maximum is rejected

- **WHEN** a request arrives whose path has one more segment than the configured maximum
- **THEN** the request is rejected with a client error naming the depth bound
- **AND** no mount is matched

#### Scenario: A request segment at the maximum length is accepted

- **WHEN** a request arrives containing a segment of exactly the configured maximum length in octets
- **THEN** the request is not rejected for segment length

#### Scenario: A request segment one octet over the maximum is rejected

- **WHEN** a request arrives containing a segment one octet longer than the configured maximum
- **THEN** the request is rejected with a client error naming the segment-length bound

#### Scenario: Total path length is bounded independently of depth

- **WHEN** a request arrives whose segments are each within bounds and whose count is within bounds, but whose total path length exceeds the configured maximum
- **THEN** the request is rejected with a client error naming the total-length bound

#### Scenario: Depth bound applies to creation

- **WHEN** a caller creates a node whose resulting depth would be one segment beyond the configured maximum hierarchy depth
- **THEN** the creation is refused

#### Scenario: A mount at maximum hierarchy depth still serves sub-paths

- **WHEN** a mount point exists at the maximum permitted hierarchy depth
- **AND** a request arrives extending that mount path by one or more segments
- **THEN** the request is not rejected for depth
- **AND** it matches that mount with a non-empty remainder

### Requirement: Traversal sequences are rejected without decoding

The system SHALL reject, before any mount is matched, a request whose received path contains a segment consisting solely of one or two full stops, or contains a null octet in literal form. The system SHALL NOT sanitise such a path and proceed.

Rejection SHALL be decided on the path exactly as received. The system SHALL NOT percent-decode a request path in order to look for a traversal sequence, and SHALL NOT reject a request because a percent-encoded octet within one of its segments would, if decoded, be a separator, a full stop, or a null octet. Percent-encoded octets are opaque segment content; decoding them in order to inspect them would destroy the request targets this system exists to carry, and no hop between the edge and the backend decodes them.

The mount boundary SHALL be enforced structurally rather than by inspecting for escape attempts: because the forwarded remainder is produced by removing the matched prefix from the received path and by no other operation, the remainder SHALL always be a suffix of the received path, and no path content SHALL be capable of moving a request out of the matched mount's namespace.

#### Scenario: Literal parent segment is rejected

- **WHEN** a request path contains a segment consisting of two full stops
- **THEN** the request is rejected before matching
- **AND** no mount is matched

#### Scenario: Literal current-directory segment is rejected

- **WHEN** a request path contains a segment consisting of a single full stop
- **THEN** the request is rejected before matching

#### Scenario: A percent-encoded separator is carried, not rejected

- **WHEN** a request path contains a percent-encoded separator inside a segment
- **THEN** the request is not rejected
- **AND** the encoded octet reaches the matched mount's remainder still encoded

#### Scenario: A percent-encoded dot segment is carried, not rejected

- **WHEN** a request path contains a segment whose full stops are expressed in percent-encoded form
- **THEN** the request is not rejected
- **AND** the segment is neither decoded nor resolved
- **AND** it reaches the matched mount's remainder in the form received

#### Scenario: Null octet is rejected

- **WHEN** a request path contains a literal null octet
- **THEN** the request is rejected before matching

#### Scenario: A legitimate full stop is not rejected

- **WHEN** a request path contains a segment with a single full stop inside a filename-like name
- **THEN** the request is not rejected
- **AND** matching proceeds normally

#### Scenario: The remainder cannot escape the mount

- **WHEN** any accepted request matches a mount
- **THEN** the computed remainder is a suffix of the received path
- **AND** the concatenation of the matched mount path and the remainder reproduces the received path exactly

### Requirement: The full path is derived, never supplied

The full path of a node SHALL be derived from the sequence of segments of its ancestors and itself. A caller SHALL NOT be able to set a node's full path directly, and a full path supplied by a caller SHALL be ignored rather than honoured.

Derivation SHALL be performed by the durable store at write time so that the stored full path and the stored hierarchy can never disagree.

#### Scenario: Full path is computed from ancestors

- **WHEN** a node is created under a parent
- **THEN** its full path is the parent's full path followed by a separator and the node's own segment

#### Scenario: A supplied full path is ignored

- **WHEN** a caller supplies a full path that contradicts the parent and segment given
- **THEN** the stored full path is the derived one
- **AND** the supplied value has no effect

#### Scenario: Root-level derivation

- **WHEN** a node is created with no parent
- **THEN** its full path is a separator followed by its own segment

### Requirement: Renaming or moving a subtree propagates atomically

When a node's segment changes or its parent changes, the system SHALL recompute the full path of that node and of every descendant, as one atomic change to the durable state. A reader of the durable state SHALL NOT observe a state in which some descendants carry the old prefix and others the new.

The terminal-mount invariant, the uniqueness obligations, and the depth bound SHALL be re-evaluated against the destination before the change is accepted.

A moved or renamed mount point SHALL become matchable at its new full path and SHALL cease to be matchable at its old one within the effectiveness bound this capability places on the lookup surface. During that window the old path MAY continue to match the moved mount; the old path SHALL NOT match any other mount, and there SHALL be no instant at which the mount is unmatchable at both its old and its new path.

#### Scenario: Durable rename is atomic

- **WHEN** a node's segment changes
- **THEN** the durable change to that node and to every descendant's full path commits as one unit
- **AND** a concurrent reader of the durable state sees the change either entirely or not at all

#### Scenario: Descendant full paths follow an ancestor rename

- **WHEN** an ancestor's segment is changed
- **THEN** every descendant's stored full path begins with the new ancestor prefix
- **AND** no descendant retains the old prefix

#### Scenario: No partially-renamed subtree is observable

- **WHEN** a subtree with many descendants is renamed
- **AND** a reader inspects the durable hierarchy while the change is in progress
- **THEN** the reader sees either every descendant under the old prefix or every descendant under the new one

#### Scenario: A move that would violate the invariant is refused

- **WHEN** a subtree is moved under a node that is a mount point
- **THEN** the move is refused
- **AND** no full path is recomputed

#### Scenario: A move that would collide is refused

- **WHEN** a subtree is moved to a destination where a live sibling already has the same segment
- **THEN** the move is refused with a uniqueness error
- **AND** the subtree keeps its original location

#### Scenario: A renamed mount is never unreachable at both paths

- **WHEN** a mount point is renamed
- **AND** requests for its old and its new full path are issued continuously across the change
- **THEN** at every instant at least one of the two paths matches the mount
- **AND** the old path never matches a different mount
- **AND** once the change is effective, only the new path matches it

### Requirement: Names are unique among live siblings and full paths are unique

Among the live children of one parent, no two nodes SHALL share a segment. Among all live nodes, no two SHALL share a full path. Both obligations SHALL be enforced by the durable store.

Uniqueness of a full path SHALL be global rather than per tenant: a path is allocated to the first tenant that claims it, and a later claim by another tenant SHALL be refused. A refusal caused by a collision with a node the caller is not entitled to see SHALL NOT disclose that node's owner, tenant, or any other attribute of it.

A soft-deleted node SHALL NOT participate in either uniqueness test, and SHALL therefore never prevent the creation of a live node with the same segment under the same parent or with the same full path.

#### Scenario: Duplicate sibling segment is refused

- **WHEN** a caller creates a node with the same segment as a live sibling
- **THEN** the creation is refused with a uniqueness error naming the segment attribute

#### Scenario: A soft-deleted name may be reused

- **WHEN** a node is soft-deleted
- **AND** a caller creates a new node with the same segment under the same parent
- **THEN** the creation succeeds
- **AND** the new node is distinct from the soft-deleted one

#### Scenario: Repeated delete-and-recreate does not accumulate blockers

- **WHEN** the same segment is created and soft-deleted many times under one parent
- **THEN** each subsequent creation succeeds
- **AND** no soft-deleted entry blocks reuse

#### Scenario: Root-level names are unique

- **WHEN** a caller creates a root-level node whose segment matches a live root-level node
- **THEN** the creation is refused with a uniqueness error

#### Scenario: A collision with another tenant's node does not disclose it

- **WHEN** a caller creates a root-level node whose segment matches a live node belonging to a different tenant
- **THEN** the creation is refused with a uniqueness error
- **AND** the refusal does not disclose the owner, tenant, or any attribute of the existing node

### Requirement: Deletion cascades to descendants and dependent routing state

Soft-deleting a node SHALL soft-delete every live descendant in the same atomic change. Soft-deleting a mount point SHALL additionally deactivate every dependent record whose only purpose is to make that mount reachable or to authorise reaching it, including host mappings that target it.

After deletion completes, no dependent record SHALL continue to make the deleted mount reachable, and no deactivated dependent record SHALL continue to occupy a uniqueness constraint that would prevent an equivalent record being created for a different mount.

#### Scenario: Descendants are deleted with their ancestor

- **WHEN** a node with a subtree of descendants is soft-deleted
- **THEN** every live descendant is soft-deleted in the same change
- **AND** none of them is matchable afterwards

#### Scenario: A deleted mount stops matching

- **WHEN** a mount point is soft-deleted
- **THEN** requests that previously matched it no longer match it once the change is effective
- **AND** the result is an explicit no-match rather than a failure to reach a sidecar

#### Scenario: Host mappings do not survive their mount

- **WHEN** a mount point that is the target of a host mapping is soft-deleted
- **THEN** the host mapping is deactivated in the same change
- **AND** requests arriving on that host no longer reach the deleted mount

#### Scenario: A deactivated dependent releases its uniqueness key

- **WHEN** a mount point with a host mapping is soft-deleted
- **AND** a caller creates the same host mapping targeting a different mount point
- **THEN** the creation succeeds
- **AND** the deactivated mapping does not block it

#### Scenario: Cascade is all-or-nothing

- **WHEN** a cascade fails partway through
- **THEN** no node and no dependent record is left deleted
- **AND** the hierarchy is exactly as it was before the attempt

### Requirement: A routing change never retroactively alters an exchange already dispatched

A change to the hierarchy — creating, renaming, moving, deleting, or restoring a node, or changing which mount a host mapping targets — SHALL determine which mount subsequent requests match, and SHALL NOT alter the destination, the remainder, or the outcome of an exchange already dispatched to a sidecar. An exchange in flight when its mount is deleted SHALL continue under the mount it was dispatched against and SHALL end by its own completion, its own bounds, or the loss of its sidecar, rather than being failed because the mount was removed.

Requests arriving after the change becomes effective SHALL NOT match a deleted mount, and SHALL NOT match a moved mount at its old path once the change is effective. Long-lived exchanges SHALL therefore be capable of outliving the configuration that admitted them, and this SHALL be observable rather than surprising: while any exchange dispatched against a deleted mount remains in flight, the mount SHALL remain identifiable to an operator as retired-with-work-outstanding.

#### Scenario: Deletion does not kill an in-flight exchange

- **WHEN** an exchange has been dispatched to a sidecar for a mount
- **AND** that mount is deleted while the exchange is still transferring
- **THEN** the exchange continues
- **AND** it ends by completion, by one of its own bounds, or by the loss of its sidecar
- **AND** no failure is recorded whose cause is the deletion

#### Scenario: New requests stop matching immediately after effectiveness

- **WHEN** a mount is deleted while a long-lived exchange against it is in flight
- **AND** a new request for the same path arrives after the change is effective
- **THEN** the new request receives an explicit no-match
- **AND** the in-flight exchange is unaffected

#### Scenario: A retired mount with work outstanding is visible

- **WHEN** a mount has been deleted and an exchange dispatched against it is still in flight
- **THEN** an operator can determine that the deleted mount still has work outstanding and how much
- **AND** the mount ceases to be reported that way once its last exchange ends

#### Scenario: A rename does not move an in-flight exchange

- **WHEN** a mount is renamed while an exchange against it is in flight
- **THEN** the in-flight exchange's remainder and destination are unchanged
- **AND** requests arriving after the change is effective are matched at the new path

### Requirement: Recovery of a deleted path does not transfer ownership

Creating a node whose segment and parent match a soft-deleted node SHALL NOT restore that soft-deleted node. The operation SHALL either create a new, distinct node owned by the caller, or be refused; in neither case SHALL the caller acquire any grant, credential, dependent record, or history belonging to the soft-deleted node.

Restoring a soft-deleted node SHALL be a separate, explicitly named operation available only to a principal that already holds an ownership grant on that node. A lookup performed while deciding whether to create or restore SHALL be scoped to the acting principal's own entitlements.

#### Scenario: Creating over another owner's deleted path does not restore it

- **WHEN** one tenant's node is soft-deleted
- **AND** a different principal creates a node with the same segment under the same parent
- **THEN** a new distinct node is created
- **AND** the soft-deleted node remains soft-deleted
- **AND** the creating principal receives no grant on the soft-deleted node

#### Scenario: Credentials of a deleted path do not follow a new owner

- **WHEN** a soft-deleted mount point still has unrevoked credentials issued against it
- **AND** a different principal creates a node at the same location
- **THEN** those credentials do not authorise anything against the new node
- **AND** the original grants are not reassigned

#### Scenario: Restore is a distinct authorised operation

- **WHEN** a principal holding an ownership grant on a soft-deleted node invokes the restore operation
- **THEN** the node is restored with its original ownership intact

#### Scenario: Restore is refused to a principal without a grant

- **WHEN** a principal without an ownership grant invokes the restore operation on a soft-deleted node
- **THEN** the operation is refused
- **AND** the refusal does not disclose whether the node exists

### Requirement: The lookup surface converges to durable state without operator action

Matching SHALL NOT require a synchronous read of the durable store: a lookup SHALL complete, using the most recently loaded routing state, while the durable store is unreachable. That lookup surface SHALL satisfy the following observable properties.

A committed change to a mount point SHALL become effective within a configured bound, whether or not any change notification was delivered, and the bound SHALL hold with no notification mechanism present at all. The lookup surface SHALL converge to the durable state without operator action after a missed, malformed, duplicated, or out-of-order notification, and after a modification made directly to the durable store by something other than the application. A reader performing a lookup SHALL never observe an empty lookup surface, nor one missing an entry that was present both before and after a refresh. The lookup surface SHALL be reconstructible from the durable state alone, and a reconstructed one SHALL produce the same matching results as one maintained incrementally.

Making one tenant's change effective SHALL NOT interrupt or delay lookups for other tenants, and SHALL NOT require reading or re-comparing the routing state of tenants whose mounts did not change.

#### Scenario: A committed change becomes effective within a bound

- **WHEN** a mount point is created and committed
- **THEN** within the configured bound a request for its path matches it
- **AND** this holds with the notification mechanism disabled

#### Scenario: The lookup surface repairs itself after an external change

- **WHEN** mount points are modified in the durable store by something other than the application
- **THEN** the lookup surface converges to the durable state within the configured bound
- **AND** no operator action is required

#### Scenario: A reader never sees an empty lookup surface

- **WHEN** a refresh replaces the lookup surface contents
- **AND** lookups run continuously throughout the refresh
- **THEN** every lookup for a mount that existed before and after the refresh matches
- **AND** no lookup observes an empty or partially-populated surface

#### Scenario: Reconstruction reproduces the maintained results

- **WHEN** the lookup surface is discarded and reconstructed from the durable state
- **THEN** it produces the same match, remainder, and no-match outcomes as the one that was being maintained

#### Scenario: A duplicate or malformed notification is harmless

- **WHEN** a change notification is delivered twice, out of order, or in a form the reader cannot interpret
- **THEN** the lookup surface still converges to the durable state
- **AND** no lookup returns an incorrect mount in the meantime

#### Scenario: Lookups survive an unreachable durable store

- **WHEN** the durable store becomes unreachable
- **THEN** requests for mounts present before it became unreachable continue to match
- **AND** no lookup blocks waiting on the durable store

#### Scenario: One tenant's change does not disturb another's lookups

- **WHEN** one tenant changes a mount point
- **THEN** lookups for other tenants continue to be served without interruption
- **AND** their results are unaffected

#### Scenario: Refresh work does not scale with the whole installation

- **WHEN** one tenant changes a single mount point in an installation holding mounts for many tenants
- **THEN** the work performed to make that change effective does not include reading or re-comparing the mounts of tenants whose state did not change
- **AND** the same measurement is unchanged when the number of unrelated tenants is increased

### Requirement: The lookup surface of every instance converges, and divergence between instances is bounded and observable

Every instance that matches requests SHALL hold a lookup surface of its own, and the configured effectiveness bound SHALL be met by each of them independently, measured from the commit of the change. It SHALL NOT be satisfied by the change becoming effective only at the instance through which it was made, and SHALL NOT require a request to be directed at an instance in order for the change to become effective there. Adding instances to the installation SHALL NOT lengthen the bound.

Until that bound has elapsed, two instances MAY match the same request path to different mounts, or one match it and another not. That window is the only divergence permitted, and within it the result an instance returns SHALL correspond to a state the durable store actually held — the state before the committed change or the state after it — never to a combination of the two, and never to a state derived from a partially applied change. After the bound has elapsed with the durable store reachable, no two instances SHALL disagree about any mount.

A deletion, a rename, and a subtree move SHALL become ineffective at every instance under the same bound as a creation. A mount that has been deleted SHALL NOT continue to match at any instance once the bound has elapsed, and an instance SHALL NOT keep serving a deleted mount on the ground that it was not the instance the deletion was made through.

Divergence SHALL be observable rather than inferred from traffic. For each instance an operator SHALL be able to retrieve, from any instance's operational surface, both the age of that instance's last successful refresh and an identifier of the committed routing state its surface reflects, so that instances serving different states are distinguishable from instances serving the same one. That answer SHALL obey the coverage rule `operability/observability` states for an answer spanning the installation: an instance whose contribution is missing SHALL be named rather than reported as agreeing.

An instance that starts or rejoins SHALL NOT match requests from an empty or partially built lookup surface: it SHALL build one from the durable state, SHALL report itself not ready until it has, and once ready SHALL match every mount committed before it started without any change notification being re-delivered for them.

The bound in this requirement is the time a committed change takes to become effective everywhere; the staleness bound in the requirement below is the age at which an instance stops presenting itself as able to serve. Both SHALL hold, and neither SHALL be substituted for the other.

#### Scenario: A change made through one instance becomes effective at every instance

- **WHEN** a mount point is created through one instance of a multi-instance installation
- **AND** no request is directed at the other instances in the meantime
- **THEN** within the configured bound a request for its path matches it at every instance
- **AND** this holds with the change notification mechanism disabled

#### Scenario: A deletion does not survive at another instance

- **WHEN** a mount point is deleted through one instance
- **THEN** within the configured bound no instance matches a request to it
- **AND** no instance continues to serve it on the ground that the deletion was made elsewhere

#### Scenario: Divergence within the window is to a state that was committed

- **WHEN** a subtree is moved and the same request path is matched repeatedly at every instance throughout the effectiveness bound
- **THEN** each result corresponds either to the hierarchy as committed before the move or to the hierarchy as committed after it
- **AND** no result combines the two, and none names a path that neither state contained

#### Scenario: Instances agree once the bound has elapsed

- **WHEN** a series of creations, renames and deletions is committed and the effectiveness bound then elapses with the durable store reachable from every instance
- **THEN** the same request path yields the same match and the same remainder at every instance
- **AND** no instance reports a mount that another does not

#### Scenario: Which state each instance is serving is retrievable

- **WHEN** an operator queries any instance for the routing state each instance's lookup surface reflects
- **THEN** the answer reports, per instance, the age of its last successful refresh and an identifier of the committed state it reflects
- **AND** two instances reflecting different committed states are distinguishable from two reflecting the same one
- **AND** an instance whose contribution could not be obtained is named rather than reported as agreeing

#### Scenario: A joining instance serves mounts committed before it existed

- **WHEN** an instance is added to an installation that already holds many mount points
- **THEN** it reports itself not ready until its lookup surface is built from the durable state
- **AND** once ready it matches every mount committed before it started
- **AND** no change notification is re-delivered for those mounts in order for it to do so
- **AND** it never matches a request from a partially built surface

### Requirement: Staleness of the lookup surface is observable and bounded

The system SHALL record the time of the last successful refresh of the lookup surface and SHALL make it observable to an operator, together with the outcome of the most recent refresh attempt. A failed refresh SHALL be recorded with a machine-readable reason and SHALL NOT be silently retried without record.

When the age of the last successful refresh exceeds a configured bound, the instance SHALL surface the condition: it SHALL report itself not ready to receive new traffic and SHALL emit an operator-visible signal identifying stale routing state as the cause. The system SHALL NOT continue to serve from an unrefreshable lookup surface indefinitely without surfacing that it is doing so.

A stale lookup surface SHALL nevertheless continue to serve the state it last loaded successfully. The system SHALL NOT discard, empty, or partially clear it because a refresh failed or because it has become stale; withdrawing routes is a worse failure than serving known-good ones while the condition is visible.

Recovery SHALL NOT require a restart: once a refresh succeeds, readiness SHALL be restored automatically and the recorded refresh age SHALL reset.

#### Scenario: Refresh age is observable

- **WHEN** an operator inspects the routing subsystem
- **THEN** the age of the last successful refresh of the lookup surface is reported
- **AND** the outcome of the most recent refresh attempt is reported

#### Scenario: Failed refresh is recorded with a reason

- **WHEN** a refresh attempt fails because the durable store is unreachable
- **THEN** the failure is recorded with a machine-readable reason
- **AND** the last-successful-refresh age continues to grow

#### Scenario: Staleness beyond the bound withdraws readiness

- **WHEN** no refresh has succeeded for longer than the configured staleness bound
- **THEN** the instance reports itself not ready
- **AND** an operator-visible signal identifies stale routing state as the cause

#### Scenario: Stale service is never silent

- **WHEN** the lookup surface cannot be refreshed for an extended period
- **THEN** the condition is surfaced continuously for as long as it persists
- **AND** requests are not served from the stale state without the condition being observable

#### Scenario: Staleness does not empty the routing state

- **WHEN** refreshes have been failing for longer than the configured staleness bound
- **THEN** mounts present at the last successful refresh continue to match
- **AND** the lookup surface is neither cleared nor partially cleared
- **AND** no request receives a no-match that would have matched before the failures began

#### Scenario: Readiness returns without a restart

- **WHEN** the durable store becomes reachable again after a staleness period
- **AND** a refresh succeeds
- **THEN** the instance reports itself ready again
- **AND** no restart was required
