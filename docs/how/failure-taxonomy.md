---
type: essay
status: current
authority: rationale
---

# The failure taxonomy

One failure, three viewpoints. A bound that elapses in the tenant's network is, at the same instant,
a truncated download to somebody's browser, a line in a sidecar's local diagnostic, and an
enumerated cause in an operator's record. The three views are deliberately not the same view, and
most wasted debugging time in a system shaped like this one is spent assuming they are.

The three parties here are the ones in the [orientation diagram](../start-here.md#orientation-in-one-screen):
the **client** that dialled the edge, the **tenant** who runs the sidecar next to their backend, and
the **operator** who runs the proxy. They are not the three audiences of
[who it is for](../why/audiences.md) — that triple is operators, contributors and the portfolio, and
it answers a different question.

**None of this is built.** The specifications linked below are planning artifacts of an unstarted
change ([tasks](../../openspec/changes/rebuild-plugboard/tasks.md)). This note is an index into them
and states no behaviour of its own; where a sentence here and a linked specification disagree, the
specification wins.

## Who can see what, and why they differ

| | can reach | cannot reach |
|---|---|---|
| **client** | the status and reason on a refusal; a close code and reason on a stream; the absence of the rest of a response | anything after the response head is committed — no status, no diagnostic ([commit point](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-the-response-head-is-the-commit-point)) |
| **tenant** | the sidecar's own local diagnostics — per-exchange phase, age, waiting condition, octets, all answerable while the tunnel is unresponsive ([sidecar diagnostics](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-an-operator-inside-the-tenants-infrastructure-can-diagnose-without-proxy-access)) | the proxy |
| **operator** | one outcome record per exchange, elapsed time attributed to enumerated phases, the degraded-condition inventory, every accept-path refusal by cause ([observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-exchange-produces-exactly-one-outcome-record)) | the tenant's backend |

Two of those gaps are load-bearing rather than incidental.

- **Some differences are privacy.** At the tunnel's accept path a refusal is specific to the operator
  and opaque to an unauthenticated peer, and inside the capacity and timeout classes nothing
  separates one instance of the class from another — because occupancy figures describe what other
  tenants hold ([listener](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-a-refusal-is-specific-to-the-operator-and-opaque-to-an-unauthenticated-peer)).
  Authentication failures go further: unknown, expired and revoked are one indistinguishable outcome
  to the presenter, and the audit trail is the thing that
  [distinguishes what the presenter cannot](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-the-audit-trail-distinguishes-what-the-presenter-cannot).
- **Some differences are topological.** No probe spans both hops, so the backend hop's liveness is
  the sidecar's to prove and the proxy's only to attribute
  ([liveness](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-backend-hops-liveness-is-the-sidecars-to-prove-and-to-report)).
  The same asymmetry is why one of the six bounds below is not the proxy's to enforce.

## Class 1 — a bound elapsed

Six separately named bounds, not one request timeout. That shape is
[D7 — timeout taxonomy replaces the single cap](../decisions/d07-timeout-taxonomy.md), and the five
the proxy enforces plus the one it does not are fixed by
[timeout bounds are separate and independently configurable](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-timeout-bounds-are-separate-and-independently-configurable).

| bound | enforced by | notes |
|---|---|---|
| edge header-read — the client's request header section arriving | proxy | [own requirement](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-the-client-request-header-section-is-bounded-at-the-edge) |
| tunnel connect — obtaining a usable tunnel to a sidecar serving the mount | proxy | distinct from an absent sidecar and from an unreachable backend ([three-way distinction](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-tunnel-availability-and-origin-connection-are-distinguishable-failures)) |
| time-to-first-byte — request head dispatched until response head arrives | proxy | [own requirement](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-time-to-first-byte-is-bounded-separately-from-total-duration) |
| idle between body octets, either direction, measured at its own hop | proxy | [resets on delivery](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-idle-between-body-octets-is-bounded-and-the-bound-resets-on-delivery) |
| total duration of the exchange | proxy | one route class has no total bound at all ([timeout classes](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-every-route-carries-a-timeout-class-and-one-class-permits-an-unbounded-total)) |
| origin connect — the sidecar reaching the tenant's backend | **sidecar** | configured and enforced locally; the proxy only attributes it ([sidecar's own bounds](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-backend-connection-bounds-are-the-sidecars-own-and-distinct-from-the-proxys)) |

Six bounds is a refusal of an assumption rather than a larger number. The prior art had one global
cap of 300s over the whole buffered exchange, which is why an event stream could not exist on it —
`path.ex:67` and `proxy_controller.ex:246`, citations taken from the
[reference audit](../history/reference-audit.md) rather than checked afresh here.

The consequence for a reader is the one D7's note draws: "the request timed out" is never a complete
account, because every terminating condition names the bound that ended it
([distinct causes](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-every-terminating-condition-is-recorded-with-a-distinct-cause)).
A long-lived bidirectional stream is governed by its own idle and lifetime bounds, separate again
from these, with the idle close distinguishable from the lifetime close
([stream bounds](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-idle-and-lifetime-bounds-are-separate-from-request-bounds)).

## Class 2 — refused, because nothing could back it

The refusal class exists because of [D3 — capability negotiation](../decisions/d03-capability-negotiation.md):
a request no connected sidecar can back is refused with a stated reason instead of served at lower
fidelity. Two shapes, and they are visible to different parties.

- **Before dispatch.** The required capability set is derivable from the request head and the route's
  class, and eligible sidecars are filtered by capability *before* one is selected — so the refusal
  names each missing capability
  ([refusal rather than silent degradation](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-refusal-rather-than-silent-degradation),
  [filtered before selection](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-eligibility-is-filtered-by-capability-before-selection-not-after)).
- **After dispatch.** A need that only becomes apparent once the backend has answered — a trailer
  section reaching a sidecar that declared no trailer support — resets the stream with a code naming
  the capability, and the client observes a truncated response rather than one whose trailers were
  quietly dropped. Same requirement as above; it is the case worth reading twice.

"No sidecar available" is its own outcome rather than a variant of a timeout
([registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-no-sidecar-available-is-its-own-outcome)),
and a tenant that has deployed no sidecar is recorded differently from one whose sidecar is held by
an instance this one cannot reach — the whole point being that the two are not investigated the same
way. The operator's counterpart to a refusal storm is the deployed contract-version and capability
spread, which is required to be observable
([spread](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-deployed-contract-version-and-capability-spread-is-observable)).

## Class 3 — a reset, and the code space it stays out of

Stream reset codes and tunnel error codes are drawn from one partitioned code space, with a code's
class derivable from the code itself so an unrecognised code is still actionable
([errors are machine-readable](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-errors-are-machine-readable)).
Three boundaries inside that class are the ones that get confused:

- **Stream-fatal versus tunnel-fatal.** A frame that is well formed but cannot be acted on costs one
  stream; framing that cannot be trusted costs the tunnel, with no resynchronising
  ([malformed framing](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-malformed-framing-is-tunnel-fatal-and-unusable-frames-are-stream-fatal)).
- **The application-reserved range.** Tenant applications encode their own error taxonomies in it, so
  a proxy-originated close is drawn from a documented vocabulary outside it — otherwise a
  proxy-generated code is indistinguishable to a client from an error its own backend raised
  ([close vocabulary](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md#requirement-proxy-originated-closes-come-from-a-documented-vocabulary)).
- **One vocabulary, not two.** Each way the backend hop can fail is a published code of the
  contract's own enumeration rather than a set the sidecar invents, and never a description attached
  to a broader code, because a description is text no receiver may branch on
  ([backend failures](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-backend-failures-are-distinct-outcomes-the-contract-can-carry)).

## Class 4 — the enumerated error space

An index, not a definition: each group below is owned by the linked requirement, which is where the
conditions and their names actually live.

| enumeration | conditions at version 1 | owner |
|---|---|---|
| contract, general | version incompatibility · malformed version declaration · authentication or authorisation failure · credential no longer valid · undeclared or baseline-violating capability · unimplemented or unrecognised frame kind · tunnel protocol violation · flow-control violation · declared parameter exceeded · a mount the receiver was not admitted for · a destination it refuses to originate against · malformed method, field or target · cancellation by the originator · exchange abandoned because the tunnel ended · drain in progress · unspecified failure | [errors are machine-readable](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-errors-are-machine-readable) |
| contract, far hop | host unresolvable · connection refused · connect bound exceeded · origin identity unverifiable · no response head within bound · body idle beyond bound · origin failed after its response head · origin stopped answering on an established stream · protocol violation of that side's own hop | same |
| contract, framing translation | malformed frame in the carried body · length beyond the configured bound · section over its maximum · a field the target framing cannot express · an origin that ended without the required section | same |
| proxy-generated errors | no mount matched · no eligible sidecar · no usable tunnel path · a capability no eligible sidecar declared · trailer emission the client's protocol cannot express · incremental transfer no sidecar declared · backend not connectable · each timeout bound separately · each admission bound separately · header-section bound · request-body size bound · draining · backend failure before commit | [distinguishable per cause](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-proxy-generated-error-responses-are-distinguishable-per-cause) |
| per-exchange outcomes | completion · refusal before a sidecar was reached · no sidecar available · refusal for an undeclared capability · cancellation by the client · cancellation by the backend · each class of exceeded time bound · each class of exceeded resource bound · each cause a stream is closed by the proxy · tunnel failure in flight · loss of the instance holding the tunnel in flight | [one outcome record](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-exchange-produces-exactly-one-outcome-record) |
| accept-path refusals | protection policy · absent framing identification · unserved framing identification · oversized pre-authentication read · unauthenticated timeout · pre-authentication bound · total connection bound · rate limit · authentication failure | [specific to the operator](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-a-refusal-is-specific-to-the-operator-and-opaque-to-an-unauthenticated-peer) |
| connection phases | accepted · protection being established · framing being identified · awaiting the establishment declaration · credential being evaluated · established · draining · ended | [enumerated phase](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-every-connection-is-attributable-to-an-enumerated-phase-while-it-is-open) |

These are separate enumerations with one registry over them: every enumerated cause maps to exactly
one outcome value, and the connection-level vocabularies are deliberately *not* mapped into the
per-exchange set — a connection that never authenticates produces no exchange to attribute an
outcome to
([the registry rule](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-enumerated-cause-in-the-system-maps-to-exactly-one-outcome-value)).
Alongside the outcome, elapsed time is attributed to enumerated phases, and a phase an exchange never
entered is reported as not entered rather than as zero
([phases](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-elapsed-time-is-attributed-to-enumerated-phases)).

## Class 5 — silence

The class a ticket actually gets filed about, and the reason this note exists rather than a list of
status codes.

The project's own worst case is recorded in [scope refusals](../why/scope-refusals.md#webrtc-media-and-data-channels):
WebRTC media fails with a `201 Created` and then nothing, about thirty seconds later, with clean logs
on both sides. Everything else in the system is designed to fail loudly. That failure is
unattributable *by construction* — the traffic is out of scope, so no specification here owns a
condition for it and nothing in the system will ever name it. Documenting it where a tenant will look
is the whole mitigation, which is why the refusal note carries it and this one points at it. The same
page records the neighbouring gap: no specification names CORS, and a browser WHIP client that cannot
read `Location` fails in this class too.

Inside the supported surface, four shapes come close to silence, and each is made legible by a
specific requirement rather than by good intentions:

| looks like nothing happened | what makes it legible |
|---|---|
| a response that stops mid-body — no status, no error content, because the head was already committed | the client detects incompleteness against the declared length or framing, and the record states the failure was after commit ([commit point](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md#requirement-the-response-head-is-the-commit-point)) |
| a sidecar that never connects, so no exchange exists for exchange-shaped diagnostics to find | the connection-phase enumeration, obtainable per open connection with its time in phase ([phases](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-every-connection-is-attributable-to-an-enumerated-phase-while-it-is-open)) |
| a backend that accepted the stream and then went quiet | only the sidecar's own keepalive can find it; expiry becomes a reset the proxy can attribute to the backend rather than the tunnel ([liveness](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-backend-hops-liveness-is-the-sidecars-to-prove-and-to-report)) |
| a refusal that reads as "tenant at its ceiling" but is really "we could not tell where the tenant stood" | degraded accounting is itself an enumerated degraded condition, and the refusal is distinguishable *to the operator* from a real bound ([partition discipline](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-bound-accounting-under-partition-follows-a-declared-discipline-with-bounded-and-recorded-overshoot), [degraded inventory](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-degraded-operation-is-announced-for-as-long-as-it-persists)) |

The last row is the three-audience point in its sharpest form: that refusal is required to be
distinguishable to the operator and required *not* to be distinguishable to the tenant presenting the
credential. A taxonomy that flattened the three views into one would have to call that a
contradiction.

Where silence is what a tenant reports, the two diagnostics designed for it are the proxy-side
[stuck-exchange diagnostic](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-a-stuck-exchange-can-be-diagnosed-from-one-place-while-it-is-stuck)
and the [registry inspection](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-registry-is-inspectable-while-a-tunnel-is-stuck),
with the sidecar's local answers as the tenant's half. The waiting conditions the two sides report
are drawn from the same published enumeration, so an operator and a tenant describing one stuck
exchange use the same words.

## Read next

- [D7 — timeout taxonomy](../decisions/d07-timeout-taxonomy.md) and [D3 — capability negotiation](../decisions/d03-capability-negotiation.md) — the two decisions this taxonomy is mostly an unfolding of.
- [Scope refusals](../why/scope-refusals.md) — the silent class, and the refusals that are refusals.
- [Protocol fidelity](protocol-fidelity.md) — what has to survive a round trip, which is what most of these conditions are protecting.
- [The architecture](architecture.md) — the hub, if you arrived here first.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
