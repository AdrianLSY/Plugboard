---
type: glossary
status: current
authority: rationale
---

# Glossary

Every domain term the sixteen specifications use in a defining sense, with a link to the artifact
that fixes it.

**This note fixes nothing.** Each entry is a pointer with a gloss attached: the specification named
on the entry owns the term, and where a gloss here and that specification disagree, the
specification wins. Terms fixed by a decision rather than by a specification carry the decision note
too. Read [start-here](start-here.md) for the precedence order this sits inside.

Terms the set uses but never defines are in [gaps](#gaps--terms-nothing-defines), and terms it uses
in more than one sense are in [collisions](#collisions--terms-used-in-two-senses). Those two
sections are the point of the extraction pass, not an appendix to it: a term used in a defining
sense by one capability and in a different sense by another is a defect the same size as an
undefined one.

## The vocabulary triple

Fixed by [D20](decisions/d20-multi-instance.md), and stated for the whole set in
[`tenancy/isolation`'s Purpose](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#purpose).

**instance** — one running process of a deployable. Qualified as a *proxy instance* where it has to
be told apart from a sidecar or from the client-facing terminator.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#purpose) ·
[D20](decisions/d20-multi-instance.md)

**installation** — the whole set of instances under one operator's configuration. Obligations about
what an operator can see, and every per-tenant ceiling, are stated for the installation and not for
whichever instance a query reached.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#purpose) ·
[D20](decisions/d20-multi-instance.md)

**node** — an entry in the mount-point path hierarchy, and never a running process. A node has at
most one parent, belongs to exactly one tenant, and carries a flag saying whether it is a mount
point.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-paths-form-a-single-parent-hierarchy) ·
[D20](decisions/d20-multi-instance.md)

**deployable** — a member of the enumerated set of separately deployed components. The enumeration
lives in one place and every other capability refers to it rather than keeping a component list.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose)

**client-facing terminator** — the deployable that terminates client-facing protocols, made separate
by [D16](decisions/d16-http2-to-clients.md). The wire contract calls the role it holds the
client-facing role; edge hygiene states its obligations against whichever component terminates the
client connection; packaging records that these are three names for one component.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose) ·
[`proxy/edge-hygiene`](../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md#requirement-these-obligations-bind-whichever-component-terminates-the-client-connection)

**sidecar** — the program a tenant runs inside their own infrastructure, which dials out to the
listener and originates requests against the tenant's backend from local configuration alone. Its
specification defines it as a program rather than as a peer that speaks the contract.
[`sidecar/program`](../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#purpose)

## Routing

**mount point** — a node eligible to receive proxied traffic. A node that exists but is not a mount
point is reachable by no request. Ten of the sixteen specifications shorten this to *mount*; see
[collisions](#collisions--terms-used-in-two-senses).
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-paths-form-a-single-parent-hierarchy)

**terminal** — the property that a mount point has no children, enforced from both directions. This
is what makes longest-prefix matching provably unambiguous, which is why it is an obligation rather
than a convention.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-mount-points-are-terminal)

**remainder** — the request path with exactly the matched mount path removed from its front, derived
by removal only. It is the sole input from which the backend request is composed.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-the-forwarded-remainder-is-the-request-target-minus-the-mount-prefix) ·
[`proxy/http-fidelity`](../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-the-backend-request-is-derived-only-from-the-mount-remainder)

**longest-prefix match** — the rule by which an inbound request is matched to at most one mount, on
undecoded segment boundaries.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-a-request-matches-at-most-one-mount-by-longest-prefix)

**reserved path** — a prefix served by the proxy itself rather than by a mount. The enumeration of
them is closed, is held in one place for the installation, and is not extendable by a tenant; every
capability needing one contributes its prefix there.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-the-proxys-own-namespace-is-not-mountable) ·
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-listeners-namespace-is-reserved-in-the-single-reserved-enumeration)

**lookup surface** — the routing state an instance matches requests against without a synchronous
read of the durable store. Every instance holds one; convergence, divergence and staleness are
stated for the installation.
[`routing/mount-points`](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-the-lookup-surface-converges-to-durable-state-without-operator-action)

**routing entry** — a node in the path hierarchy, whether or not it is a mount point. The word the
role model grants authority on.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#purpose)

**hostname claim** — the association of exactly one hostname with exactly one mount, owned by the
tenant that owns the mount. A hostname resolves to at most one mount at any instant across all
tenants.
[`routing/custom-domains`](../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md#requirement-a-hostname-claim-names-one-mount)

**verified claim** — a claim whose hostname ownership has been established. Until then the claim
confers nothing: no traffic served, no certificate requested.
[`routing/custom-domains`](../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md#requirement-a-claim-confers-nothing-until-ownership-is-verified)

**verification challenge** — the unpredictable value bound to one claim that a claimant answers to
prove control of the hostname. The responder answering it belongs to the edge, never to a tenant.
[`routing/custom-domains`](../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md#requirement-verification-challenges-are-unpredictable-and-bound-to-one-claim)

**wildcard claim** — a claim covering a hostname's subordinate names, provable by delegation only,
and losing to an exact match wherever both apply.
[`routing/custom-domains`](../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md#requirement-wildcard-claims-are-proved-by-delegation-only)

**affinity key** — an optional opaque octet string carried on a request, derived by the proxy under
a policy configured on the matched mount. It cannot name a sidecar, a tunnel, an instance or a
tenant.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-requests-carry-an-affinity-key)

**affinity binding** — the registry's mapping from an affinity key to the entry serving it: scoped
to one tenant and one mount, honoured from every instance, released when its entry becomes
ineligible.
[`tunnel/sidecar-registry`](../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-affinity-bindings-are-registry-state-with-a-bounded-lifetime)

## Tenancy and authority

**tenant** · **tenancy** — the isolation boundary. The isolation capability fixes *tenancy* as the
same boundary the rest of the set calls a *tenant*; both words are therefore in the set on purpose.
Every resource belongs to exactly one.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-every-resource-belongs-to-exactly-one-tenancy) ·
[D8](decisions/d08-tenant-scoping.md)

**principal** — the actor an operation is performed on behalf of. Reads are scoped to the requesting
principal's tenancy, and no mutation is reachable without one; the set distinguishes a *tenant
principal* from an *operator principal*. What a principal *is* is not itself defined — see
[gaps](#gaps--terms-nothing-defines).
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-every-read-is-scoped-to-the-requesting-principals-tenancy)

**acting principal** — the principal a credential operation is authorised against, required for
every one of them and recorded on what it produces.
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-every-credential-operation-is-authorised-against-an-acting-principal)

**role** — a named grant on a routing entry, from a model of at least owner, maintainer and viewer,
each with stated and bounded authority, inherited down the mount hierarchy.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-roles-carry-defined-and-bounded-authority)

**occupancy dimension** — one of the enumerated things a tenant's *traffic* holds: concurrent
exchanges, concurrent long-lived streams, octets in flight, octets buffered, and admission rate.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-per-tenant-resource-bounds-are-enforced-on-every-dimension) ·
[`proxy/http-fidelity`](../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-long-lived-exchanges-are-admitted-against-occupancy-not-arrival-rate)

**standing-resource dimension** — one of the enumerated things a tenant may hold whether or not
traffic flows, contributed to the same closed enumeration by the capability that owns the resource.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-per-tenant-resource-bounds-are-enforced-on-every-dimension)

**bound** — a configured ceiling on one dimension. There is no single definition of the word; what
is fixed is that the per-tenant enumeration is closed, that a per-tenant bound is one value for the
installation, and that accounting it per instance is a closed exception a capability must claim and
justify.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-a-per-tenant-bound-is-one-value-for-the-installation-not-one-value-per-instance) ·
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-per-instance-accounting-is-a-closed-and-justified-exception)

**audit trail** — the append-only record of every mutation, one trail for the installation with a
stated ordering, readable within its own scope.
[`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-every-mutation-is-recorded-in-an-audit-trail)

## The tunnel

**tunnel** — the persistent connection a sidecar dials out to the listener, over which the versioned
contract is spoken. It is held by exactly one instance, and nothing on the wire names an instance or
reveals how many there are.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#purpose) ·
[the tunnel](how/the-tunnel.md)

**listener** — the endpoint a sidecar dials. It presents a verifiable endpoint identity, protects the
connection before anything is read, serves establishment and nothing else, and occupies a reserved
prefix.
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-listener-presents-a-verifiable-endpoint-identity-on-every-connection) ·
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-listener-serves-establishment-and-nothing-else)

**frame** — the unit of transfer on the tunnel: a fixed-shape header carrying a kind, a stream
identifier and a length, so a receiver that does not know the kind can still find the next
boundary. Not a message carrying a whole request or response.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-framed-exchange-with-stream-identifiers) ·
[D2](decisions/d02-frame-shaped-tunnel.md)

**exchange** — the work carried on one stream. Every admitted exchange produces exactly one outcome
record when it ends, including an established bidirectional-stream session.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-framed-exchange-with-stream-identifiers) ·
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-exchange-produces-exactly-one-outcome-record)

**stream identifier** — the value scoping a frame to an exchange, drawn from disjoint sets per side,
strictly increasing, never reused within a connection, and meaningless once the connection ends.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-stream-identifiers-are-allocated-scoped-and-never-reused)

**correlation identifier** — the proxy-assigned, contract-opaque value carried on the request head
that spans a whole exchange, distinct from the stream identifier precisely because that one says
nothing after its connection ends.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-exchanges-carry-a-correlation-identifier-distinct-from-the-stream-identifier) ·
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-one-correlation-identifier-spans-the-whole-exchange)

**client-facing role** · **origin-facing role** — the contract's two roles: the side an exchange
originates at, and the side that originates it against a backend. Obligations bind roles rather than
components, so either end can be substituted.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-the-contract-defines-two-roles-and-a-client-edge-speaker-occupies-one-of-them)

**datagram** — a frame kind whose delivery is not guaranteed and which takes no part in flow control,
carrying the identifier of the bidirectional-stream session it belongs to.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-datagram-class-is-defined-and-reserved)

**registry entry** — one record per established tunnel — not per sidecar deployment, host or mount —
carrying the tenant, the single admitted mount, the negotiated version, the declared capability set,
a proxy-assigned distinguishing identifier, and the instance holding the tunnel.
[`tunnel/sidecar-registry`](../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-a-registry-entry-describes-one-tunnel)

**eligibility** — the property of being selectable to serve a mount. It begins and ends with the
tunnel, and is filtered by capability before selection rather than after.
[`tunnel/sidecar-registry`](../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-eligibility-begins-and-ends-with-the-tunnel) ·
[`tunnel/sidecar-registry`](../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-eligibility-is-filtered-by-capability-before-selection-not-after)

**observed source** — the origin of a connection as derived from the connection itself, never from
anything the peer states. Every pre-authentication bound keys on it, which is why it is defined
where no authenticated identity yet exists.
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-observed-source-of-a-connection-is-derived-from-the-connection-never-claimed-by-the-peer)

**connection phase** — the enumerated state a held connection is attributable to while it is open,
from accepted through to ended. It exists so a sidecar that never authenticates is still visible to
an operator.
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-every-connection-is-attributable-to-an-enumerated-phase-while-it-is-open)

## Capability and conformance

**capability** — in the contract's sense, an optional behaviour whose availability each side declares
at establishment, named by a stable published identifier rather than by prose. The word has a second
sense across the set; see [collisions](#collisions--terms-used-in-two-senses).
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-capability-declaration) ·
[D3](decisions/d03-capability-negotiation.md)

**baseline** — the behaviours every implementation of a contract version supports without declaring
them, as distinct from optional capabilities. Declaring a baseline behaviour unsupported is refused
and no tunnel is established.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-capability-declaration)

**refusal** — the answer to a request the negotiated capability set cannot back: an enumerated,
stated reason rather than a reduced-fidelity attempt. The set's alternative to degradation.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-refusal-rather-than-silent-degradation) ·
[D3](decisions/d03-capability-negotiation.md)

**contract version** — the negotiated version of the wire protocol in force on a tunnel. It is also
declared by a stopped artifact as a range, so a pairing can be judged before deployment.
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-contract-version-negotiation) ·
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-each-artifact-declares-the-contract-version-range-it-speaks-readable-without-running-it)

**conformance suite** — the independently executable artifact that is the authority on the contract,
obtainable and runnable by a third party against their own implementation.
[`tunnel/conformance`](../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md#requirement-the-suite-is-an-independently-executable-artifact) ·
[D23](decisions/d23-contract-first.md)

**implementation under test** — the one component of a run whose behaviour the suite does not
control; it supplies every other party. The task list's *conformance subject* is this term — see
[gaps](#gaps--terms-nothing-defines).
[`tunnel/conformance`](../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md#requirement-the-suite-supplies-every-party-except-the-subject)

**run** — one execution of the suite, scoped to a single contract version and a declared capability
set, with a verdict that does not depend on the subject's instance topology.
[`tunnel/conformance`](../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md#requirement-a-run-is-scoped-to-one-contract-version)

**declaration-based skip** — the only admissible skip: a case not run because the subject did not
declare the capability it covers, and reported distinctly from a failure.
[`tunnel/conformance`](../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md#requirement-declaration-based-skips-are-distinct-from-failures-and-are-the-only-skips)

## Credentials and key material

**credential** — the proof a sidecar presents that it is entitled to serve one mount for one tenant.
Bound to that scope at issuance, never widened afterwards, and never issuable without an expiry.
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-a-credential-is-scoped-to-one-mount-and-one-tenant)

**issuing credential** — the distinct, bounded credential class used for automated issuance, whose
minted credentials inherit its scope, cannot exceed it, and record it as their issuer. This, not a
*service account*, is the set's term for a non-human issuer.
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-automated-issuance-uses-a-distinct-bounded-credential-class) ·
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-minted-credentials-are-attributable-to-their-issuer)

**presentation** — the single point at which a credential's secret is shown and expiry is enforced.
Authentication binds to the tunnel rather than to individual requests.
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-the-secret-is-presented-exactly-once) ·
[`auth/sidecar-credentials`](../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-authentication-binds-to-the-tunnel-not-to-individual-requests)

**credential store** — on the sidecar's side, one configured location, exclusively held, with three
distinguishable states. It is also the sidecar's only footprint on the tenant's machine.
[`sidecar/program`](../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-credential-store-is-one-configured-location-exclusively-held-with-three-distinguishable-states)

**custody class** — one entry in the closed inventory of cryptographic material the installation
holds, stating its purpose, who may replace it, whether it is required to start, and whether a
holder may obtain the material or only have operations performed with it.
[`security/key-custody`](../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-the-inventory-of-custody-managed-material-is-enumerated-and-closed)

**protection material** — the material that makes other material unusable to a reader of the store
alone. It is purpose-separated, versioned, and does not live where what it protects lives.
[`security/key-custody`](../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-protection-material-does-not-live-where-the-protected-material-lives) ·
[`security/key-custody`](../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-derivation-is-purpose-scoped-and-versioned-for-every-class)

**root material** — operator-supplied material not recoverable from anything the platform stores.
There is no escrow: unrecoverable material is reported rather than worked around.
[`security/key-custody`](../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-root-material-is-operator-supplied-and-is-not-recoverable-from-anything-the-platform-stores)

## The edge

**hop** — one connection in the chain an exchange crosses. The set names three of them: the *client
hop*, the tunnel, and the *backend hop*. Framing, masking, compression and liveness are properties
of a hop rather than end-to-end facts, regenerated per hop and never relayed.
The word itself is defined nowhere; only the three named hops are.
[`proxy/edge-hygiene`](../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md#requirement-message-framing-is-generated-per-hop-and-never-relayed) ·
[`proxy/websocket`](../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-backpressure-is-applied-at-the-client-hop) ·
[`sidecar/program`](../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-backend-connection-bounds-are-the-sidecars-own-and-distinct-from-the-proxys) ·
[D6](decisions/d06-framing-authority.md)

**timeout class** — the one class each route carries, determining every time bound in force for
exchanges on it. At least one class permits an unbounded total, expressible only as an explicit
choice.
[`proxy/http-fidelity`](../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-every-route-carries-a-timeout-class-and-one-class-permits-an-unbounded-total) ·
[D7](decisions/d07-timeout-taxonomy.md)

**commit point** — the response head. Once it has been emitted the proxy can no longer answer with an
error of its own, which is where the line falls between a generated error and a truncation.
[`proxy/http-fidelity`](../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-the-response-head-is-the-commit-point)

**cause** — the distinct, enumerated reason recorded for a terminating condition. Every cause in the
system maps to exactly one outcome value.
[`proxy/http-fidelity`](../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-every-terminating-condition-is-recorded-with-a-distinct-cause) ·
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-enumerated-cause-in-the-system-maps-to-exactly-one-outcome-value)

**mount-boundary rewriting** — the reconciliation of a tenant's mount prefix with a backend that
believes it is at a root, applied under an explicit per-content-type policy and bounded so it does
not defeat incremental transfer.
[`proxy/edge-hygiene`](../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md#requirement-mount-boundary-rewriting-has-an-explicit-per-content-type-policy)

**bidirectional stream** — the frame-stream primitive established through a mount point, admitted at
the edge only once the backend has accepted. It is a declared capability, not a baseline one.
[`proxy/websocket`](../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-an-upgrade-is-never-accepted-before-the-backend-has-accepted) ·
[`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-bidirectional-stream-exchanges-carry-the-backend-handshake)

**close vocabulary** — the documented set of codes a proxy-originated close draws from, kept from
colliding with the tenant application's own.
[`proxy/websocket`](../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-proxy-originated-closes-come-from-a-documented-vocabulary)

## Operation and artifacts

**artifact** — in packaging's sense, the released content of one deployable for one platform
variant. The conformance suite's own distribution is an artifact in a different sense and is not a
deployable.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose)

**input** — something a build draws on, as distinct from something a request or a conformance case
supplies. Every input is pinned to an immutable identity.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose) ·
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-every-input-is-pinned-to-an-immutable-identity)

**identity** — unqualified, an artifact's verifiable content identity. The identity of a principal, a
credential or a listener endpoint belongs to another capability and is always named as such.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose)

**release gate** — a check whose recorded outcome a publication depends on, as distinct from the
validation a component performs on itself at startup. The gate set is enumerated and each release
records which it passed.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose) ·
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-gate-set-is-enumerated-and-a-release-records-which-gates-it-passed)

**provenance** — what an artifact records about its own construction, fixed when it is produced,
unalterable by any deployment, and retrievable without running it.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-provenance-is-fixed-when-the-artifact-is-produced-and-no-deployment-can-alter-it)

**pairing** — a proxy artifact and a sidecar artifact judged for viability from the artifacts alone,
before either is deployed.
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-pairing-viability-is-determinable-from-the-artifacts-alone)

**durable schema version** — the version recorded in the durable state itself, against which running
code declares a supported range. The counterpart of contract versioning for state rather than wire.
[`operability/schema-migration`](../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md#requirement-the-durable-schema-carries-its-own-version) ·
[`operability/schema-migration`](../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md#requirement-the-running-code-declares-a-supported-schema-version-range)

**migration** — an operator-initiated, immutable change to the durable shape, with a stable identity
in one total order, applied at most once, and never reachable from tenant traffic.
[`operability/schema-migration`](../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md#requirement-every-migration-has-a-stable-identity-and-one-total-order)

**liveness** — the signal that answers only whether a restart would help. It does not fail because a
dependency is unavailable, because a projection is stale, or because the instance is partitioned.
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-liveness-answers-only-whether-a-restart-would-help)

**readiness** — the distinct signal that answers whether a component should currently receive new
traffic, derived from actual dependency state and never a constant.
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-readiness-reflects-dependency-state-and-drain)

**drain** — ceasing to take new work while work already in flight continues. Each hop states its own
form of it: the listener stops accepting, a sidecar finishes in-flight exchanges, and a planned
withdrawal does not disconnect a fleet at once.
[`tunnel/listener`](../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-listener-drains-by-ceasing-to-accept-while-established-tunnels-continue) ·
[`tunnel/sidecar-registry`](../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-a-sidecar-can-drain-without-failing-its-in-flight-work)

**degraded** — an enumerable condition the installation is operating under, each entry stating what
it is, when it began, and its effect on serving, for as long as it persists.
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-degraded-operation-is-announced-for-as-long-as-it-persists)

**outcome record** — the one record an admitted exchange produces when it ends, stating an outcome
from a stable enumerated set.
[`operability/observability`](../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-exchange-produces-exactly-one-outcome-record)

**configuration schema** — the single declared enumeration of every value a component's behaviour
depends on. The sidecar's is closed; packaging owns its retrievability from a stopped artifact and
the rule that the artifact's declaration is generated from it.
[`sidecar/program`](../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-configuration-is-a-declared-schema) ·
[`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-artifacts-declared-configuration-is-generated-from-the-configuration-schema)

## Gaps — terms nothing defines

Each of these is used in a defining sense somewhere in the set, or was named as a required glossary
term, without any artifact fixing it. A gap is a finding to be closed in the owning specification,
not a definition for this note to supply.

| term | the gap |
|---|---|
| **projection** | Used across three of the sixteen specifications — isolation, observability, schema-migration — with no definition anywhere. Its meaning is reconstructible only by inference: [schema-migration](../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md#requirement-projections-are-rebuilt-across-a-schema-version-change-never-assumed-valid) treats the lookup surface as one projection among others, so a projection is a read model derived from durable state. Nothing says so normatively, and readiness, degradation and rebuild obligations all key on the word. |
| **principal** | 166 uses across eight specifications, and two kinds — tenant and operator — are distinguished in prose. Nothing fixes what a principal is, how one comes to exist, or what the closed set of kinds is. [`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-roles-carry-defined-and-bounded-authority) fixes only what a role grants one. |
| **service account** | Not a term in the set: zero occurrences across all sixteen specifications. The nearest defined thing is the **issuing credential** class. If a human-facing identity distinct from a credential is intended anywhere, no specification owns it. |
| **conformance subject** | Not a term in the set: zero occurrences. The defined term is **implementation under test**. The word *subject* does appear, but as an ordinary noun rather than a fixed term. |
| **custom domain** | The capability is named `routing/custom-domains`, and other specifications cite it as "the custom-domain capability", but no requirement inside it uses the phrase. Its defined nouns are **hostname claim** and **verified custom hostname**. A term that exists only in a directory name is a term no gate can check. |
| **terminator** | The word appears twenty times across six specifications, most of them in [packaging](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md), but no specification *fixes* it as a term. The component is named three ways in the set, reconciled deliberately at [packaging's Purpose](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose). The reconciliation is sound; what is missing is that the repository's own directory name is a fourth name nothing ties to it. |
| **bound** | The most-used word in the set with no definition. What is fixed is the closed enumeration of *per-tenant* dimensions; a bound that is not per-tenant — a header-section size, a pre-authentication hold time, a decompressed message ceiling — is stated wherever it is enforced, with no rule that every one carries a stated overflow behaviour. [`CLAUDE.md`](../CLAUDE.md) states that rule as a review blocker; no specification does. |

## Collisions — terms used in two senses

These are not errors to fix by renaming on sight; each is recorded here so a reader who meets the
second sense does not read it as the first.

| term | sense one | sense two |
|---|---|---|
| **capability** | An optional wire behaviour declared at establishment, named by a published identifier ([`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-capability-declaration)). | One of the sixteen specification units — "this capability owns…" — the sense every Purpose paragraph uses. The two are unrelated, and the phrase "the negotiation capability" means a specification while "an undeclared capability" means a wire behaviour. |
| **stream** | The multiplexing unit a frame is scoped to; every exchange runs on one ([`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-framed-exchange-with-stream-identifiers)). | The bidirectional-stream primitive — the WebSocket-class long-lived session. Isolation's occupancy dimensions bound "concurrent exchanges" and "concurrent long-lived streams" separately, so the two senses are bounded independently in one enumeration. |
| **frame** | The tunnel's own unit of transfer ([`tunnel/wire-contract`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-framed-exchange-with-stream-identifiers)). | The edge protocol's frames on the client hop, which are masked, compressed and interleaved under the client protocol's rules ([`proxy/websocket`](../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-frame-masking-is-a-property-of-a-hop)). Masking state is never relayed, so a frame in one sense never becomes a frame in the other. |
| **artifact** | The released content of one deployable for one platform variant ([`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose)). | The conformance suite's own distribution ([`tunnel/conformance`](../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md#requirement-the-suite-is-an-independently-executable-artifact)). Packaging names the collision and excludes the second from its own obligations. |
| **identity** | An artifact's verifiable content identity ([`operability/packaging`](../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#purpose)). | A principal's, a credential's, or the listener endpoint's identity. Packaging requires the second always be qualified. |
| **mount** · **mount point** | *Mount point* is the defined term, and is what distinguishes a routable node from a node that merely exists. | *Mount* is the shorthand, and is what ten of the sixteen specifications use without ever saying "mount point" — which appears in only five of them. The shorthand is unambiguous only because a mount point is terminal; a reader who has not read [mount-points](../openspec/changes/rebuild-plugboard/specs/routing/mount-points/spec.md#requirement-mount-points-are-terminal) cannot tell that "mount" excludes a non-mount node. |
| **tenant** · **tenancy** | *Tenant* is what fifteen specifications say. | *Tenancy* is what thirteen of them say, and [`tenancy/isolation`](../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#purpose) fixes the two as the same boundary. Both are in the set on purpose; neither is a subset of the other. |
| **node** | An entry in the mount-point hierarchy, and never a running process — reserved that way for the whole set by [D20](decisions/d20-multi-instance.md). | A running proxy process, in the *title* of D20 as first written — the one use of the word the decision's own body forbids. The body was right and the title was the defect: the register entry, its note and the generated index now read *multi-instance*, and the hand-written index row and topology label followed on 2026-09-12. The row stays because the old title survives in the archived changes and in history, where a reader meeting it should not read it as the first sense. |

Every count in the two tables above is a claim about tracked text, and is meant to be re-run rather
than believed:

```
cd openspec/changes/rebuild-plugboard/specs
grep -rli "<term>" . | wc -l     # how many of the sixteen use it
grep -rio "<term>" . | wc -l     # how many times
```

## Keeping this current

Task 4.1 requires that a term added to a specification and absent from this note fails. That check
does not exist yet, and until it does this list is only as current as its last extraction pass. The
extraction that produced it read the Purpose paragraph and every `### Requirement:` heading of all
sixteen specifications, then followed each candidate to the requirement body that fixes it; the same
pass reproduced from
[`openspec/changes/rebuild-plugboard/specs/`](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
is what a reviewer should re-run before trusting the gaps table.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
