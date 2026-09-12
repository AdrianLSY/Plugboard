## Context

See `proposal.md` — Why. The relevant constraints, not the motivation:

**Version skew is permanent and asymmetric.** The operator deploys the proxy; tenants deploy sidecars into their own infrastructure on their own schedule. Production will always run an unbounded spread of sidecar versions against one proxy. This inverts normal prioritisation: a schema field that costs nothing today is unfixable once the first tenant pins a version, while an expensive runtime behaviour can ship in phases behind negotiation.

**The reference system's failures are schema failures.** Seven type and shape choices are ceilings no sidecar work can lift — a seven-verb method allowlist, `map<string,string>` headers in both directions, bodies as JSON strings, whole-response buffering with `chunked := len(chunks) > 1` shipped in one message, exactly one reply per correlation id, one global timeout capped at 300s, and no backpressure at any hop. Full evidence in `docs/`.

**Research basis.** Twelve research agents over nine protocol families plus a runtime assessment; the two load-bearing conclusions were handed to adversarial reviewers. One was upheld with corrections, one was overturned. Both outcomes are recorded below, because the overturn changed the runtime decision.

## Goals / Non-Goals

**Goals:**

- A wire contract whose v1 frame vocabulary and type choices are complete enough that no later protocol on the roadmap requires a new frame type or splits the fleet.
- One body-transport path, binary-safe, used by every protocol. The reference base64-encodes WebSocket frames correctly and corrupts HTTP bodies; the defect is the absence of a shared abstraction.
- Deterministic, observable degradation across mixed sidecar versions. A request a sidecar cannot honour is refused with a stated reason, never silently downgraded.
- Tenant scoping as a property of every projection and every mutation signature, not a convention callers may remember.
- A conformance suite that is the authority on the contract, replacing "each side tests its own fiction of the other".

**Non-Goals (design-level, beyond the proposal's scope):**

- Not a forward proxy. `CONNECT` is refused, not forwarded — in a multi-tenant edge it is an open-relay and SSRF hole.
- Not a caching proxy in v1. No response cache, so no cache-key or cache-poisoning surface to reason about.
- Not a load balancer with health-based ejection in v1. Sidecar selection is registry membership plus liveness, not active probing.
- No response body transformation in v1 beyond mount-boundary URL rewriting, which is explicitly scoped and owned.

## Decisions

### D1. Three primitives, not twelve protocols

The protocol surface collapses. Nine of the twelve named protocols are one primitive differing only by `Content-Type` and method token.

```
  PRIMITIVE 1 -- request/response byte stream
    {opaque method token, raw request target, ORDERED (name,value) header
     pairs, opaque octet stream that may begin before it ends, optional
     trailer section, N interim responses then exactly one final response}

    carries: SSE, HLS, LL-HLS, MPEG-DASH, GraphQL-over-HTTP, JSON-RPC-over-HTTP,
             gRPC-Web, Connect, WebDAV, CalDAV, CardDAV, WHIP/WHEP, Range/206,
             long-poll, ordinary HTTP

  PRIMITIVE 2 -- bidirectional frame stream
    carries: WebSocket + everything riding on it (Phoenix Channels, ActionCable,
             graphql-ws, MQTT-over-WS, SIP-over-WS = WebRTC signalling, LSP).
    Also supplies cancellation and interim responses to Primitive 1.

  PRIMITIVE 3 -- QUIC streams + unreliable datagrams
    carries: WebTransport. Exactly one item. Deferred; reserved in the contract.
```

*Alternative considered:* per-protocol handling, which is what the reference did — `ws_check` exists as a runtime probe standing in for a capability the contract could not express, and the WebSocket path grew its own body encoding. Rejected: it produces one code path per protocol, and the paths diverge.

### D2. The tunnel exchange is frame-shaped

The unit on the wire is a frame carrying a stream id, not a message carrying a whole request or response.

```
  v1 frame vocabulary -- ALL reserved at v1, even where unimplemented

    REQ_HEAD       method, target, header pairs, capability assertions
    BODY_DATA      stream id, sequence, opaque octets
    BODY_END       stream id, optional trailer section
    INTERIM_RESP   1xx status + header section (no body, no trailers)
    RESP_HEAD      status, header pairs
    RESET          stream id, application error code, reason
    WINDOW_UPDATE  stream id, credit delta
    DATAGRAM       unreliable class, drop-on-overflow  (v1: reserved, unused)
```

Every frame header carries a stream id and participates in a credit window, even where v1 grants an effectively infinite window. Reserving a frame type costs nothing; adding one later splits the fleet.

*Alternative considered — and strongly recommended for evaluation during implementation:* adopt `draft-ietf-webtrans-http2` capsule framing verbatim instead of a bespoke vocabulary. Its `WT_STREAM` capsules already provide stream ids, FIN, reset with application error codes, session and per-stream flow control, and a datagram class whose discard-on-overflow semantics are specified (§6.11: *"The data in DATAGRAM capsules is not subject to flow control. The receiver MAY discard this data if it does not have sufficient space to buffer it."*). It is designed for exactly this shape — WebTransport streams and datagrams multiplexed inside one reliable ordered bidirectional stream — and it comes with a standards conformance target, which pairs well with an already-decided conformance suite. It reached WG Last Call on 2026-07-06. The reason it is not yet the decision: no publicly available HTTP/2 WebTransport server library exists in any language, so adopting it means implementing draft-conformant capsule framing by hand. Resolve during `tunnel/wire-contract`.

### D3. Capability negotiation, with refusal rather than degradation

The sidecar declares a capability set at tunnel join: `binary_bodies`, `header_lists`, `response_streaming`, `request_streaming`, `trailers`, `interim_responses`, `cancellation`, `flow_control`, `frame_level_ws`, `datagrams`.

The proxy refuses a request or a mount a connected sidecar cannot back, with an explicit status and reason. This is load-bearing because sidecar selection already round-robins across a mount: without negotiation, two identical requests routed to sidecars of different versions get different fidelity, non-deterministically.

*Alternative considered:* best-effort degradation. Rejected — silent fidelity differences between two requests to the same URL are undebuggable, and "it worked yesterday" is the resulting support load.

### D4. Runtime: Elixir proxy, Go sidecar, Go H3 terminator later

**This reverses an earlier recommendation.** The reversal is recorded because the reasoning matters more than the conclusion.

The earlier recommendation was Rust for the proxy, on the premise that WebTransport requires HTTP/3 termination in the same process as the tunnel, which would remove the BEAM from consideration on capability grounds. Adversarial review overturned it:

| claim | finding |
|---|---|
| `tokio-quiche` is the Rust stack for QUIC/H3/WebTransport | Neither `quiche` nor `tokio-quiche` implements WebTransport. `cloudflare/quiche#1114` open since 2021-12-11; Cloudflare, 2025-08-26: *"we can't commit to any timeline or prioritization."* No WebTransport item in either published API. The recommended stack cannot do the thing it was recommended for. |
| MDN: *"WebTransport exclusively uses HTTP/3 and does not fall back to HTTP/2"* | Sentence does not exist on the page or in `mdn/content` source. Fabricated — and the entire "same process, therefore no BEAM" chain rested on it. |
| Tokio: *"preemption is out of scope… for the foreseeable future"* | Not on the cited page. The post exists to announce the mitigation (128-operation per-task budget since 0.2.14). Fabricated. |
| Pingora: 70% less CPU, nginx→Rust | Figures accurate, attribution wrong. Cloudflare credits *"our new architecture which can share connections across all threads"*; the language comparison is against **Lua**. |
| No Go equivalent | `quic-go` powers **cloudflared** — structurally this exact product — plus `frp`, `reverst`, Caddy, Traefik. |

WebTransport can be front-proxied. The WG chair's answer on `w3c/webtransport#525`: *"reverse proxies that want to support WebTransport will need to implement it… The simplest approach is to implement support for WebTransport over HTTP/2 or HTTP/3 when speaking to the origin."* Chromium's stated motivation for WT-over-H2 is *"a protocol we can use for proxy-to-backend communication"*. Caddy PR #7669 bridges bidi streams, uni streams and datagrams across that boundary today.

**Decisive factor:** once WebTransport stops forcing the runtime, what remains is the work that must actually get finished — a distributed sidecar registry with failover, hot-reloadable routing, per-tenant crash containment, and a live multi-tenant admin console. The reference already has all four working on the BEAM. Rewriting them is weeks of hand-written bulkheads, a gossip or etcd layer, and an admin plane rebuilt as `axum` + templates + htmx.

The performance argument does not survive the request path: at minimum two wide-area round trips per request, one into a network the operator does not control, around per-request compute that is header parse plus prefix match plus byte copy. No verified performance advantage for this shape exists in any of the three runtimes.

**Sidecar: Go.** Static binary, `GOOS`/`GOARCH` cross-compilation, an HTTP and TLS stack that already handles whatever a customer backend does, and — underrated — the language a customer's platform team will read before allowing it into their pods. Drop `gorilla/websocket`: archived, and message-level only where the contract needs frame-level fidelity.

**H3/WebTransport edge: a separate Go terminator, later.** Because it speaks the versioned wire contract, it is a contract speaker that can be written in any language and swapped, not a rewrite of the proxy.

### D5. Proxied traffic terminates before application middleware

A dedicated pipeline at the adapter or endpoint level: no body parsing, no method override, no HEAD folding, no content negotiation, no session, no CSRF. This is not a spec requirement; it is the structural consequence of D1 and the direct cause of the reference's worst defect — `Plug.Parsers` consuming request bodies before the proxy reads them, which breaks GraphQL and JSON-RPC through the endpoint pipeline rather than through anything protocol-specific.

Arbitrary method tokens pass through unmodified. `CONNECT` is refused (D-Non-Goals). `TRACE` is answered by the proxy per the `Max-Forwards` rule or returns 405 — forwarding it lets a caller reflect headers the proxy added, including internal auth.

### D6. Framing authority is per-hop, never relayed

`Content-Length` and `Transfer-Encoding` are per-connection properties. The tunnel carries explicitly framed data and each hop generates its own framing headers. A message arriving with both is rejected at the edge with 400, not reconciled. This is the request-smuggling surface, and the reference relays `Content-Length` verbatim over a body path that changes the byte length.

### D7. Timeout taxonomy replaces the single cap

Six separately configurable timers — tunnel connect, origin connect, time-to-first-byte, idle-between-body-bytes, total, and edge header-read — with per-route classes including an explicit `total = infinite`. SSE and watch APIs get a finite TTFB, a finite idle timeout, and no total. The reference's single `request_timeout_ms`, capped at 300s, encodes the assumption that every request ends soon.

### D8. Tenant scoping in the data model, not in queries

Every projection is tenant-keyed and every context mutation takes the acting principal in its signature. The reference demonstrates both failures: the mount projection runs a global full-table `SELECT` and full-keyspace diff on any tenant's change, and `update_token/2` takes no actor at all, yielding a cross-tenant write.

### D9. Domain ownership verification precedes certificate issuance

A v1 blocker rather than a v2 feature. Layering ACME onto a first-come unverified domain claim escalates a routing bug into obtaining a publicly trusted certificate for a domain the claimant does not own. Ownership proof, then certificate.

### D10. Carry-forward is explicit and cited

Roughly sixty items from the reference are ported deliberately, each with a citation, listed in `docs/`. The load-bearing one: the terminal-mount invariant is enforced by two complementary Postgres triggers taking `FOR UPDATE` on the parent, and that invariant is *what makes* longest-prefix ETS matching correct with no trie, no sort and no tie-break. The coupling is recorded nowhere in the reference and is the single thing a naive rebuild would most likely lose.

Deliberately **not** carried forward: the correlation-id machinery. Keep the idea (one logical exchange, independently multiplexed); delete the implementation — D2's stream ids subsume it, along with its unbounded `waiting_callers` growth and its late-reply mailbox pollution.

## Risks / Trade-offs

**[Bandit implements neither HTTP/3 nor RFC 8441 extended CONNECT]** → The strongest surviving argument against D4, and it bites without WebTransport ever being mentioned: behind an h2-terminating CDN, WebSocket upgrades arrive as extended CONNECT with `:protocol: websocket`, an HTTP/1.1-only upgrade predicate can never be true, and WebSocket fails. HTTP/2 to clients is also where real per-stream flow control lives. *Mitigation:* **settled by D16** — HTTP/2 to clients is in v1, so the edge listener is a separate contract-speaking terminator from the start, which is the same mitigation D4 already prescribes for H3. This entry is therefore a scheduled cost, not an open question: task 54.4 terminates HTTP/2 from clients and task 55.1 recognises extended `CONNECT` as an establishment request.

**[Three moving parts for one developer: Elixir proxy, Go sidecar, Go edge terminator]** → *Mitigation:* every edge protocol sits behind the versioned contract, so each component is independently replaceable and independently testable against the conformance suite. D16 settled that HTTP/2 to clients already forces the terminator, so all three are v1 deployables and the mitigation is the contract boundary rather than deferral.

**[A bespoke frame vocabulary duplicates a standard]** → *Mitigation:* D2's alternative. Evaluate `draft-ietf-webtrans-http2` capsules before freezing v1, and prefer the standard if hand-implementing its framing is tractable.

**[Streaming with real backpressure is the hardest item and gates the most value]** → *Mitigation:* build it first, before breadth. It unblocks SSE, HLS/DASH, gRPC-Web streaming and large transfers simultaneously, and no amount of protocol coverage substitutes for it.

**[Conformance suite becomes happy-path theatre]** → The reference's failure mode exactly: 27k lines of tests that never noticed empty bodies. *Mitigation:* the suite is seeded with adversarial fixtures — a lone `0x80` byte, two `Set-Cookie` lines, both `Content-Length` and `Transfer-Encoding`, `%2F` inside a path segment, a trailing-slash collection URI, a `HEAD` with non-zero `Content-Length`, a fragmented WebSocket message, a response that emits headers then stalls 90 seconds. Fixtures before implementation.

**[Slow test suite reproduces the original root cause]** → The completeness critic's finding: when feedback is slow, an agent or a person writes assertions that are cheap to satisfy rather than assertions that are expensive to satisfy. *Mitigation:* a pure core with a thin database edge, so the suite a contributor runs on save needs no Postgres and no serialisation. Treat suite latency as a correctness control.

**[Test config erases the property under test]** → The reference downgrades Argon2 cost and disables SSRF protection suite-wide. *Mitigation:* production-equivalent security configuration in test; speed comes from architecture, never from disabling the invariant.

## Migration Plan

No migration. The reference is read-only prior art with no users to carry forward. Sequencing instead:

1. **Contract first.** Freeze the v1 frame vocabulary and type choices, generate types, write the adversarial fixture suite. Nothing else starts until the schema is frozen, because the schema is the only irreversible artifact.
2. **Streaming spine.** Primitive 1 end to end with real backpressure and cancellation, proven by a test that POSTs bytes and asserts the sidecar received *those exact bytes* — the assertion the reference never had.
3. **Fidelity breadth.** Arbitrary methods, repeated headers, trailers, interim responses, Range. Most of the protocol list falls out here with no protocol-specific code.
4. **Primitive 2.** WebSocket with a deferred 101 relaying the backend's real handshake response.
5. **Tenancy and edge.** Tenant-scoped projections, ownership-verified custom domains, certificate lifecycle, observability.
6. **Deferred, cheap because the primitive exists:** WebTransport via a terminator, HTTP/3 at the edge, multiple tunnel connections per sidecar, transport swap behind an unchanged contract.

### The cost of this ordering, stated rather than discovered

Sorting by reversibility puts the irreversible work first, and the price is that end-to-end signal arrives late. In `tasks.md` as it stood on 2026-09-12, 270 of 727 tasks land before the streaming spine begins (section 26), 406 before a response body first reaches a client (task 38.6), and 440 before the spine closes (section 43). More than half the plan is spent before the architecture is known to carry real traffic, and contract v1 is frozen and published (section 17) before any of it.

That is accepted, not overlooked, because the alternative is worse: a walking skeleton built before the schema is frozen would either freeze the schema by accident or be thrown away, and the schema is the one artifact no later work can correct. But it sits in direct tension with the Risks entry above — *when feedback is slow, an agent or a person writes assertions that are cheap to satisfy* — so the ordering carries three obligations rather than a hope:

- **The two exact-bytes gates are the milestones that matter**, and they are scheduled, not aspirational: task 36.5 turns the request-direction POST assertion green and task 38.6 the response-direction one. Their red baselines are committed from task 4.3 onward, so the gap is visible in CI from the first week rather than being discovered at section 38.
- **Nothing in sections 5 to 25 may be justified by "the spine will need it".** Each is gated by its own conformance fixtures against a stub, not by a downstream consumer that does not exist yet.
- **If either exact-bytes gate has not turned green by the end of section 38, the ordering has failed and the remaining sequence is re-planned** — the plan is wrong before the code is, and that is the cheaper thing to discover.

### D16 · HTTP/2 to clients is in v1, and the edge listener is a separate component from the start

**Decided.** This closes what was previously an open question, and it is recorded as a decision rather than left implicit because the specs had begun to commit to it by accident: `proxy/websocket` requires recognising an establishment request as extended `CONNECT` naming the stream protocol in a dedicated field, and `tunnel/wire-contract` carries the slot for it. A decision that changes the edge topology should not be made by implication in a spec.

**Why yes.** Behind any HTTP/2-terminating CDN, WebSocket upgrades arrive as extended `CONNECT` with `:protocol: websocket` (RFC 8441). Without support, an HTTP/1.1-only upgrade predicate can never match and WebSocket silently fails — which is precisely the reference's defect. Separately, HTTP/2 is where genuine per-stream flow control lives at the edge; WebSocket has none of its own, so without it the client-facing half of the credit chain the fidelity contract requires has nothing to attach to.

**The consequence, accepted.** Bandit implements neither HTTP/3 nor RFC 8441 extended `CONNECT` (issues #27, #91, #690 open). So the edge listener becomes a **separate contract-speaking component in v1**, not later — the same mitigation D4 already prescribes for HTTP/3, arriving earlier. This is the risk named in Risks / Trade-offs materialising as a scheduled cost rather than a surprise.

**Alternative considered:** HTTP/1.1 only at the edge for v1, with the protocol slot reserved but unused. Rejected: it ships the reference's exact silent-failure mode to anyone who puts a CDN in front, and it leaves the client-side flow-control story unanswered.

### D17 · Five further capabilities are in scope; three are deferred with their dependencies named

**Decided** after two cross-capability reviews found behaviour that every spec assumed another owned. In scope for this change: the sidecar as a deployable program, certificate and private-key custody, the tunnel listener, durable schema migration, and packaging of every deployable. Deferred to a later change: a human-facing control plane, audit retention and erasure, and the origin of per-tenant bound values.

The fifth addition, `operability/packaging`, came from the reconcile over fifteen specs: `sidecar/program` requires the sidecar be a self-contained artifact whose packaged configuration is generated from its own schema and whose provenance is fixed at build time, and nothing stated the equivalent for the proxy or the edge terminator that D16 introduces. The reference's unbootable published image was a **both-sides** failure — the proxy raised on a salt set in no packaging artifact, and the sidecar died on a variable its own image never declared — and `docs/history/carry-forward.md` says explicitly to do this on both sides. Packaging therefore owns the obligations common to every deployable; `sidecar/program` retains only what is specific to running inside a tenant's infrastructure.

Rationale for each in-scope addition, and the dependency each deferral leaves behind, are in `proposal.md` — Capabilities.

Two deferrals carry commitments that must land here even though the capability does not:

- **The control plane's namespace is committed in v1.** `routing/mount-points` reserves an administrative path prefix and `routing/custom-domains` reserves a control-surface hostname. That reservation is correct and is kept, so the later capability cannot be locked out of its own namespace.
- **Audit retention carries an unresolved conflict that is named now rather than discovered later.** `tenancy/isolation` makes the trail append-only and immutable; `auth/sidecar-credentials` requires audit records to outlive the credentials they describe under a retention policy no capability states. An immutable trail plus any erasure obligation is a direct contradiction requiring a stated resolution — tombstoning, field-level redaction, or a documented refusal. It is recorded as a conflict, not left as an implementation detail.

### D18 · Frame payloads are encoded from a binary interface definition, with generated codecs

**Decided.** The specs already mandate a binary frame header carrying kind, stream identifier and length, so that an unrecognised frame can be skipped without being understood. This decision covers what encodes the *payloads* — the contents of a request head, a response head, and the control frames. Bodies ride as raw octets in body-data frames under any choice.

**Why an interface definition with generated codecs.** Field-number-based backward compatibility is precisely the additive-change discipline the contract demands, and this way it comes *from the encoding* rather than from reviewer vigilance — which is the same substitution of structure for discipline that the whole rebuild rests on. It also yields codecs for any implementation language, which is what makes "a sidecar in any language" a real offer rather than an aspiration, and it is binary-safe by construction, so the reference's replacement-character defect class cannot be written.

**Cost, accepted.** A schema toolchain becomes a build dependency, and frames are not human-readable without a tool. The mitigation is that the conformance work produces an inspector regardless, since `tunnel/conformance` requires published encode-decode vectors and a suite that can report at the octet level.

**Alternatives considered.** JSON payloads inside the binary frames: inspectable with ordinary tools and trivially implementable in any language, but additive compatibility reverts to manual discipline plus a lint, header pairs cost more bytes per frame, and a JSON envelope coercing strings is the exact origin of the reference's worst defect. A hand-rolled compact binary encoding with published vectors: no toolchain dependency and full control, but hand-written codecs per language and the backward-compatibility rules become yours to invent and enforce.

### D19 · The v1 tunnel is a WebSocket over TLS on the standard HTTPS port

**Decided.** The binding constraint is not elegance or overhead — it is that the sidecar runs inside *the tenant's* infrastructure, where egress policy belongs to someone else. A WebSocket over TLS on 443 traverses nearly every corporate egress policy, transparent proxy and inspecting firewall in practice.

**Cost, accepted.** A framing layer that the contract's own frames then sit inside, and no flow control of its own — which is exactly why the contract carries credit windows rather than borrowing the transport's.

**Alternatives considered.** An HTTP/2 stream would reuse the edge listener D16 already requires and traverses egress well, but HTTP/2 has per-stream flow control of its own, so the contract's credit windows would run on top of it — two interacting layers of flow control, a known source of stalls and throughput cliffs that are painful to diagnose. Raw TLS is the simplest and lowest-overhead option with no borrowed framing, but it is the most likely of the three to be blocked or broken by policies that permit only recognisable HTTP traffic.

**D2 still holds.** The framing is transport-independent, and `tunnel/listener` is written to specify the endpoint without choosing the transport. This decision selects the v1 transport; it does not weld the contract to it, and moving to a different transport later remains a change of transport rather than a redesign.

### D20 · The proxy is a multi-instance installation in v1

**The vocabulary, first, because the rest of this decision depends on it.** One word names a running proxy process across all sixteen specs: an **instance**, or a *proxy instance* where it must be told apart from a sidecar or from the client-facing terminator, with the **installation** being the whole set of them under one operator's configuration. **Node** is reserved for an entry in the mount-point path hierarchy. `tenancy/isolation` fixes both terms for the whole system, and the rename ran across eight specs.

**Decided**, confirming scope that surfaced late. `tunnel/sidecar-registry` requires that a sidecar connected to one instance serves requests arriving at *any* instance — explicitly without requiring the sidecar to hold a tunnel to every instance — and that the registry converges after a partition with no operator action and no sidecar reconnection. Those requirements were written before anyone asked whether v1 was clustered, and the task audit surfaced them as the single largest piece of unplanned scope in the change. They are kept.

**Why keep it rather than defer.** A tenant's sidecar dials one instance; the client's request arrives wherever the load balancer sends it. Single-instance deferral would mean either pinning every tenant's traffic to the instance their sidecar happens to hold — which makes instance loss a tenant outage and forecloses the horizontal story the positioning rests on — or redirecting clients, which is visible to them and breaks non-idempotent requests. Neither is a smaller v1; both are a different product.

**What it costs.** One multi-instance integration harness, extending the integration harness the streaming spine already needs, before the registry work can be verified. Cross-instance dispatch routing, partition-scoped eligibility, convergence tests, and a rolling-replacement drill.

**The bound-accounting consequence.** With more than one instance, a per-tenant ceiling enforced against locally observed consumption grants a tenant one allowance *per instance*, which would falsify the isolation promise the product is sold on. `tenancy/isolation` already required each dimension be *"one configured value per tenant, accounted once"* — but stated that against multiple *admission surfaces*, not multiple instances. That is now settled explicitly, in both directions: a tenant's total across every instance may not exceed the configured value, **and** the value may not be silently divided into per-instance fractions, so a tenant whose traffic all lands on one instance may consume its whole allowance there.

**Per-instance accounting is a closed exception, not an escape hatch.** The sole ground is a dimension bounded *before the consuming party's identity is established* — because an installation-wide count on every arrival is coordination work an unidentified party could trigger at an instance it never connected to. `tunnel/listener`'s pre-authentication connection bound qualifies and is preserved. Where the exception is claimed, the owning capability must state it and its ground, the per-instance nature must be observable, and it must never be attributed to a tenancy. Convenience, performance, and implementation difficulty are explicitly not grounds; a per-tenant dimension accounted per instance is a conformance failure.

**Partitions get a declared discipline rather than silence.** Exact installation-wide accounting is unattainable while instances cannot reach one another, so the specs state the observable contract instead of a mechanism: exactly one of *refuse* or *admit to a locally-held share* per dimension, declared and retrievable rather than emergent, with overshoot finite and determinable in advance, every unaccounted admission recorded, degraded accounting surfaced as an enumerated condition, and recovery that admits nothing further until the tenant is back under its value. A specification that pretends partitions do not happen is worse than one that states a bounded compromise.

### D21 · Rebuild from scratch; the reference is prior art only

**Decided.** The reference does not work: `POST` bodies arrive empty, binary payloads are corrupted, neither container boots. Its defects are ceilings frozen into the wire schema, not accumulated bugs.

*Alternative considered:* restructure the existing code, keeping the 20,810 lines of Elixir tests as an executable specification. **Rejected** once the audit showed the suite is bimodal — the asynchronous and distributed half is worthless or actively self-defeating, and the synchronous half is enumerated as carry-forward instead. The tests are a *citation list*, not a foundation.

### D22 · One repository

**Decided.** Replaces two git submodules whose sync workflow auto-committed unreviewed pointer updates to the parent's `main` on every push to the sidecar's `main`.

**Explicitly not a solution to the contract problem.** A monorepo makes the *repository* consistent and does nothing for production, where sidecar versions spread without bound. It is actively dangerous if it lulls anyone into assuming the two halves agree — which is why it is recorded next to D24 rather than as a mitigation of it.

*Alternative considered:* keep the submodules and gate the pointer-update workflow on human approval. Rejected: it preserves a two-repository release surface for a contract whose whole point is that both halves are generated from one schema.

### D23 · Contract-first, with a conformance suite

**Decided.** A versioned schema is the root artifact; types are generated for every implementation; an executable conformance suite is the authority on the contract.

**Why it is mandatory rather than nice:** the reference asserts its wire contract twice, independently, against two different fictions. `Phoenix.ChannelTest` replaces the serializer with a no-op — provably, `telephone_channel_test.exs:101` asserts an *atom* key that cannot survive JSON — and the Go tests marshal a struct whose tags production never uses. `proxy_res` has zero key-level assertions on either side.

*Alternatives considered:* (a) a shared schema with codegen but no conformance suite — kills type drift but leaves the two-fictions gap; (b) hand-written types plus one docker-compose end-to-end test — cheapest, but drift prevention depends on discipline rather than tooling. Both rejected because version skew is permanent (D24) and discipline does not survive it.

**Secondary benefit:** it makes "a sidecar in any language" real, which is the best-scoped, highest-status contribution an outside contributor can make.

### D24 · Version skew is the governing constraint

**Decided as a framing, not a feature.** The operator deploys the proxy; tenants deploy sidecars on their own schedule or never. Three consequences flow from this and recur throughout every other decision:

- The wire schema is the only irreversible artifact, so work sorts by *reversibility*, not by cost.
- Capability negotiation is mandatory (D3), because sidecar selection round-robins across mixed versions.
- Anything requiring the sidecar to change is expensive forever.

*Alternative considered:* treat skew as a migration problem with a supported-version window and a forced-upgrade path. Rejected: there is no mechanism to force a tenant to upgrade software running in their own infrastructure, so a version window would be a policy the system cannot enforce.

### D25 · Positioning: multi-tenant platform ingress

**Decided by the owner**, against a recommendation for self-hosted dev tunnels.

*The recommendation was* dev tunnels as the front door — demoable in thirty seconds, proven demand, and contributors can use it themselves, which is the strongest predictor of whether anyone contributes. Multi-tenant routing, autoscaling and NAT traversal would then be extensions rather than competing pitches.

**The owner chose multi-tenant ingress.** It is the more impressive systems claim and it is where the architecture already leans. The cost, priced explicitly:

| becomes foundational | where the reference fails it |
|---|---|
| tenant-scoped projections | `mount_store.ex:402` — global full-table `SELECT` plus full-keyspace ETS diff on any tenant's change |
| authorization as a signature, not a habit | `telephone_tokens.ex:353` — `update_token/2` takes no actor; cross-tenant write |
| per-tenant blast radius and an audit trail | one bounded queue in the whole system; no backpressure, no logs, no per-tenant metrics, no audit log |

Dev tunnels would have let all three be deferred. Multi-tenant ingress does not: a prospect's first question is what stops tenant A affecting tenant B, and the answer has to be architectural. This is why D8 is a data-model decision rather than a later feature.

### D26 · WebTransport is designed for, not shipped

**Decided.** The stated need is the capability being reachable rather than present — future-proofing, not scope.

**What that buys and costs.** Reserving the `DATAGRAM` frame type and stream-oriented framing costs essentially nothing. The expensive part — extended `CONNECT` plus capsule framing at the edge — has **zero reuse** for SSE, streaming or WebDAV, whereas the tunnel work WebTransport motivates (incremental emission, binary frames, per-stream interleaving, flow control) is *already mandatory* for SSE and large downloads. So the tunnel work sequences first; it pays for itself either way.

**The trap this avoids.** Building v1 on TCP "with a swappable transport layer" would reproduce the reference exactly: TCP gives one ordered stream, so you invent correlation ids, a pending map, one reply per request, and no backpressure — because that is what TCP forces. Swapping to QUIC later then means deleting the core of the tunnel. Define the primitive first (independent streams plus datagrams) and implement any TCP transport as an emulation of it. Not the reverse.

*Alternative considered:* ship WebTransport in v1 behind the same contract. Rejected under D19 — the v1 transport is a WebSocket over TLS on 443 for egress reasons, and an HTTP/3 terminator is a separate contract speaker added when WebTransport forces it.

### D27 · Observability before the hot path

**Decided.** A metric sink and a structured logger are chosen in week one, with a telemetry-attach test as the gate.

The reference emits 75 telemetry events, attaches zero handlers, and contains one `"Logger."` occurrence in 14,600 lines — inside a doc comment claiming errors are logged. **Five of seven auditors cited that telemetry as evidence of good instrumentation**, which is the finding that makes this a decision rather than a task: emission is visible in review and attachment is not, so the gate has to assert the handler, not the event.

*Alternative considered:* instrument after the streaming spine works, when the signals worth emitting are known. Rejected: the hot path is where retrofitting is most invasive, and the reference demonstrates that "we will attach handlers later" is indistinguishable from never.

### D28 · Licensing: Apache-2.0 over the authored tree

**Decided.** One `LICENSE` at the repository root, Apache-2.0, over the work this repository authors — `docs/`, `openspec/`, `ci/`, and the five component directories when they exist. No per-directory split, no contributor licence agreement. Inbound contributions arrive under the same terms by §5 of the licence itself, which does not depend on GitHub's terms of service and survives a patch arriving by email. `.claude/` is excluded and is covered below.

**Why now rather than later.** The unlicensed state was not a neutral hold. GitHub's terms make inbound-equals-outbound conditional on "a repository containing notice of a license" (§D.6), so with no notice that clause was inoperative and a merged pull request would have stayed under its author's exclusive copyright. §D.5 grants other users only view-and-fork *through the Service*, while the README asks the reader for a full-history clone and a `make check`. **The repository's central invitation was an act it granted no clear right to perform.** D24 supplies the rest of the argument: the licence on published bytes is the irreversible artifact and everything around it is not, so this sorts by reversibility, and the cost of deciding it rises with the first outside contributor rather than with the calendar.

**Why Apache-2.0 rather than MIT.** §5 puts inbound-equals-outbound inside the licence instead of inside a platform's terms. §4 requires notice retention and modification marking, which is the attribution [the supply-chain rule](../../../docs/method/supply-chain.md) asks of others and this decision now asks of itself. §6 conveys no trademark rights, which leaves the *name* rather than the licence as the instrument governing who may claim conformance — the arrangement Kubernetes uses, where the suite is free to run and the mark is not free to use. That matters here because D23 offers third parties a conformance suite as the on-ramp, which obliges the fixtures to be vendorable into a competitor's repository and runnable in their CI. §3 adds an express patent grant with retaliation, but its reach is narrower than it is usually sold as, and the narrowness is recorded in the costs below rather than glossed.

*Alternatives considered:*

**(a) AGPL-3.0 on `proxy/`, Apache-2.0 on `contract/`, `conformance/`, `sidecar/` and `terminator/`** — the split at the deployment boundary, and the only serious alternative. The precedent is strong and consistent: MongoDB's SSPL server with Apache-2.0 drivers, Element's AGPL Synapse against an Apache-2.0 specification, Grafana's AGPL core with an Apache-2.0 agent, HashiCorp's BUSL products with MPL-2.0 SDKs. Teleport shows the split working by directory inside a single repository, so D22 is not the obstacle. Rejected on facts rather than on principle: no pricing, hosted-service, open-core or business-model statement exists anywhere in this repository, and the owner confirms no hosted service is planned — so the restriction would defend revenue that does not exist while landing on the audience D25's tie-break says sets hard requirements. The legal analysis for a tenant running an *unmodified* sidecar is genuinely clean, since §13 fires on modification and deployment inside one legal entity conveys nothing; but that analysis is not what a procurement scanner performs, and the friction is procurement rather than law. This becomes the right answer the moment the owner intends to operate Plugboard as a paid service, and the cheapest moment to take it is before `proxy/` carries code — so that, and not a date, is when this decision reopens.

**(b) MIT** — the category's other norm, and the shorter text. Rejected for §5 and §4 alone: without them, inbound terms depend on the hosting platform and attribution depends on goodwill. The patent argument is the weaker half of the case against it and is not relied on here.

**(c) MPL-2.0** — file-level copyleft, triggered by distribution and expressly not by operating a service, with its own patent grant and retaliation. The coherent middle: protective enough that modifications to these files return, permissive enough that a tenant embedding the sidecar owes nothing. Rejected because file-scoped copyleft is awkward to reason about in Go's package model, it is rare in both target ecosystems, and it buys reciprocity on a tree that has nothing yet to reciprocate.

**(d) BSL-1.1, FSL-1.1-ALv2, Elastic License 2.0, SSPL** — code-available rather than open source. Rejected: none is OSI-approved, which forecloses distribution packaging, and a licence forbidding competing use contradicts D23's offer to third-party implementers in the same repository that makes it. Two common objections to this family are *not* load-bearing and are set aside as wrong: BSL's covenant permits any Change Licence compatible with GPL 2.0 *or a later version*, so Apache-2.0 is a permitted exit and is what Sentry and CockroachDB named; and AGPL-3.0 is recognised by Go's package documentation policy, so that penalty separates recognised licences from source-available ones rather than Apache from AGPL.

**(e) CC-BY-4.0 for `docs/` and `openspec/` with a code licence elsewhere** — the one alternative that engages the fact that prose is this repository's only asset today, and it has precedent in the Kubernetes website. Rejected because the boundary is undecidable in *this* tree: the sixteen specifications carry normative text and outrank the notes, so a docs/code line would cut across the authority precedence rather than along it, and the conformance fixtures derive from specification prose, which would make every quotation into a test name an attribution event under a second licence.

**(f) Leave the tree unlicensed** — rejected above. It is defensible only as a deliberate pause while ownership is confirmed, and it was never stated as one.

**What it costs, named rather than discovered.** A competitor may run Plugboard as a managed service, modified, and owe nothing but attribution. That is the entire protection (a) would have bought, and it is given up permanently for every version published — not in twelve months, on the first push. The mechanism is D24's asymmetry applied to the licence rather than to the schema: a later relicence covers only future versions, and the last permissive commit remains a lawful fork seed forever, which is how OpenTofu, Valkey and OpenSearch came to exist. The vault prose becomes freely copyable rather than merely freely readable, and that is the largest real cost, because the notes *are* the work product today. Note what a restrictive licence would *not* have saved: copyright protection for protocol and API structure is contested rather than settled — the Federal Circuit held Java's declaring code copyrightable in 2014 and the Supreme Court in 2021 assumed copyrightability and decided on fair use instead, leaving the question open — so "nobody can take the design" was never available at any licence. §3's patent grant runs to whoever uses, copies or embeds the Work; a third party who reads the specifications and reimplements from scratch is not a licensee and receives nothing, which is recorded as open work rather than claimed as protection. GPL-2.0-only dependencies are foreclosed for the life of the project. What it does *not* cost is the ability to sell: a sole copyright holder may dual-licence their own code, ship a proprietary edition, or sell hosting at any time without anyone's consent, which is how Traefik, Pomerium and NetFoundry are structured. The step change is not a date; it is **the first merged outside pull request**, after which the tree contains copyright the owner does not hold.

**No contributor licence agreement.** A CLA buys unilateral relicensing and costs exactly the audience the conformance suite exists to create. A DCO is a process change that needs nobody's consent and can be retrofitted, so it belongs to `CONTRIBUTING.md` at task 1.3 rather than here; this decision settles only that there is no CLA.

**One counter-example, stated rather than swept.** The claim that this product category contains no copyleft is false. PageKite — a remote front end plus a local connector with a paid hosted service, structurally the closest analogue that exists — has shipped both halves under AGPLv3 for over a decade, and HAProxy is GPL-2.0-or-later. Permissive dominates the category and Apache-2.0 is modal (frp, cloudflared, Caddy, OpenZiti, zrok, rathole; MIT for Traefik and boringproxy). It is not unanimous, and the exception is the project whose shape most resembles this one.

**The harness is not covered.** Writing this decision surfaced a vendored agent harness under `.claude/` that this repository did not author: the openspec skills declare `license: MIT` and `author: openspec` in their own frontmatter, and every other skill directory and slash command declares no licence, no copyright holder and no source URL. The per-path breakdown is [in the notices file](../../../.claude/THIRD-PARTY-NOTICES.md) and is not restated here, because a count written in two places is one that rots in one of them. `ci/vault.json` already exempts `.claude` from the note gates on the ground that upstream owns its format, but that exemption is about classification and settles nothing about copyright, and no gate looks at this. Extending a blanket Apache-2.0 claim over them would reproduce the exact finding the supply-chain rule logs against the reference — "85 JPEGs of unestablished origin under a blanket MIT claim with no attribution" — inside the repository that logs it. So the grant is scoped and the gap is recorded, which is the refuse-never-degrade posture applied to a licence claim. The scope statement sits in `LICENSE` above the Apache text, which is left byte-identical below it. It is not carried by `NOTICE` alone: §4(d) of the Apache text states that a NOTICE file's contents "do not modify the License", so an exclusion living only there would be in the one place the licence disclaims as incapable of narrowing it. What that costs is that `LICENSE` is no longer byte-identical as a whole file, and a licence detector keying on total content may report it as unrecognised — 1.6% added against a threshold commonly set at 98%, which is an argument and not a measurement until someone runs the detector.

## Open Questions

The four questions previously recorded here are resolved as decisions: HTTP/2 to clients (D16), the scope of further capabilities (D17), frame payload encoding (D18), and the v1 tunnel transport (D19). D16 opened one in their place.

**Whether full gRPC at the ingress is still refused, and on what ground.** The refusal in `proposal.md` — Non-goals rested entirely on the edge: `grpc-status` travels as a trailer even on success, and a Plug-based edge cannot express one. D16 removes that edge. The terminator speaks HTTP/2 to clients, task 44.1 binds the client-edge trailer fixtures, and task 46.3 delivers a backend's trailer section to a client whose protocol can carry one instead of folding it into the header section — so the stated reason no longer holds. What is unanswered is whether any other ground survives (deadline propagation, bidirectional streaming, and the plain fact that no section of `tasks.md` builds an ingress gRPC path), or whether the refusal should be withdrawn and the work scheduled. It is recorded as open rather than quietly re-justified, because inventing a fresh reason for a standing refusal is how a documented refusal turns into a habit. Until it is settled the refusal stands on scope: nothing in this change builds it.

Two items are deliberately left to be settled *inside* implementation rather than before it, because the specs are written to hold either way and neither moves the task breakdown:

- Whether `draft-ietf-webtrans-http2` capsule framing is adopted in place of the bespoke frame vocabulary (D2's alternative). Evaluate before the contract's first version is frozen.
- Which challenge type is preferred for wildcard hostname verification, where more than one can prove control (`routing/custom-domains` requires that at least one work, not which).
