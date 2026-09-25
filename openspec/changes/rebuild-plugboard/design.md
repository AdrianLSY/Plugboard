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
  v1 stream-scoped frame vocabulary -- ALL reserved at v1, even where unimplemented

    REQ_HEAD       method, target, header pairs, capability assertions
    BODY_DATA      stream id, sequence, opaque octets
    BODY_END       stream id, optional trailer section
    INTERIM_RESP   1xx status + header section (no body, no trailers)
    RESP_HEAD      status, header pairs
    RESET          stream id, application error code, reason
    WINDOW_UPDATE  stream id, credit delta
    DATAGRAM       unreliable class, drop-on-overflow  (v1: reserved, unused)
```

Every frame header carries a stream id (tunnel-scoped kinds carry the reserved tunnel-scoped identifier of task 8.1), and every body octet participates in both credit windows, even where v1 grants an effectively infinite window. The liveness exchange and the datagram class are exempt from credit (`tunnel/wire-contract`). Reserving a frame type costs nothing; adding one later splits the fleet.

*Alternative considered — and strongly recommended for evaluation during implementation:* adopt `draft-ietf-webtrans-http2` capsule framing verbatim instead of a bespoke vocabulary. Its `WT_STREAM` capsules already provide stream ids, FIN, reset with application error codes, session and per-stream flow control, and a datagram class whose discard-on-overflow semantics are specified (§6.11: *"The data in DATAGRAM capsules is not subject to flow control. The receiver MAY discard this data if it does not have sufficient space to buffer it."*). It is designed for exactly this shape — WebTransport streams and datagrams multiplexed inside one reliable ordered bidirectional stream — and it comes with a standards conformance target, which pairs well with an already-decided conformance suite. Its WG Last Call opened on 2026-03-09 against revision 14 and **closed on 2026-03-29**; 2026-07-06 is revision 15's posting date, which this entry previously mistook for the Last Call. Verified against the datatracker's single `changed_state` event and the chair's Last Call announcement on the webtransport list. The document has sat in that state since, unadvanced, with `rfc_number` null — so the standing to weigh is a draft whose Last Call concluded five months ago and which has not moved, not one under active review. The reason it is not yet the decision: no publicly available HTTP/2 WebTransport server library exists in any language, so adopting it means implementing draft-conformant capsule framing by hand. Resolve during `tunnel/wire-contract`.

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

Deliberately **not** carried forward: the correlation-id machinery. Keep the idea (one logical exchange, independently multiplexed); delete the implementation — D2's stream ids subsume its multiplexing and reply-matching role, along with its unbounded `waiting_callers` growth and its late-reply mailbox pollution. The correlation identifier the request head carries (task 8.5; `tunnel/wire-contract` *Exchanges carry a correlation identifier distinct from the stream identifier*) is not that machinery: it is an opaque join key for signals, assigned once per exchange (`operability/observability`; task 34.2) and never used to match a reply.

## Risks / Trade-offs

**[Bandit implements neither HTTP/3 nor RFC 8441 extended CONNECT]** → The strongest surviving argument against D4, and it bites without WebTransport ever being mentioned: behind an h2-terminating CDN, WebSocket upgrades arrive as extended CONNECT with `:protocol: websocket`, an HTTP/1.1-only upgrade predicate can never be true, and WebSocket fails. HTTP/2 to clients is also where real per-stream flow control lives. *Mitigation:* **settled by D16** — HTTP/2 to clients is in v1, so the edge listener is a separate contract-speaking terminator from the start, which is the same mitigation D4 already prescribes for H3, while the proxy-alone edge the specifications also define stays a supported topology rather than v1's only one. This entry is therefore a scheduled cost, not an open question: task 54.4 terminates HTTP/2 from clients and task 55.1 recognises extended `CONNECT` as an establishment request.

**[Three moving parts for one developer: Elixir proxy, Go sidecar, Go edge terminator]** → *Mitigation:* every edge protocol sits behind the versioned contract, so each component is independently replaceable and independently testable against the conformance suite. D16 settled that HTTP/2 to clients already forces the terminator, so all three are v1 deployables, the proxy alone remaining a defined edge topology (D16), and the mitigation is the contract boundary rather than deferral.

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
- **Nothing in sections 5 to 25 may be justified by "the spine will need it".** Each is gated by its own conformance fixtures against a stub, not by a downstream consumer that does not exist yet — with the exceptions stated in the tasks themselves rather than discovered, task 6.8a, the cross-instance half of task 6.8, being one: it runs on task 33.10's multi-instance harness, which is a downstream consumer.
- **If either exact-bytes gate has not turned green by the end of stage 4b (Staged delivery, below), the ordering has failed and the remaining sequence is re-planned** — the plan is wrong before the code is, and that is the cheaper thing to discover.

**Section order is not the work order.** Some tasks depend on tasks numbered after them, and the
dependency is recorded in the depending task's own text — named there as a prerequisite rather than
left as a passing citation, so an agent or a person working the list in file order is told before
starting rather than after failing. It is never recorded by moving a task. The identifiers cannot
move: every `task N.M` reference in `tasks.md`, and every task and section number cited in this file
and across `docs/`, resolves against them, so a renumbering that silently redirected one would be the
defect class this repository exists to refuse. `tasks.md` is therefore the single place any instance
is recorded, and this paragraph deliberately enumerates none.

### D16 · HTTP/2 to clients is in v1, and the edge listener is a separate component from the start

**Decided.** This closes what was previously an open question, and it is recorded as a decision rather than left implicit because the specs had begun to commit to it by accident: `proxy/websocket` requires recognising an establishment request as extended `CONNECT` naming the stream protocol in a dedicated field, and `tunnel/wire-contract` carries the slot for it. A decision that changes the edge topology should not be made by implication in a spec.

**Why yes.** Behind any HTTP/2-terminating CDN, WebSocket upgrades arrive as extended `CONNECT` with `:protocol: websocket` (RFC 8441). Without support, an HTTP/1.1-only upgrade predicate can never match and WebSocket silently fails — which is precisely the reference's defect. Separately, HTTP/2 is where genuine per-stream flow control lives at the edge; WebSocket has none of its own, so without it the client-facing half of the credit chain the fidelity contract requires has nothing to attach to.

**The consequence, accepted.** Bandit implements neither HTTP/3 nor RFC 8441 extended `CONNECT` (issues #27, #91, #690 open). So the edge listener becomes a **separate contract-speaking component in v1**, not later — the same mitigation D4 already prescribes for HTTP/3, arriving earlier. This is the risk named in Risks / Trade-offs materialising as a scheduled cost rather than a surprise. The separate terminator is the component that serves HTTP/2 clients and extended `CONNECT` from the start. The specifications also define a deployment whose edge is the proxy alone (`proxy/edge-hygiene`, *The same outcome from either topology*), held to identical statuses and reasons; that is the topology the exact-bytes gates of tasks 36.5 and 38.6 exercise, as do tasks 48.8, 69.7 and 74.1, task 54.9 holding the terminator topology to the outcomes recorded there. What D16 rules out is that topology being v1's only edge, not its existence.

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

**Decided.** One `LICENSE` at the repository root, Apache-2.0, over the work this repository authors — `docs/`, `openspec/`, `ci/`, and the five component directories when they exist. No per-directory split, no contributor licence agreement. Inbound contributions arrive under the same terms by §5 of the licence itself, which does not depend on GitHub's terms of service and survives a patch arriving by email. The vendored agent harnesses under `.claude/` and `.agents/` are excluded and are covered below.

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

**The harnesses are not covered.** Writing this decision surfaced a vendored agent harness under `.claude/` that this repository did not author: the openspec skills declare `license: MIT` and `author: openspec` in their own frontmatter, and every other skill directory and slash command declares no licence, no copyright holder and no source URL. Its per-path breakdown is [in the Claude notice](../../../.claude/THIRD-PARTY-NOTICES.md) and is not restated here, because a count written in two places is one that rots in one of them. The later Codex harness under `.agents/` has better provenance: [`skills-lock.json`](../../../skills-lock.json) names the source path and content hash for every installed Matt Pocock skill, the OpenSpec-generated skills identify their author and licence, the `pr` skill retains its HumanLayer attribution, and [the Codex notice](../../../.agents/THIRD-PARTY-NOTICES.md) carries all three upstream MIT notices. `ci/vault.json` exempts both harness roots from the note gates on the ground that their loaders and upstreams own their formats, but that exemption is about classification and settles nothing about copyright, and no gate looks at this. Extending a blanket Apache-2.0 claim over them would reproduce the exact finding the supply-chain rule logs against the reference — "85 JPEGs of unestablished origin under a blanket MIT claim with no attribution" — inside the repository that logs it. So the grant is scoped, the known terms are carried, and the remaining Claude provenance gap is recorded: the refuse-never-degrade posture applied to a licence claim. The scope statement sits in `LICENSE` above the Apache text, which is left byte-identical below it. It is not carried by `NOTICE` alone: §4(d) of the Apache text states that a NOTICE file's contents "do not modify the License", so an exclusion living only there would be in the one place the licence disclaims as incapable of narrowing it. What that costs is that `LICENSE` is no longer byte-identical as a whole file, and a licence detector keying on total content may report it as unrecognised — the added scope statement is small against the canonical text, which is an argument and not a measurement until someone runs the detector.

### D29 · No gate manifest. The roster is discovered; the INVOCATIONS are reconciled

**Decided**, settling task 3.1, which asked for `ci/gates.yml` "enumerating every gate a merge or
release depends on, with each entry naming the obligation it enforces, its invocations, and its paired
broken input".

**The manifest is refused.** Three of those four fields are already single-sourced, and a file
restating them would be the second encoding this repository spends most of its gates refusing:

| the field | where it already lives |
|---|---|
| the roster | `ci/gates/*.py`, discovered by `ci/run-gates.py`. `ci/vault.json` says why in its own words: "a declared roster is a second encoding of what the tree states". |
| the paired broken input | `ci/broken-inputs/<gate-id>/`, bound by naming rule and enforced by `ci/gates/meta.py`. |
| the obligation | each module's `RULE_NOTE`, reconciled against `docs/rule-index.md` by `ci/gates/rule_gate_correspondence.py`. |

**The fourth field was real.** Task 3.1's own verification clause names its subject and it is not the
gate modules: *"a check that fails if any CI **job** enforces an obligation absent from the manifest"*.
Invocations live in workflow files, and three of the five — `test.yml`, `pr.yml` and
`dependabot-auto-merge.yml` — were undeclared. `ci/gates/runner.py` checks path filters, branch
filters and `continue-on-error` only on what `runner.workflows` declares, so those three ran as
blocking jobs with their refusal-defeating clauses read by nothing, and every gate was green
throughout.

**What was built instead.** Every workflow is declared with its required triggers and a stated
reason, and a new `runner-workflows` correspondence reconciles that declaration against the directory
in both directions: a workflow file nobody declared fails by name, and a declaration whose file is
gone fails too. Both demonstrated.

**Why this one could not be solved by deleting an encoding**, which is the remedy everywhere else
here. A workflow file's format is owned by the hosting service. The declaration cannot move into it
and it cannot move into the declaration, so two encodings are forced — and the answer for a forced
pair is to reconcile it, which is exactly what `ci/gates/correspondences.py` exists for. It held one
pair before this and now holds two.

*Alternative considered:* write `ci/gates.yml` as asked and accept the duplication, on the grounds
that an explicit manifest is easier to read than a discovery rule. Rejected: the manifest would have
to be maintained by hand against four things that already know their own answer, and a stale entry in
it would be indistinguishable from a correct one — which is the defect the roster was made
discoverable to avoid.

### D30 · Durable state is held in PostgreSQL

**Decided by the owner.** PostgreSQL is the engine of every durable store the proxy installation
itself operates. It binds the proxy alone: no specification assigns durable state to the client-facing
terminator, and the sidecar originates from local configuration inside the tenant's infrastructure, so
nothing settled here reaches a tenant's deployment.

**Why it is recorded now rather than left where it sat.** The store is assumed throughout the build
and decided nowhere. `Makefile:113` defines the integration tier as real Postgres and real sockets;
task 22.5 names the product outright, requiring notification delivery to be proven against real
Postgres with committing transactions; the integration job in `.github/workflows/test.yml` stands up a
`postgres:16` service container while the fast job deliberately declares none. By this repository's own
rule a thing is decided when the register holds it with its rationale and open when it is listed as
undecided, and [anything else is neither](../../../docs/start-here.md#conventions). D10 makes that more
than untidiness: the carry-forward it calls load-bearing is specific to this store, so the choice has
been carrying weight since before anyone wrote it down.

None of the sixteen specifications names a storage product, and that is correct rather than an
omission. Behaviour belongs to them and the choice belongs here; nothing below is a new obligation on a
specification.

**What is relied on, each against the requirement that needs it.**

- **A row lock inside the writing transaction.** D10 states the mechanism and carries its citations;
  they are not repeated here. What this decision adds is why the store rather than the code must supply
  it: `routing/mount-points` makes that enforcement a property of the durable store rather than of any
  single code path that writes to it, and requires it to hold for operations issued from independent
  sessions. A parent-row lock taken in the writing transaction answers both at once.
- **Transactional DDL.** `operability/schema-migration` requires an interrupted migration to leave the
  recorded version unadvanced and to be identifiable where it stopped. A schema change that commits or
  rolls back whole satisfies that without a hand-written inverse per step. Where a change cannot be
  applied as one indivisible unit — a concurrent index build cannot — that specification already owns
  the outcome rather than leaving it to be discovered: such a migration declares itself as such, and
  declares the point a re-run resumes from.
- **Change notification, for latency and never for correctness.** `routing/mount-points` requires a
  committed change to become effective within a configured bound *whether or not any notification was
  delivered, and with no notification mechanism present at all*, and task 22.4 tests exactly that. So
  notification is an optimisation the store happens to offer, not a mechanism the system has: where it
  is used it fires at commit, which is why task 22.5 is specific about committing transactions — a
  sandboxed transaction never commits and so never delivers. Its absence in a replacement store would
  cost latency rather than correctness.
- **One store that several instances read.** D20 makes the installation multi-instance, so the durable
  store is the shared state every instance projects from. It is not the sidecar registry:
  `tunnel/sidecar-registry` states no durable-store obligation at all, and this decision does not give
  it one.

**This settles the engine, not the store count, and not what sits outside the platform.**
`operability/schema-migration` contemplates an installation holding more than one durable store, each
separately versioned and checked together with the rest; whether those share one database or several is
that capability's to constrain. And the decision reaches only stores the installation itself operates —
cryptographic material held outside the platform is `security/key-custody`'s, and nothing here obliges
it into a database.

*Alternatives considered:*

**(a) SQLite, or any store embedded in the proxy process.** Rejected on D20. An embedded store is
per-instance, so a mount created at one instance exists at one instance, and the cross-instance
effectiveness bound `routing/mount-points` places on the lookup surface becomes a replication protocol
this project would then own. It also reopens by the back door the per-instance accounting exception D20
deliberately closed: a per-tenant bound accounted against a per-instance store grants one allowance per
instance, which is the conformance failure that decision names.

**(b) A key-value or document store.** The alternative worth engaging rather than waving away, because
what it offers is real — the projections are already tenant-keyed, so they shard on the key they
already have, and most of the migration machinery the previous point relies on disappears. **Rejected
on the invariant.** The terminal-mount rule needs a lock on the *parent* that a concurrent sibling
insert must respect, and a store with no cross-document transaction cannot offer one, so the check
moves into application code — which is precisely what `routing/mount-points` forecloses by making the
enforcement the store's. Reconstructing it means a lease per subtree, which is a second durable system
with failure modes of its own, or optimistic retry, whose conflict window that capability's concurrency
requirement does not permit. The invariant is not a detail: it is what makes strip-one-segment-and-retry
terminate at the unique correct answer with no trie, no sort and no tie-break.

**(c) Leave it undecided.** Rejected on the rule cited above, and on the specific harm rather than on
principle: the assumption is already encoded across the build, so "undecided" describes nothing true of
the tree. An assumption encoded several times and stated nowhere is this repository's duplication defect
with the original missing — there is no first encoding for the copies to be reconciled against, which is
why no gate could have caught it.

**What it costs, named rather than discovered.**

An operational dependency the tenant never sees and the operator cannot avoid: a database to run, back
up, restore and upgrade, on whose availability the mutation path depends. Not the matching path —
`routing/mount-points` already requires a lookup to complete against the last loaded state while the
store is unreachable, and task 22.8 is where that is proven — so the honest statement of the blast
radius is that mutations stop while traffic continues.

The fast tier has to stay free of this store, and that is a constraint on the architecture rather than
on the test setup: a module that cannot be exercised without a database is a module the tier a
contributor runs on save does not cover. The mitigation is already stated in Risks / Trade-offs under
*[Slow test suite reproduces the original root cause]* and is not restated here. What this decision adds
is that the constraint now descends from a recorded choice, so a contributor asking why the core may not
simply query has an entry to read instead of a habit to infer.

Part of the system's correctness then lives in the store rather than in the pure core, invisible to the
type system and unreachable by the fast tier. That cost has been paid once already, and the way it
failed is recorded rather than inferred: every "concurrent" test in the reference ran under one shared
sandbox connection (`data_case.ex:46`), so the `FOR UPDATE` locks the invariant depends on were never
once contended. Choosing this store means owning the contended integration test the reference never had.

**Reversibility, under D24's own framing.** The store is not the wire schema and the asymmetry does not
reach it: no tenant pins a database version, nothing a tenant deploys can observe the choice, and the
operator upgrades their own store on their own schedule. So this is reversible, and the price is stated
rather than implied — the store-enforced invariants re-expressed in whatever replaces them or moved into
code with a serialisation story of their own, a data migration conducted under
`operability/schema-migration`'s own rules, and an integration tier rewritten against the new store. That
is one component's rewrite and one migration, paid once, by one party, with no tenant action required.
Expensive, bounded, and categorically unlike the schema decisions D24 governs, which cannot be paid at
all.

**What would reopen it.** A stated durable-state requirement one PostgreSQL cluster cannot meet — a
write-latency bound across geographically separated instances, or a per-tenant volume beyond what one
primary serves — because the answer to either is a second system of record rather than a tuning exercise.
A decision moving the terminal-mount invariant out of the store and into code, which would remove the
largest single reason recorded here. A hosting arrangement whose managed PostgreSQL withholds the trigger
or DDL surface this relies on.

### D31 · A declared out-of-scope set may not name its own declarant's tree

**Decided.** `ci/vault.json`'s `out_of_scope` key declares a set of paths byte-unchanged against a
pinned baseline, and names in `declared_by` the change forbidden to touch them. Those are not the same
mechanism. `ci/gates/out_of_scope.py` reads `declared_by` for the failure text and for the expiry check
that ends a declaration once every declarant is archived. **The byte-unchanged assertion itself is
unconditional and cannot observe which change is editing.**

So re-pointing `declared_by` does not re-scope the freeze. It changes whose name the failure prints and
when the declaration expires, and nothing else. On 2026-09-12 the set naming
`openspec/changes/rebuild-plugboard/specs` was re-pointed from the two archiving documentation changes
to `rebuild-plugboard` itself — the change that owns those sixteen specifications and must revise them
as implementation finds gaps. A freeze whose ending condition was days away became one that ends when
the plan does, and the manifest recorded the move as the assertion continuing to mean what it meant. It
does not: the field that scopes the declaration is not the field the assertion reads, so the inversion
was invisible in review and every gate stayed green through it.

**The invariant this installs.** A declared out-of-scope path may not lie inside a declaring change's
own directory. It is checkable, it is what "out of scope" means, and having it as a check rather than as
a comment is the difference between the two states this repository keeps distinguishing. Task 3.16 does
the work.

*Alternatives considered:*

**(a) Retire the gate along with the declaration.** Refused, and not on preference:
[`openspec/specs/docs/knowledge-base/spec.md`](../../specs/docs/knowledge-base/spec.md) holds the
byte-unchanged requirement and requires the assertion be among those the aggregating target reports. The
declaration may go; the gate may not.

**(b) Re-baseline a third time.** Refused on evidence already in the tree. A pinned baseline cannot name
the commit that carries the revision it is meant to admit, so every revision becomes a two-commit dance
whose first commit is red — and a squash merge destroys the intermediate identifier, which is exactly how
`26d2927` came to be reachable from nothing and `make check` came to fail for every reader but its
author.

**(c) Keep the declaration and re-baseline per spec revision.** Refused: it converts a deliberate visible
act into a routine one, and a step taken on every change is a step nobody reads.

**What it costs, named rather than discovered.** Retiring the declaration removes the only mechanical
control against a coherence pass silently revising a specification no task named — the defect the gate's
own docstring says motivated it, and `/opsx:update` reconciles neighbouring artifacts over glob-expanded
spec paths, so the hazard is real rather than theoretical. The containment invariant replaces *who may
not edit* with *who may not declare*, which is a weaker property, and this decision does not pretend
otherwise. Whether anything should replace the immutability half — and if so what, given that the owner
of these specifications must be able to revise them — is left open here rather than answered by
implication.

### D32 · make check holds every tree property on change, inside a declared budget

**Decided**, settling task 3.17, which asked what the one command is for and for a budget on it.

**What it is for.** `make check` is the command run on every commit and repeated by CI, and it decides
every property of the tree on every run — the meta-gate's isolation cross-product included. Nothing
moves to `.github/workflows/scheduled.yml`, so `parity.schedule.invokes` in `ci/vault.json` is
unchanged and task 3.12's check holds the same commands it held before. Task 3.10's own-input failure
and task 3.12's on-change meta-check and parity run are untouched.

**The budget.** `gate_policy.budget_seconds` in `ci/vault.json`, 40 seconds, enforced by
`ci/run-gates.py` in the fast tier's shape: the number is declared rather than written in code, the
elapsed time is printed on every run including a passing one, and a run over the budget fails naming
both and the remedy. Raising it is a change to this entry, not a tuning step. Because wall-clock
cannot tell a slower tree from a busy machine, a run also prints the one-minute load average at its
start against the core count and the CPU time its gates spent, and a breach that started on a machine
loaded to its core count says so first, sending the reader to re-run `make check` alone before the
remedy applies, and still fails.

**Why it fits, measured.** On 2026-09-24, at 43 gates, the run took about 120 seconds. Measured again
on 2026-09-25 before the change: 126 seconds on a ten-core workstation and 105 on CI's `make check`
step, of which `ci/gates/coverage.py` spent 62 and `ci/gates/meta.py` 49 on the workstation, the other
41 gates about 14 together. Two causes, neither of them the checks themselves:

| cause | what changed |
|---|---|
| `coverage.py`'s subject is every gate's own output, and it produced that output by running every gate a second time — including the meta-gate | It runs last and reads the output `ci/run-gates.py` captured, from a fresh directory named in `GATE_OUTPUTS`. Pointed anywhere but the repository root, or at a gate the capture lacks, it still runs the gate itself, so the gate decides without the runner |
| The runner, and the meta-gate's scenario and cross-product runs, were sequential over independent processes | Both run their processes concurrently, bounded by the core count, and report in roster order |

After: 13.0 seconds on the same workstation, every gate's verdict unchanged — 58 scenarios proven to
fail by their own logic, no cross-gate failure.

**What the budget is for, given that.** Concurrency divides the cross-product's cost by the core count
and does nothing to its growth: every gate added runs against every violating tree, and every tree
added is run by every per-file gate. The budget is what makes that growth visible before it changes
what gets written. When a run breaches it, the remedy is named here rather than improvised: move the
cross-product to the schedule, keep a cheaper isolation property on change — the pairs whose gate or
violating input the change touches — and add the moved command to `parity.schedule.invokes`, so task
3.12's check holds it executed there at a command position.

*Alternatives considered:*

**(a) Move the cross-product to the schedule now.** Rejected: it weakens what every change is checked
against, to save a cost that removing the double run and the serial loop already removed.
`.github/workflows/scheduled.yml` runs daily and also on every push and pull request, so the move
would not take the property out of CI. It would take it out of the local `make check` a commit runs
and out of `check.yml`'s on-change run, whose `check` job is a required check where
`scheduled.yml`'s `standing-checks` is not
([branch protection](../../../docs/code/reviewing.md#pull-requests)): a change that breaks the
property would be told so on its own pull request, and could merge regardless.

**(b) Remove the causes and set no budget.** Rejected: that is the state the run was in while it grew
from seconds at 26 gates to two minutes at 43, with nothing noticing until it interrupted work. The
growth is structural, so the control has to be.

**(c) Have `coverage.py` inspect each gate's source for its coverage call instead of its output.**
Rejected in that gate's own docstring and not reopened: a present call proves nothing about what a run
prints, and a gate once reported "0 citations checked" while exiting zero.

### Staged delivery, and the task that closes each stage

The work is delivered in stages, each ending in one reviewed pull request at a point where something new
is demonstrably true — shown by a gate or a recorded outcome, not by code existing — with `make check`
green on `main`. A task belongs to the latest of its own section's stage, the stages of the
prerequisites its text names and the stage of any task whose change its text names as the one it lands in, with two anchors the table states: task 33.10, which builds the
installation's only multi-instance harness, belongs to stage 4d although section 33 is 4b's, and task
39.7a, the interim non-declaring flow-control mode, belongs to stage 4b although section 39 is 4c's. Membership
is therefore read off `tasks.md`, which stays the single place a prerequisite is recorded, as the
paragraph on section order above requires. A stage closes when every task in it is done; the table
names only the check that headlines each.

| stage | sections | headline check |
|---|---|---|
| 0 Runway | 1–4 | task 3.17 holds `make check` to its budget, and tasks 1.5, 1.8, 1.9 and 1.10 are demonstrated on the forge |
| 1 Honest processes | 5, 6 | every component validates its configuration in one pass, reports provenance, answers on its operational endpoint and withdraws through task 5.8's lifecycle, with task 6.1's attach test blocking |
| 2a Contract decisions | 7 | tasks 7.1 and 7.7 are recorded decisions carrying their adversarial pass, and task 7.2's pinned toolchain resolves the identical digest on a clean machine |
| 2b Schema and codecs | 8–11 | task 11.8: both generated codecs agree on every published and adversarial vector |
| 2c Corpus and runner | 12–13 | none beyond the stage's own tasks |
| 2d Coverage closed | 14–16 | tasks 14.5 and 14.5a at zero uncovered and zero unproven, task 13.22's packaged suite against a do-nothing stub reporting every requirement unmet and none unresolved, and task 15.9's catalogue meta-test |
| 2e Freeze | 17 | tasks 17.1 and 17.2: contract v1 tagged |
| 3a Routing state | 18–23 | task 20.10's cumulative-schema job over the full migration set |
| 3b Custody and credentials | 24–25 | none beyond the stage's own tasks |
| 4a Tunnel up | 26–32 | task 26.4a: the real proxy and sidecar start in CI with every process ready over an established tunnel, and task 32.6: a frozen contract layer fails liveness while its socket stays open |
| 4b First bytes | 33–38 less task 33.10, and task 39.7a | tasks 36.5 and 38.6: both exact-bytes gates advanced in `ci/expected-outcomes.json` |
| 4c Flow control and lifecycle | 39–42 less task 39.7a | none beyond the stage's own tasks, all on one instance |
| 4d Installation and spine closure | 43, and task 33.10 | task 43.4's soak |
| 5a Fidelity breadth | 44–53 | none beyond the stage's own tasks |
| 5b Edge terminator | 54–55 | task 54.12's conformant client-facing verdict |
| 6 Primitive 2 | 56–60 | task 60.9's primitive-2 gate |
| 7a Program and tenancy | 61–64 | none beyond the stage's own tasks |
| 7b Custody lifecycle and custom domains | 65–68 | none beyond the stage's own tasks |
| 8 Ship | 69–75 | task 74.16's multi-instance release soak |

The trigger stated above for re-planning is measured at a stage rather than a section: if either exact-bytes gate
has not turned green by the end of stage 4b, the remaining sequence is re-planned.

*Alternatives considered.* **Moving tasks into stage order**, which was proposed first and is refused
by the paragraph on section order: a prerequisite sentence carries the same information without moving
an identifier that the vault cites. **Stages as bare section ranges**, rejected because a stage defined
by its sections alone cannot close while one of its tasks names a prerequisite in a later stage, and an
audit of every open task on 2026-09-24, with an adversarial pass over each finding, found such
prerequisites in most sections. That audit's findings were recorded as prerequisite sentences and, where
one clause alone depended on later work, as a letter-suffixed task beside its source, so no obligation
moved stage without its text saying so.

*One criterion the revision applied, stated here so it is applied again rather than re-derived.* A
stand-in may carry a verification when the mechanism under test is generic over its input and every
real instance is asserted where it lands; it may not when the claim is about one real subject's
behaviour, or when the stand-in exists only to give a check something to refuse. It is recorded here,
where the revision that relied on it lives, and `docs/code/testing.md` links it rather than restating
it.

## Open Questions

The four questions previously recorded here are resolved as decisions: HTTP/2 to clients (D16), the scope of further capabilities (D17), frame payload encoding (D18), and the v1 tunnel transport (D19). D16 opened one in their place, and D20 left a second.

**Whether full gRPC at the ingress is still refused, and on what ground.** The refusal in `proposal.md` — Non-goals rested entirely on the edge: `grpc-status` travels as a trailer even on success, and a Plug-based edge cannot express one. D16 ends that edge being the only one. The terminator speaks HTTP/2 to clients, task 44.1 binds the client-edge trailer fixtures, and task 46.3 delivers a backend's trailer section to a client whose protocol can carry one instead of folding it into the header section — so the stated reason no longer holds for a deployment the terminator fronts. What is unanswered is whether any other ground survives (deadline propagation, bidirectional streaming, and the plain fact that no section of `tasks.md` builds an ingress gRPC path), or whether the refusal should be withdrawn and the work scheduled. It is recorded as open rather than quietly re-justified, because inventing a fresh reason for a standing refusal is how a documented refusal turns into a habit. Until it is settled the refusal stands on scope: nothing in this change builds it.

**How the instances of one installation reach one another.** `tunnel/sidecar-registry`, as D20 records, fixes what the installation must
achieve — a tunnel held at one instance serving requests that arrive at any instance, and a registry
converging after a partition with no operator action and no sidecar reconnection — and D30 fixes the
durable store, but nothing records the mechanism that publishes registry state between instances or
carries the dispatch hop, although `tunnel/sidecar-registry` *The dispatch hop is mutually authenticated and protected before an exchange crosses* requires that hop to be mutually authenticated,
confidential and integrity-protected before any exchange octet crosses (task 33.13a) and D25 sells per-tenant blast radius. Distributed Erlang
is the obvious candidate on this runtime and is deliberately not assumed: how far its trust between
connected nodes answers that requirement is a claim about a runtime, which `docs/method/harness.md` requires
be verified adversarially rather than asserted. Task 33.0 settles it before task 33.1 builds the
registry, because the shape of a single-instance entry depends on how it is replicated.

Two items are deliberately left to be settled *inside* implementation rather than before it, because the specs are written to hold either way and neither moves the task breakdown:

- Whether `draft-ietf-webtrans-http2` capsule framing is adopted in place of the bespoke frame vocabulary (D2's alternative). Evaluate before the contract's first version is frozen.
- Which challenge type is preferred for wildcard hostname verification, where more than one can prove control (`routing/custom-domains` requires that at least one work, not which).
