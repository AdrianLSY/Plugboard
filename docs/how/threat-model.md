---
type: guide
status: planned
authority: rationale
---

# The threat model

Every control below is specified. **None of it is built** — no product code exists yet
([start here](../start-here.md)) — so read this as an index into the sixteen specifications, not as a
description of a running system. The controls arrive with the tasks in
[`tasks.md`](../../openspec/changes/rebuild-plugboard/tasks.md).

The problem this note solves is that the controls are correct and *scattered*. Cookie scoping is in
one specification, the sidecar's refusal to be retargeted is in another, the bound that stops a
decompression bomb is in three, and no reader working through any single one of them can see the
adversary. This note names the adversary, the asset, the control, and **which specification owns the
control** — and where a control has no owning specification, it says so instead of guessing.

**This note states no behaviour.** Orientation is layer 4 of the precedence order: where a sentence
here and a specification disagree, the specification wins. Nothing here creates an obligation; each
row points at the artifact that does.

## The eight, at a glance

| # | Adversary | Asset at risk | Owning specification |
|---|---|---|---|
| 1 | A client, or an intermediary in front of the edge | Message boundaries on a shared connection | [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md) · [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) |
| 2 | Any client that can reach a mount | The tenant's internal network, reachable only from the sidecar | [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md) |
| 3 | Tenant B, sharing a hostname with tenant A | Tenant A's sessions | [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md) |
| 4 | A claimant of a hostname they do not control | A certificate for someone else's name; the control surface | [routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md) |
| 5 | An authenticated principal of another tenancy | Another tenant's mounts, credentials and claims | [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md) |
| 6 | Any client on the public internet | Every address the proxy's own network can reach | [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md) |
| 7 | A client on a stream, or a tenant's own backend | Shared proxy memory; the tenant's own machine | [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md) · [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md) |
| 8 | A reader of the store; any interface holder | Certificate keys, credential secrets, root material | [security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md) · [auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md) |

## 1 · Request smuggling

**Adversary** a client, or an intermediary in front of the edge. **Asset** where one message ends and
the next begins — control of it injects a request into another client's connection, or past the edge's
own checks.

- Framing is determined per hop from the connection the message arrived on, the framing fields are
  removed before the message crosses the tunnel, and each hop generates its own —
  *Message framing is generated per hop and never relayed*, [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
- A message whose framing indications disagree is **rejected, not reconciled**, with an enumerated
  reason — *Conflicting or ambiguous framing is rejected, not reconciled*, same specification, which
  names this in so many words as `"the request-smuggling surface"`. It enumerates the minimum
  rejection set: both length and coding present, repeated length fields whether or not they agree,
  a non-numeric or list-valued length, a coding list where `chunked` is not final, malformed chunk
  framing.
- Hop-by-hop removal covers the fields `Connection` *names*, not only the fields that are hop-by-hop
  by definition — so `Connection: Content-Length` cannot be used to make one hop reframe a message.
- Obsolete line folding, bare CR or LF inside a field section, and whitespace before a colon are
  rejected rather than repaired — *Malformed request lines and field sections are rejected at the
  edge*.
- The tunnel refuses to carry connection-scoped fields in either direction, and a receiver that finds
  one discards it and may not frame anything with it —
  [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md).
- The adversarial fixtures for these shapes are written before the code they gate —
  [tunnel/conformance](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md).

**Owner** the edge, for everything decidable from the connection; the wire contract, for the carried
header sequence. That per-hop split is
[D6 — framing authority is per-hop, never relayed](../decisions/d06-framing-authority.md).

## 2 · SSRF through the sidecar

**Adversary** any client that can reach a mount; also a tenant's own backend, answering with a
redirect. **Asset** the tenant's internal network and its cloud metadata endpoints — reachable from
the sidecar and from nowhere on the public internet. This is the most consequential row in the table:
the sidecar is a process the tenant runs *inside* their own perimeter.

- The backend origin comes only from local configuration — *The backend origin is taken only from
  local configuration*, [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md).
- **No component of a received request can influence the origin dialled.** The specification
  enumerates the vectors rather than gesturing at them: an authority field, an absolute-form target,
  the conventional forwarding fields, a field whose value is an internal or metadata address, the
  affinity key, body and trailer octets, a bidirectional establishment naming another authority, and
  a redirection from the backend. It requires the sidecar to apply the rule itself rather than rely on
  the edge having removed anything, and calls the property `"the single most consequential property in
  this capability"`.
- The path remainder is validated before any connection opens, and **rejection is never repair** — no
  sanitising, collapsing, decoding or re-encoding then proceeding.
- The sidecar refuses to start if its configured origin resolves to one of its own surfaces — *The
  sidecar's own surfaces are never reachable as a backend origin*.
- On the proxy side, the exchange is composed from the remainder plus method, fields and body **and
  nothing else**; the proxy conveys no origin, host, port or scheme intended to select a destination —
  [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md).
- An authority inside a request target never opens a connection toward the named host —
  *Authority-bearing request targets are resolved explicitly*, [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).

**Owner** `sidecar/program`, decisively — the specification's own framing is that in the prior art
this was *"the one genuinely good defence with no owner"*. The prior art's implementation is the piece
worth reusing and the piece worth distrusting at once: address-tuple matching over regex at
`hook.ex:247-257` with a metadata-endpoint list at `:25-38`
([carry-forward](../history/carry-forward.md)), and the same protection disabled suite-wide in the
test configuration at `reference/Plugboard/config/test.exs:96` with zero tests anywhere
([reference audit](../history/reference-audit.md)).

## 3 · Cross-tenant cookie scoping on a shared hostname

**Adversary** tenant B, on a hostname several tenants share by path prefix. **Asset** tenant A's
session cookies — the browser's own scoping rules do not distinguish two path prefixes on one host.

- Each `Set-Cookie` a backend emits has its path scope constrained to lie within the mount that
  produced it, and a domain scope that would widen it past the arrival hostname is removed or narrowed
  — including one naming a suffix at or above the registrable-domain boundary. Every field line is
  treated individually; none is merged, dropped or reordered. *Cookies a backend sets are scoped to
  that tenant's mount*, [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
- In the other direction, only cookies whose scope covers the matched mount are forwarded, and cookies
  arriving split across several field lines are recombined with the **cookie** separator, which is not
  the separator used for ordinary repeated fields — *Cookies a client presents are filtered to the
  matched mount*.
- On a hostname dedicated to one tenant both rules are inert, because no other tenant shares it.
- Session values do not cross a mount boundary on a shared hostname —
  [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md).
- A hostname claim is rejected where verifying it would let the claimant set cookies scoped to a
  reserved hostname — [routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md).
- None of the above survives a header map. Repeated fields cross the tunnel as an **ordered sequence
  of pairs**, and the wire contract carries a scenario for three separate `Set-Cookie` fields
  arriving as three — [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md).
  The prior art collapsed them in both directions and silently deleted every cookie past the first:
  `proxy_controller.ex:496` and `telephone.go:85`
  ([reference audit](../history/reference-audit.md)). `Set-Cookie` is the canary for the banned
  headers-as-a-map pattern for this reason — see [protocol fidelity](protocol-fidelity.md).

**Owner** `proxy/edge-hygiene`, resting on the ordered-header-list guarantee in `tunnel/wire-contract`.

## 4 · Certificate-issuance escalation from an unverified claim

**Adversary** a tenant claiming a hostname they do not control, or claiming a parent of a hostname the
platform reserves. **Asset** a publicly trusted certificate for someone else's name; the platform's
own control surface.

- A claim **confers nothing** until ownership is verified: no traffic served, and no certificate
  requested from any authority. Possession of an account, ownership of a mount, prior use of a related
  hostname, and claim order do not substitute — *A claim confers nothing until ownership is verified*,
  [routing/custom-domains](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md).
- Challenge values are unpredictable, valid for exactly one claim of one hostname by one tenant, and
  expire — so a value issued to one tenant cannot satisfy another's claim on the same name.
- The verification responder **belongs to the edge, never to a tenant**: the reserved challenge path
  is answered by the edge, crosses no tunnel, and a tenant's backend has no way to make the edge
  answer for a hostname it was issued no challenge for. Sibling paths under the same well-known
  ancestor still route to the tenant.
- Verification is re-checked and **lapses** — specifically for a name still delegated to the platform
  whose owner has released it.
- Competing claims are resolved by verification rather than order; wildcards are proved by delegation
  only; certificates cover only verified hostnames.
- The platform's own hostnames are reserved, evaluated *after* normalisation so a case, trailing-dot
  or internationalised variant is equally reserved, and a parent claim is rejected where verifying it
  would yield a certificate covering a reserved name.
- Where certificate material is supplied from outside, receipt validates that the certificate names
  only hostnames verified to the supplying tenant, and refuses with nothing written otherwise —
  [security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md).

**Owner** `routing/custom-domains`; `security/key-custody` for material arriving from outside. The
ordering is on the record as
[D9 — domain ownership verification precedes certificate issuance](../decisions/d09-domain-ownership.md).

## 5 · Cross-tenant writes

**Adversary** an authenticated principal of another tenancy — and, just as often, a caller inside the
system that forgot to check. **Asset** another tenant's mounts, credentials, hostname claims and
membership.

- **Authorization is intrinsic to the mutation.** Every mutation takes an identified principal as part
  of the invocation, the operation itself decides whether that principal holds the required authority,
  and a caller that performs no check of its own cannot cause an unauthorized mutation. A refusal makes
  no partial change. *Authorization is intrinsic to the mutation*,
  [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md).
- Every resource belongs to exactly one tenancy; every read is scoped to the requesting principal's
  tenancy; **knowing an identifier confers no access**; reclaiming a released name confers no access
  to prior state.
- Data-plane traffic never crosses a tenant boundary: selection, failover and affinity treat another
  tenancy's sidecar as if it did not exist, and a credential presented for a mount in another tenancy
  is refused **without confirming whether that mount exists**.
- Tenant attribution derives only from inputs the system established or verified — the matched mount,
  the authenticated hostname binding, the presented credential — never from an unverified client field.
- A credential is bound at issuance to one mount and one tenant, and the scope cannot be widened
  afterwards — [auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md).
- Every mutation lands in an append-only audit trail with the acting principal, and refusals disclose
  nothing about another tenant.

**Owner** `tenancy/isolation`, with `auth/sidecar-credentials` for credential scope. This is
[D8 — tenant scoping is a key and a signature, not a habit](../decisions/d08-tenant-scoping.md), and
the reason it is a decision rather than a convention is that the prior art broke it in both shapes:
`update_token/2` took no actor at all where its sibling `revoke_token/2` did
(`telephone_tokens.ex:353-363` vs `:175-181`), and `create_path` restored another user's soft-deleted
path and granted the caller the owner role (`paths.ex:219-241`, no user scoping on the `FOR UPDATE`
lookup) — both from the [reference audit](../history/reference-audit.md).

## 6 · Open relay via the tunnelling method

**Adversary** any client on the public internet. **Asset** every address the proxy's own network can
reach — which, for a proxy sitting in a platform's ingress, is a great deal.

- A request whose method asks the proxy to become a tunnel to an arbitrary destination is refused at
  the edge with an enumerated reason: no name resolution, no connection toward the named destination,
  no mount matched, no tunnel frame. The specification's own framing is that
  `"The proxy is not a forward proxy"` — *Tunnelling and reflecting methods are answered at the edge,
  never forwarded*, [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
- The **extended** form of that method — the one that names an upgrade protocol in a dedicated field —
  is explicitly *not* caught by the refusal, and is handled as an ordinary mount-destined
  establishment. A refusal written as a bare method match would break every HTTP/2 WebSocket client.
- The reflecting method is answered by the proxy or refused, never forwarded, so the fields the proxy
  added on the way through — including the client identity it established — are not returned to the
  caller.
- The method policy is a **closed enumeration held in exactly one capability**, and every method
  outside it is forwarded byte-identically, including one the proxy has never seen. This is the
  correct reading of the method-allowlist ban in [`CLAUDE.md`](../../CLAUDE.md): what is banned is an
  allowlist of *permitted* methods, not the two-entry refusal list that keeps the edge from being a
  relay.
- A request arriving already bearing this proxy's own intermediary identity is refused with a
  loop-detection status, so a tenant backend configured to call back through the proxy cannot recurse
  to a resource bound.
- The proxy's own endpoints are unreachable as tenant traffic; the tunnel listener serves
  establishment and nothing else, and no client request reaches it —
  [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md).

**Owner** `proxy/edge-hygiene` for the method policy, `tunnel/listener` for its own surface.

## 7 · Compression amplification

**Adversary** a client on a bidirectional stream, or a tenant's own backend on the backend hop.
**Asset** shared proxy memory — and, on the sidecar side, the tenant's own machine, which the sidecar
shares with the application it exists to serve.

The magnitude is what makes this an isolation concern rather than a bandwidth one: [the
tunnel](the-tunnel.md) puts it at a ~6 MiB compressed frame inflating to ~6 GiB, a whole-node kill.

> **Unverified.** That ~1000:1 figure is the vault's own estimate and is not traced to a source in
> this repository. RFC 1951 is not the place to check it: that document states DEFLATE's worst-case
> *compression* expansion (five bytes per 32 KiB block), not a decompression ratio, and specifies no
> maximum inflation at all. The figure needs an empirical bound measured against the chosen
> decompressor before it is quoted as anything but an order of magnitude.

- Compression is negotiated **per hop and does not exist end to end**. The proxy decompresses an
  incoming frame and places untransformed octets on the tunnel with the indicator clear; an indicator
  set on a hop that negotiated no compression is a protocol violation —
  [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md).
- *Message size after decompression is bounded*, enforced **incrementally**, so the memory held never
  exceeds the bound however small the compressed form was. The specification carries the scenario for
  a compressed message far smaller than the bound whose decompressed size greatly exceeds it.
- The identical obligation binds the sidecar on the backend hop, with its own configured bound and its
  own reason code — [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md).
  Its rationale is the sharper one: the sidecar shares a machine with the tenant's application.
- Octets are accounted **after** any expansion the holding hop performs, so a small compressed input
  is charged what it actually occupies — and a payload forwarded without expansion is never expanded
  merely to account for it. [tenancy/isolation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md),
  whose closed enumeration of per-tenant dimensions covers octets in flight and octets buffered.
- The declared maximum frame payload is enforced at the boundary, and the header section is bounded
  separately with a code that distinguishes the two —
  [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md).
- The request/response primitive has **no** amplification surface here at all, because the proxy
  neither decompresses, recompresses nor re-codes a response body —
  [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md).
  The exposure is confined to the frame-stream primitive.

**Owner** three capabilities, one per hop: `proxy/websocket` (client hop), `sidecar/program` (backend
hop), `tenancy/isolation` (the accounting that makes either bound a per-tenant fact rather than a
per-process one).

## 8 · Credential and key custody

**Adversary** a reader of the durable store; a holder of any interface the platform exposes,
including one at the highest authority it defines; a reader of logs and diagnostics; a tenant simply
asking for the key. **Asset** certificate private keys, the listener's endpoint identity, credential
secrets, protection material, root material.

- The inventory of custody-managed material is **enumerated and closed** — material nobody enumerated
  is material nobody rotates — [security/key-custody](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md).
- Material at rest is unusable to a reader of the store alone, and protection material does not live
  where the protected material lives.
- **No interface returns private key material** — tenant-facing, operator-facing, diagnostic, support,
  export or backup. Material can be used, replaced and destroyed through the platform's interfaces and
  read back through none of them; the specification carries the scenario for a principal holding the
  highest authority the platform defines attempting every exposed operation.
- Material never crosses the tunnel and never leaves its trust boundary: no certificate private key is
  sent to a tenant, a sidecar or a backend, on request or otherwise.
- There is **no escrow and no recovery path**; unrecoverable material is reported as such rather than
  worked around. Replacement carries fresh material, never the outgoing key, and material is not
  carried across a hostname's removal-and-reclaim or a change of hands. Destruction is verifiable
  across every holder, and a destroyed item does not come back.
- On the credential side: the system generates the secret and the caller cannot influence it; it is
  presented exactly once; stored state cannot be turned back into a credential; the sidecar protects
  its own stored credential at rest; authentication failures are indistinguishable to the presenter
  while the audit trail distinguishes them; every credential-accepting endpoint is rate limited on an
  **unforgeable** attribute — [auth/sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md).
- No secret appears in any emitted signal, and redaction is applied where signals are produced so a
  newly added call site cannot bypass it —
  [operability/observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md).
  The sidecar carries the same obligation at every verbosity —
  [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md).
- The tunnel's own hop is protected above a floor that configuration can raise and cannot lower, with
  no setting that admits a connection below it — [tunnel/listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md).

**Owner** `security/key-custody` for material, `auth/sidecar-credentials` for credentials,
`operability/observability` for signals, `sidecar/program` for the tenant-side store.

## Gaps — controls with no owning specification

This is the useful half of the page. A gap here is not a refusal: the refusals, with their reasons,
are in [scope refusals](../why/scope-refusals.md). A gap is a control that nothing in the sixteen
specifications claims, found by searching the specifications for the control before attributing it.

| Gap | How it was established | Consequence, as far as the vault records it |
|---|---|---|
| **CORS, and `Access-Control-Expose-Headers` in particular.** No specification names either. | A search of all sixteen specification files for `CORS` or `Access-Control` returns nothing. | [Scope refusals](../why/scope-refusals.md) records this as a known hole rather than an assumed owner, and carries the standards claim behind it: RFC 9725 §4.2 makes honouring CORS the difference between a browser WHIP client that can read `Location` and `Link` and one that cannot. Sharpened by two adjacent facts: proxied traffic explicitly has no cross-site-request protection applied to it, and the proxy *does* rewrite absolute references such as `Location` at a mount boundary — so a rewritten field and a backend-issued expose-headers list have to agree, and no requirement says they must. |
| **`Strict-Transport-Security`.** No specification names it, and nothing decides whether the platform or the tenant owns it. | A search of all sixteen for `Strict-Transport` or `HSTS` returns nothing. | The unencrypted listener answers the verification challenge and otherwise issues a permanent redirect to the secure scheme, and the proxy is forbidden from adding a security-policy field of its own to a *proxied* response. So if the platform is to emit HSTS anywhere it would be on that edge-generated redirect — and no requirement states whether it does. Named here as undecided, not as an obligation. |
| **The provenance of the ~1000:1 inflation figure.** | See the unverified marker in §7. | A bound is being justified by a magnitude nothing in the repository sources. Cheap to close; cheaper still to notice. |

Adding a control to a specification without adding it here, or closing one of these gaps without
striking the row, is the drift this vault exists to prevent — the note is only worth reading while its
rows are the specifications' rows.

## Read next

- [Failure taxonomy](failure-taxonomy.md) — every refusal named above has to be observable as
  something other than a generic 500, which is what the typed error codes in
  [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
  are for.
- [Protocol fidelity](protocol-fidelity.md) — three tiers of what must survive a round trip; the
  `Set-Cookie` and framing rows above are its rows too.
- [The tunnel](the-tunnel.md) — the frame vocabulary the isolation bounds are expressed in.
- [Scope refusals](../why/scope-refusals.md) — what is deliberately not defended, with the reason.
- [Reference audit](../history/reference-audit.md) · [Carry-forward](../history/carry-forward.md) —
  the prior art's failures and its two genuinely good defences.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
