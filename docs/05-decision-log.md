# Decision log

Decisions with rationale, alternatives, and reversals. **If you disagree with one, read its entry
first** — it may already have been argued, or already reversed once.

Status values: **Decided** · **Open** · **Reversed** (superseded, kept for the reasoning).

---

## D1 · Rebuild from scratch, reference as prior art only

**Decided.** The reference does not work: `POST` bodies arrive empty, binary payloads are corrupted,
neither container boots. Its defects are ceilings frozen into the wire schema, not accumulated bugs.

**Alternative considered:** restructure the existing code, keeping the 20,810 lines of Elixir tests as
an executable specification. **Rejected** once the audit showed the suite is bimodal — the
asynchronous and distributed half is worthless or actively self-defeating, and the synchronous half is
enumerated in [carry-forward](06-carry-forward.md) instead. The tests are a *citation list*, not a
foundation.

---

## D2 · One repository

**Decided.** Replaces two git submodules whose sync workflow auto-committed unreviewed pointer updates
to the parent's `main` on every push to the sidecar's `main`.

**Explicitly not a solution to the contract problem.** A monorepo makes the *repository* consistent
and does nothing for production, where sidecar versions spread without bound. It is actively dangerous
if it lulls anyone into assuming the two halves agree. See D3.

---

## D3 · Contract-first, with a conformance suite

**Decided.** A versioned schema is the root artifact; types are generated for every implementation; an
executable conformance suite is the authority on the contract.

**Why it is mandatory rather than nice:** the reference asserts its wire contract twice, independently,
against two different fictions. `Phoenix.ChannelTest` replaces the serializer with a no-op (provable:
`telephone_channel_test.exs:101` asserts an *atom* key that cannot survive JSON), and the Go tests
marshal a struct whose tags production never uses. `proxy_res` has zero key-level assertions on either
side.

**Alternatives considered:** (a) shared schema with codegen but no conformance suite — kills type drift
but leaves the two-fictions gap; (b) hand-written types plus one docker-compose end-to-end test —
cheapest, but drift prevention depends on discipline rather than tooling. Both rejected because version
skew is permanent (D4) and discipline does not survive it.

**Secondary benefit:** it makes "a sidecar in any language" real, which is the best-scoped
high-status contribution an outside contributor can make.

---

## D4 · Version skew is the governing constraint

**Decided as a framing, not a feature.** You deploy the proxy; tenants deploy sidecars on their own
schedule or never. Consequences that flow from this and appear throughout:

- The wire schema is the only irreversible artifact → sort work by reversibility, not cost.
- Capability negotiation is mandatory (D8), because selection round-robins across mixed versions.
- Anything requiring the sidecar to change is expensive forever.

---

## D5 · Positioning: multi-tenant platform ingress

**Decided by the owner**, against a recommendation for self-hosted dev tunnels.

**The recommendation was:** dev tunnels as the front door — demoable in 30 seconds, proven demand, and
contributors can use it themselves, which is the strongest predictor of whether anyone contributes.
Multi-tenant routing, autoscaling and NAT traversal would then be extensions rather than competing
pitches.

**The owner chose multi-tenant ingress.** It is the more impressive systems claim and it is where the
architecture already leans (domain affinity, hooks, service accounts). The cost, priced explicitly:

| becomes foundational | where the reference fails it |
|---|---|
| tenant-scoped projections | `mount_store.ex:402` — global full-table `SELECT` + full-keyspace ETS diff on any tenant's change |
| authorization as a signature, not a habit | `telephone_tokens.ex:353` — `update_token/2` takes no actor; cross-tenant write |
| per-tenant blast radius + audit trail | one bounded queue in the whole system; no backpressure; no logs; no per-tenant metrics; no audit log |

Dev tunnels would have let all three be deferred. Multi-tenant ingress does not — a prospect's first
question is what stops tenant A from affecting tenant B, and the answer has to be architectural.

---

## D6 · Three primitives, not per-protocol handling

**Decided.** See [Architecture](02-architecture.md) and [Protocol fidelity](04-protocol-fidelity.md).

**Alternative considered:** per-protocol code paths, which is what the reference did. Rejected because
it produces one path per protocol and the paths diverge — demonstrated by the same codebase
base64-encoding WebSocket frames correctly (`websocket.go:201`) while corrupting HTTP bodies
(`telephone.go:853`).

---

## D7 · The tunnel exchange is frame-shaped

**Decided.** Stream ids, credit windows, and the full frame vocabulary reserved at v1 even where
unimplemented. This deletes the correlation-id machinery and both of its critical bugs.

**Open sub-decision:** whether to adopt `draft-ietf-webtrans-http2` capsule framing verbatim instead of
a bespoke vocabulary. Strongly worth it — it provides stream ids, FIN, reset codes, session and
per-stream flow control, and a standardised discard-on-overflow datagram class, with a conformance
target. Blocker: no publicly available HTTP/2 WebTransport server library exists in any language, so
adopting it means hand-writing draft-conformant capsule framing. **Resolve before freezing v1.**

---

## D8 · Capability negotiation with refusal, not degradation

**Decided.** The proxy refuses what a connected sidecar cannot back, with an explicit status and
reason.

**Alternative considered:** best-effort degradation. Rejected — silent fidelity differences between two
requests to the same URL are undebuggable. Concretely: a v1 sidecar that buffers whole responses will
not *error* on a server-streaming call, it will hang until the timeout.

---

## D9 · Runtime · **REVERSED once**

**Current decision:** Elixir/Phoenix proxy · Go sidecar · separate Go HTTP/3 + WebTransport terminator
later if needed.

**Previously recommended, then overturned:** Rust proxy + Rust sidecar, on the premise that
WebTransport requires HTTP/3 termination in the same process as the tunnel, which would eliminate the
BEAM on capability grounds.

**Why it was overturned.** An adversarial reviewer checked the premise and found it built on
fabrications:

| claim | finding |
|---|---|
| `tokio-quiche` is the Rust stack for QUIC/H3/**WebTransport** | Neither `quiche` nor `tokio-quiche` implements WebTransport. `cloudflare/quiche#1114` open since 2021-12-11; Cloudflare, 2025-08-26: *"we can't commit to any timeline or prioritization."* No WebTransport item in either published API. **The recommended stack cannot do the thing it was recommended for.** The real Rust path is `wtransport` (single primary maintainer) or `web-transport-quinn` — with no escape hatch behind them. |
| MDN: *"WebTransport exclusively uses HTTP/3 and does not fall back to HTTP/2"* | **Sentence does not exist** on the page or in `mdn/content` source. The entire "same process, therefore no BEAM" chain rested on it. |
| Tokio: *"preemption is out of scope… for the foreseeable future"* | **Not on the cited page.** The post exists to *announce* the mitigation — a 128-operation per-task budget since 0.2.14. |
| Pingora: 70% less CPU, 67% less memory, nginx→Rust | Figures accurate, **attribution wrong.** Cloudflare credits *"our new architecture which can share connections across all threads… less time on TCP and TLS handshakes"*, and the language comparison is against **Lua**, not C. The measured win (5 ms median TTFB, 80 ms p95) came from eliminating round trips. |
| "No Go equivalent" | **False.** `quic-go` powers **cloudflared** — structurally this exact product — plus `frp`, `reverst`, Caddy, Traefik. |

**And WebTransport can be front-proxied.** `w3c/webtransport#525`, Lucas Pardue (WebTransport WG):
*"reverse proxies that want to support WebTransport will need to implement it… The simplest approach is
to implement support for WebTransport over HTTP/2 or HTTP/3 when speaking to the origin."* Chromium's
stated motivation for WT-over-H2 is *"a protocol we can use for proxy-to-backend communication"* — this
system's tunnel hop. Caddy PR #7669 bridges bidi streams, uni streams and datagrams across that
boundary today, with measured results.

**Decisive factor.** Once WebTransport stops forcing the runtime, what remains is the work that must
get finished: a distributed sidecar registry with failover, hot-reloadable routing, per-tenant crash
containment, and a live multi-tenant admin console. The reference has all four working on the BEAM;
rewriting them is weeks of hand-written bulkheads, a gossip or etcd layer, and an admin plane rebuilt
as `axum` + templates + htmx.

**On the owner's stated criterion** — *"I don't mind Rust if the performance gain outweighs development
speed"* — the antecedent is not satisfied. No verified performance advantage for this shape exists in
any of the three runtimes, and the request path is at minimum two wide-area round trips, one into a
network the operator does not control, around per-request compute that is header parse plus prefix
match plus byte copy. The rule therefore selects development speed.

**Corrected framing of the fault-isolation argument** (the original overstated it): the BEAM wins
*crash containment* and hands you `max_heap_size` as a per-process cap. It does **not** hand you
backpressure, and backpressure is the harder and more load-bearing half of the isolation promise. Also
note the reference's own containment is coarser than it looks — one process per sidecar carries all of
that tenant's traffic, so a crash there kills every in-flight request for that tenant *and* is the
head-of-line block. Fixing that needs a process or task per stream **in any runtime**.

**Strongest surviving argument against the current decision:** Bandit implements neither HTTP/3 nor
RFC 8441 extended CONNECT (issues #27, #91, #690 open). The second bites without WebTransport — behind
an h2-terminating CDN, WebSocket upgrades arrive as extended CONNECT and fail. HTTP/2 to clients is
also where real per-stream flow control lives. Mitigation: every edge protocol sits behind the versioned
contract, so the terminator is a swappable contract speaker.

**If Rust is ever chosen anyway:** the H3/WT layer must be `wtransport` or `web-transport-quinn` behind
a narrow swappable trait. `tokio-quiche` is not an option for this requirement and must not be written
into a plan as one.

---

## D10 · WebTransport designed-for, not shipped

**Decided.** The owner's stated need: *"for now, nothing, but I want the capability there… it's more
for future proofing."* That is a design constraint, not scope.

**What that buys and costs.** Reserving the `DATAGRAM` frame type and stream-oriented framing costs
essentially nothing. The expensive part — extended CONNECT plus capsule framing at the edge — has
**zero reuse** for SSE, streaming or WebDAV, whereas the tunnel work WebTransport motivates
(incremental emission, binary frames, per-stream interleaving, flow control) is *already mandatory* for
SSE and large downloads. So sequence the tunnel work first; it pays for itself either way.

**The trap this avoids.** Building v1 on TCP "with a swappable transport layer" would reproduce the
reference: TCP gives one ordered stream, so you invent correlation ids, a pending map, one-reply-per-
request, and no backpressure — because that is what TCP forces. Swapping to QUIC later then means
deleting the core of the tunnel. **Define the primitive first (independent streams + datagrams);
implement any TCP transport as an emulation of it.** Not the reverse.

---

## D11 · Proxied traffic terminates before application middleware

**Decided.** No body parser, no method override, no HEAD folding, no content negotiation, no session,
no CSRF. Direct cause of the reference's worst defect (`endpoint.ex:118` before `:134`).

Note the reference *half*-learned this: the `/call` pipeline deliberately removed `:accepts` with a
comment saying proxies should be content-agnostic, while the domain-affinity pipeline — the one custom
domains use — kept `plug(:accepts, ["json", "html"])` at `router.ex:157`. The fix was applied to one
path and not the other.

---

## D12 · Framing authority is per-hop, never relayed

**Decided.** `Content-Length` and `Transfer-Encoding` are per-connection properties; each hop generates
its own. A message with both is rejected with 400, not reconciled. **This is the request-smuggling
surface**, and the reference relays `Content-Length` verbatim (`proxy_controller.ex:445`) over a body
path that changes the byte length.

---

## D13 · Tenant scoping in the data model

**Decided.** Every projection tenant-keyed; every context mutation takes the acting principal in its
signature. Authorization is a property of the function signature, not something a caller may remember —
`telephone_tokens.ex` demonstrates both halves, since `revoke_token/2` authorizes and `update_token/2`
does not.

---

## D14 · Domain ownership verification precedes certificate issuance

**Decided, and it is a v1 blocker.** Layering ACME onto a first-come unverified domain claim escalates a
routing bug into obtaining a publicly trusted certificate for a domain the claimant does not own. Also
guard dangling-CNAME takeover.

---

## D15 · Observability before the hot path

**Decided.** A metric sink and a structured logger chosen in week one, with a telemetry-attach test as
the gate. The reference emits 75 telemetry events, attaches zero handlers, and contains one
`"Logger."` occurrence in 14,600 lines — inside a doc comment claiming errors are logged. Five of
seven auditors cited the telemetry as evidence of good instrumentation.

---

## Open questions

| question | why deferrable | resolve by |
|---|---|---|
| **Schema technology** — binary IDL vs text envelope with base64 bodies | Changes generated code, not the frame vocabulary or type choices. Does not move specs or tasks. | during `tunnel/wire-contract` |
| **Tunnel transport for v1** — WebSocket, raw TLS, or HTTP/2 stream | Deferrable *only because* D7 makes framing transport-independent | during `tunnel/wire-contract` |
| **`draft-ietf-webtrans-http2` capsules vs bespoke frames** | See D7 | before freezing v1 |
| **Is HTTP/2 to clients in v1?** | **Not safely deferrable** — changes the edge topology and interacts with Bandit's missing RFC 8441 | before `proxy/websocket` specs |
