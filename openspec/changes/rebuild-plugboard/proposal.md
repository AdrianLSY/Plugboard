## Why

The previous system (`reference/`, ~27k lines across an Elixir proxy and a Go sidecar) works only for `GET` requests returning text. A seven-agent audit with adversarial verification confirmed that request bodies never reach the sidecar, binary payloads are corrupted in transit, neither container boots, and the cache-invalidation mechanism has 947 lines of tests that cannot observe the event they test. These are not accumulated bugs — they are consequences of four type choices frozen into the tunnel's schema, made without planning by an LLM working in a harness that made the honest path expensive.

Rebuilding matters now because the schema is the one thing that can never be fixed later. Sidecars run in tenants' own infrastructure; the operator upgrades the proxy, tenants upgrade whenever they feel like it or never. An ordered header list added in v2 does not help the tenant still pinned to v1, and there is no mechanism to force the upgrade. Every cheap schema decision becomes permanent the day the first tenant pins a version.

## What Changes

**Positioning.** The product is dynamic ingress for multi-tenant platforms — many tenants, many simultaneously-deployed sidecar versions, hard tenant isolation as a sold promise. This makes tenant scoping and per-tenant blast radius day-one data-model decisions rather than later features.

- **BREAKING — no migration path from the reference system.** The reference is read-only prior art. Its wire protocol, schema, and deployment artifacts are not carried forward. Roughly sixty specific carry-forward items (invariants, algorithms, and small correct functions) are enumerated in `docs/` and ported deliberately.
- **One repository**, replacing two git submodules with an auto-merging pointer-update workflow that pushed unreviewed protocol changes to the parent's `main`.
- **A versioned wire contract as the root artifact**, with generated types for every implementation and an executable conformance suite. The contract stops being 17KB of prose pseudocode and becomes a machine-checked schema.
- **The tunnel exchange becomes frame-shaped**, not one-message-per-correlation-id: stream ids, credit windows, and a frame vocabulary reserved in full at v1 even where unimplemented.
- **HTTP messages become byte-faithful**: arbitrary method tokens, ordered repeated header pairs, opaque octet bodies, raw request targets, trailers, and N interim responses before one final response.
- **Incremental streaming with end-to-end backpressure**, replacing whole-response buffering. This single change unblocks SSE, HLS/LL-HLS, MPEG-DASH, gRPC-Web server streaming, and large transfers.
- **Capability negotiation at tunnel join**, so a request a connected sidecar cannot honour is refused explicitly rather than served at reduced fidelity. Round-robin across mixed-version sidecars currently makes two identical requests behave differently.
- **Custom-domain ownership verification** before certificate issuance, closing a path where a first-come unverified domain claim would escalate into obtaining a publicly trusted certificate for someone else's domain.
- **Observability that exists**: a metric sink and structured logging chosen before the hot path is written. The reference emits 75 telemetry events and attaches zero handlers.
- **Proxied traffic terminates before any application middleware**, so no body parser, method override, HEAD folding, or content negotiation can touch it.

### Non-goals

Documented refusals, not omissions:

- **WebRTC media and data channels.** SRTP and SCTP-over-DTLS over ICE-negotiated UDP; the component that relays them is a TURN server — bandwidth-priced, latency-SLA'd, a different product. WebRTC *signalling* is carried for free as an ordinary bidirectional stream.
- **Web Push with VAPID.** The tenant's app server POSTs directly to FCM or Mozilla autopush. Nothing traverses the proxy; no support is required.
- **NTLM / Negotiate to tenant backends.** Connection-bound authentication cannot work through a multiplexed tunnel.
- **TLS passthrough.** Encrypted Client Hello encrypts the single field such a mode routes on.
- **WebTransport in v1.** Designed for and reserved in the contract, shipped later as a separate HTTP/3 terminator that speaks the wire contract. Not a reason to make the tunnel QUIC.
- **Full gRPC at the ingress** in this change — no section of `tasks.md` builds an ingress gRPC path, and the gRPC-Web ↔ gRPC bridge sits in the sidecar, the one component adjacent to an HTTP/2 backend. The reason first given (`grpc-status` travels as a trailer even on success, which a Plug-based edge cannot express) was retired by D16, which replaces that edge with a contract-speaking terminator; whether the refusal survives on another ground is carried in `design.md` — Open Questions rather than re-argued here.

## Capabilities

### New Capabilities

- `tunnel/wire-contract`: the versioned frame protocol — frame vocabulary, stream ids, credit windows, the HTTP message type choices, capability negotiation, and version-skew rules across simultaneously-deployed sidecars.
- `tunnel/conformance`: the executable suite any sidecar implementation must pass, built from adversarial fixtures rather than happy paths.
- `tunnel/sidecar-registry`: sidecar registration, selection across a mount, failover, and behaviour when connected sidecars declare differing capabilities.
- `proxy/http-fidelity`: byte-faithful request/response proxying — arbitrary methods, repeated headers, opaque bodies, incremental streaming both directions, trailers, interim responses, cancellation, and the timeout taxonomy.
- `proxy/websocket`: bidirectional stream proxying — deferred 101 relaying the backend's real handshake response, frame-level fidelity, fragmentation, close codes, and subprotocol negotiation.
- `proxy/edge-hygiene`: framing authority, hop-by-hop removal, client-identity propagation, `Host`/SNI binding, and mount-boundary URL and cookie rewriting.
- `routing/mount-points`: the terminal-mount invariant and its coupling to longest-prefix matching, path validation, and the tenant-scoped projection that serves lookups.
- `routing/custom-domains`: domain affinity, ownership verification, and per-tenant certificate lifecycle including ACME challenge selection and renewal.
- `tenancy/isolation`: tenant scoping of every projection and mutation, per-tenant resource bounds, blast-radius containment, and the audit trail.
- `auth/sidecar-credentials`: sidecar tokens and service accounts — issuance, rotation, revocation, and an authentication path that does not scan every credential in the installation.
- `operability/observability`: metrics, structured logging, health and readiness probes, build provenance, and the diagnostics an operator needs to debug a stuck tunnel.
- `sidecar/program`: the sidecar as a program a tenant runs inside their own infrastructure rather than as a contract endpoint — configuration schema with fail-fast validation reporting every missing value at once, process lifecycle and signal handling, dialling the backend including path validation and the prohibition on deriving the origin from request content, the gRPC-Web to gRPC bridge that `design.md` places here, and the tenant-side delta of the artifact obligations `operability/packaging` owns for every deployable.
- `security/key-custody`: where certificate private keys and other cryptographic material live, how they are protected at rest, how they are shared across instances, and how they are rotated — the property the tenant-isolation promise rests on, which `auth/sidecar-credentials` explicitly excludes.
- `tunnel/listener`: the endpoint a sidecar dials — its transport and protocol negotiation, the identity it presents so a sidecar can verify it before offering a credential, connection and accept-path bounds, and the namespace it occupies.
- `operability/schema-migration`: versioning, forward and backward compatibility, and migration of the durable schema, so that the guarantees the wire contract makes across version skew have an equivalent for durable state.
- `operability/packaging`: the obligations common to every deployable — the proxy, the sidecar, and the edge terminator D16 introduces. A self-contained artifact per component; its packaged environment generated from the same schema its startup validation reads, so the two cannot drift; build provenance fixed at build time and reported; a declared range of contract and durable-schema versions the artifact supports; and a release gate that asserts a published artifact actually starts and reports ready. The reference's published images could not boot on either side, and the one workflow claiming to prove the product ran could not pass — this capability exists so that class of failure is caught before release rather than by a user.

### Deferred to a later change

Named here because eleven specs already lean on them, so their absence is a known gap rather than an oversight:

- **A human-facing control plane** — operator and tenant authentication, sessions, tenant creation and invitation, and the administrative surface. Roughly forty scenarios across the set say "an operator can retrieve" or "a tenant can list" without a capability owning the surface those verbs happen on. Its namespace is nonetheless committed in v1: `routing/mount-points` reserves an administrative path prefix and `routing/custom-domains` reserves a control-surface hostname.
- **Audit retention and erasure** — `tenancy/isolation` makes the audit trail append-only and immutable and defines neither retention nor removal; `auth/sidecar-credentials` requires records to outlive the credentials they describe under a policy no capability states. The conflict between an immutable trail and any erasure obligation is recorded in `design.md` (D17) and must be resolved explicitly, not discovered.
- **The origin of per-tenant bound values** — `tenancy/isolation` enumerates the bound dimensions in two parts: *occupancy* dimensions it defines outright, and *standing-resource* dimensions contributed by the capability that owns each. Every other spec says "a configured bound". Nothing owns whether those values derive from a plan or tier, who may change them, or how a change takes effect for a tenant with work already in flight. The gap is wider than traffic occupancy: a plan or tier must supply values for hostname claims, certificate issuance, sidecar registrations and affinity bindings as well, and `tunnel/listener` adds a per-credential narrowing whose relation to the per-tenant value must hold at startup.

### Modified Capabilities

None. This is a greenfield repository; `openspec/specs/` is empty and the reference system carries no specs.

## Impact

- **New repository layout**: contract, proxy, sidecar, conformance suite, and docs in one repo. No submodules.
- **Runtime decision**: Elixir/Phoenix for the proxy, Go for the sidecar, and a separate Go edge terminator that D16 places in v1 — it terminates HTTP/2 from clients first and gains HTTP/3 and WebTransport when those ship. Recorded with its reversal history in `design.md` — an earlier Rust recommendation was overturned when adversarial review found the recommended Rust QUIC stack cannot do WebTransport at all.
- **Known runtime gap**: Bandit implements neither HTTP/3 nor RFC 8441 extended CONNECT. The second bites without WebTransport — behind an h2-terminating CDN, WebSocket upgrades arrive as extended CONNECT and fail. Tracked in `design.md` as the strongest surviving argument against the runtime choice.
- **Process**: the development methodology is derived finding-by-finding from how the reference failed, not written from first principles. Documented in `docs/`.
- **Dependencies**: no dependency, tool, or workflow is inherited from the reference without justification. Auto-merge of dependency updates is gated on `semver-patch`, and no wire-protocol pointer advances without a human.
