---
type: guide
status: planned
authority: rationale
---

# The operator's view

You deploy the proxy. Tenants deploy sidecars into their own infrastructure, on their own schedule,
or never — [version skew](../why/version-skew.md). This note is your half of that split: what you
install, what you must configure before anything starts, what you can watch, and what a tenant's
"our tunnel is stuck" looks like from your side.

> **Planned.** None of this exists in the tree. There is no `proxy/`, `sidecar/` or `terminator/`
> directory and no operational surface; what exists is the obligation. The work that builds it is
> [tasks section 5](../../openspec/changes/rebuild-plugboard/tasks.md#5-configuration-validation-provenance-and-operational-surfaces)
> — configuration validation, provenance and operational surfaces — and
> [tasks section 6](../../openspec/changes/rebuild-plugboard/tasks.md#6-observability-substrate-signals-redaction-and-the-attach-gate),
> the observability substrate.

**Nothing here states behaviour.** Every row below links to the requirement that owns it; where a
sentence here and that requirement disagree, the requirement wins. A diagnostic or a signal not
linked below is one this note is not entitled to promise you.

The proxy is a multi-instance installation in v1 ([D20](../decisions/d20-multi-instance.md)), so
every answer you get is an answer about an *installation* and not about whichever instance your load
balancer picked. That single fact shapes every section that follows.

## What you install

One artifact per separately deployed component, and nothing you have to assemble.

| what you get | the requirement that owns it |
|---|---|
| Exactly one artifact per separately deployed component, with the operator-run components not exempt | [one artifact per component](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-every-deployable-component-releases-as-exactly-one-artifact) |
| It starts without fetching its own parts, and declares what it needs from outside | [self-contained, declared dependencies](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-carries-everything-it-needs-to-start-and-declares-what-it-needs-from-outside) |
| A verifiable identity that depends on content rather than on where you obtained it | [verifiable identity](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-carries-a-verifiable-identity-independent-of-where-it-was-obtained) |
| It starts unprivileged and writes only where it declared it would | [no more privilege than needed](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-requires-no-more-privilege-than-the-component-needs) |
| Provenance fixed when the artifact was produced — no deployment, no configuration item, no peer can restate it | [provenance is not configurable](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-provenance-is-fixed-when-the-artifact-is-produced-and-no-deployment-can-alter-it) |
| Whether two builds can serve each other, decided from the stopped artifacts rather than by starting them | [pairing viability](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-pairing-viability-is-determinable-from-the-artifacts-alone) |
| Whether a build is too old for the durable state you already have, before you deploy it | [declared durable schema range](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-each-artifact-declares-the-durable-schema-version-range-it-supports-readable-without-running-it) |

The "separately deployed component" enumeration those obligations bind is the proxy, the sidecar,
and the component that terminates client-facing protocols, named as such where the provenance
requirement refuses to be stated of only some of them
([build provenance](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-component-reports-its-build-provenance)).
See [topology](topology.md) for why that third one exists.

## What you configure

Configuration is a schema, validated once, before anything accepts a connection.

- **One pass, every failure named.** Every failing item across every capability is reported in a
  single refusal, before any listener, tunnel endpoint or probe surface accepts a connection, and a
  missing value is a failure rather than an implicit default — a defensible default is supplied by
  the shipped configuration rather than by the code that reads it, so what is in force is readable.
  The complete set in force, secrets redacted, is recorded at startup.
  → [one validation pass](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-configuration-is-validated-in-one-pass-before-anything-accepts-a-connection)
- **You do not write the example.** The artifact's declared configuration and the shipped example
  are generated from the same schema the validation pass reads, and that schema is retrievable from
  a *stopped* artifact.
  → [schema retrievable while stopped](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-configuration-schema-is-retrievable-from-every-artifact-without-running-it),
  [example generated and complete](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-shipped-example-configuration-is-generated-from-the-same-schema-and-is-complete-on-its-own)
- **A destination for every class of signal, or it will not start.** You may configure a class to be
  discarded; that is reported at startup rather than being a default.
  → [signals are delivered, not merely emitted](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-signals-are-delivered-not-merely-emitted)
- **Root key material is yours to supply.** The platform does not generate it and store it beside
  the data it protects, and its configured value is redacted wherever configuration in force is
  reported. Everything marked required to start is validated — recoverable, correctly
  parameterised, and actually able to perform its purpose — before any surface accepts a connection.
  → [root material is operator-supplied](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-root-material-is-operator-supplied-and-is-not-recoverable-from-anything-the-platform-stores),
  [required material validated before service](../../openspec/changes/rebuild-plugboard/specs/security/key-custody/spec.md#requirement-required-material-is-validated-before-service-begins)
- **What sidecars dial is published configuration, not folklore.** The address, the framing
  identifier and the endpoint identity to verify are retrievable by a party provisioning a sidecar,
  and an endpoint you do not serve is not advertised.
  → [the endpoint a sidecar dials](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-endpoint-a-sidecar-dials-is-discoverable-configuration)
- **Ceilings are installation-wide, with one declared exception.** A per-tenant bound is one value
  for the installation, not one per instance; the pre-authentication connection bound is the closed
  exception, accounted per accepting instance and per observed source, for the reason the listener
  capability states.
  → [one value for the installation](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-a-per-tenant-bound-is-one-value-for-the-installation-not-one-value-per-instance),
  [pre-authentication bound](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-connections-in-the-pre-authentication-state-are-bounded)

## What you watch

Two probes, one signal set, and a coverage rule that runs through all of it.

| the question | the requirement that owns the answer |
|---|---|
| Would a restart help? (and: a partition must never restart the installation) | [liveness](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-liveness-answers-only-whether-a-restart-would-help) |
| Should this instance take new traffic? Answered per instance, derived from real dependency state, withdrawn for the whole of a drain | [readiness](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-readiness-reflects-dependency-state-and-drain) |
| Which instances is this installation, and what state is each in? | [membership from any instance](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-the-installations-membership-and-each-instances-state-are-visible-from-any-instance) |
| Did the answer I just read cover the whole installation? | [an answer states which instances it covers](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-an-answer-that-spans-the-installation-states-which-instances-it-covers) |
| What is degraded right now, and since when? | [degraded operation is announced while it persists](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-degraded-operation-is-announced-for-as-long-as-it-persists) |
| What can I measure at all? | [the measurable quantities are enumerated](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-the-measurable-quantities-are-enumerated) |
| Will measuring it cost me unboundedly? | [labels are bounded in cardinality](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-measurement-labels-are-bounded-in-cardinality) |
| What happened to one exchange, end to end? | [exactly one outcome record](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-exchange-produces-exactly-one-outcome-record), [one correlation identifier](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-one-correlation-identifier-spans-the-whole-exchange), [time attributed to phases](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-elapsed-time-is-attributed-to-enumerated-phases) |
| Which instance produced this signal, and is the fault one instance's or everywhere? | [every signal identifies its instance](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-signal-identifies-the-instance-that-produced-it) |
| Is this mine to act on, or a client's own doing? | [severity reflects required action](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-severity-reflects-required-action-not-internal-surprise) |
| Is the same failure counted once, however many components saw it? | [one cause, one outcome value](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-enumerated-cause-in-the-system-maps-to-exactly-one-outcome-value) |
| Which builds are serving, including during a rollout? | [build provenance, reported and retrievable](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-every-component-reports-its-build-provenance) |
| What is the tenant fleet actually running, and who is holding an old version? | [contract-version and capability spread](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-deployed-contract-version-and-capability-spread-is-observable) |
| What is a drain doing, while it is doing it? | [drain and shutdown are observable throughout](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-drain-and-shutdown-are-observable-throughout) |
| What has this tenant consumed against its configured value? | [consumption as an installation total](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-a-tenants-consumption-is-observable-as-an-installation-total) |
| Who changed what, and when? | [every mutation is recorded](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-every-mutation-is-recorded-in-an-audit-trail), [one trail with a stated ordering](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-the-audit-trail-is-one-trail-for-the-installation-with-a-stated-ordering) |
| Will my alerts survive the next release? | [signal identifiers are a stable interface](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-signal-identifiers-are-a-stable-interface) |

Two structural rules about where you read all this. The probe and diagnostic surfaces are reachable
independently of the surfaces serving tenant traffic and never through a mount; their paths are
contributed to the *single* reserved-path enumeration the mount-point capability owns, so no tenant
mount can shadow them, and an unauthenticated probe discloses neither a tenancy nor the shape of the
installation
([operational surfaces](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-operational-surfaces-are-separated-from-tenant-traffic-and-disclose-nothing-sensitive)).
And the endpoint a sidecar dials, the administrative surface, and the probe and diagnostic surfaces
are three separately identified surfaces — a credential presented at the wrong one authenticates
nothing
([three distinct surfaces](../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md#requirement-the-listener-is-distinct-from-the-administrative-and-operational-surfaces)).

## What a stuck tunnel looks like

A tenant reports that their tunnel is stuck. The obligation is that you answer from your own
operational surface, without shell access, a code change, or a restart, from *any* instance,
without knowing which instance holds the tunnel and without repeating the query instance by
instance —
[a stuck exchange can be diagnosed while it is stuck](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-a-stuck-exchange-can-be-diagnosed-from-one-place-while-it-is-stuck).

Three conditions that look identical from the outside must be distinguishable to you: a mount with
no sidecar anywhere in the installation, a mount whose sidecars are connected but stalled, and a
mount whose sidecars are held by an instance the answering instance cannot reach. The waiting
condition of each in-flight exchange comes from a stable enumerated set — at minimum awaiting
sidecar selection, awaiting flow-control credit, awaiting the backend's first response octet,
transferring a body, and awaiting the client to consume — alongside its age, its correlation
identifier, its octets transferred each way and its octets buffered. The answer is bounded for the
installation as a whole, oldest first, and does not require the stuck sidecar, the backend, or every
instance to be reachable.

The registry side of the same question — per mount, the eligible entries, the instance holding each
tunnel, each entry's negotiated contract version and declared capability set, the time since each
last proved liveness, whether each is draining, and how many exchanges are in flight on each — is
[the registry is inspectable while a tunnel is stuck](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-registry-is-inspectable-while-a-tunnel-is-stuck),
and retrieving it does not require a response from that sidecar.

Three specific shapes of "stuck" are worth knowing before you see one:

- **A frozen sidecar with an open connection is not alive.** Liveness is the wire contract's own
  exchange, answered by the layer that implements the contract; an open socket or a keepalive
  answered by a transport library below the sidecar's contract logic is not evidence.
  → [liveness proven end to end](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-liveness-is-proven-end-to-end-not-inferred-from-the-transport)
- **"No sidecar available" is its own outcome**, produced without waiting for a timer and
  distinguishable from an unmatched mount, from a refusal for a missing capability, and from a
  backend failure — with the reason no entry is eligible available for diagnosis.
  → [no sidecar available](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-no-sidecar-available-is-its-own-outcome)
- **A partition is not something you repair by hand.** The registry converges after a partition with
  no operator action and no sidecar reconnection; your job during it is to see which part of the
  answer is missing, which is what the coverage rule is for.
  → [convergence without intervention](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-registry-converges-after-a-partition-without-intervention)

When you act, you can terminate a single in-flight exchange, or drain or disconnect a single tunnel,
through any instance's surface without establishing which instance holds it. Every action is
attributable to you and recorded — including a refused one — and an action against an instance that
cannot be reached is reported as *not performed*, naming that instance, rather than left ambiguous.
→ [an operator can act on a stuck exchange or tunnel](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md#requirement-an-operator-can-act-on-a-stuck-exchange-or-tunnel)

Planned withdrawal of a proxy instance is its own obligation rather than yours to stage: a fleet is
not disconnected at once —
[planned withdrawal](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-planned-proxy-withdrawal-does-not-disconnect-a-fleet-at-once).

## What the deferred control plane leaves missing

This is the most important thing this note can tell you, and it is a gap, not a feature.

[D17](../decisions/d17-capability-scope.md) defers a human-facing control plane, together with audit
retention and erasure and the origin of per-tenant bound values
([register entry](../../openspec/changes/rebuild-plugboard/design.md#d17--five-further-capabilities-are-in-scope-three-are-deferred-with-their-dependencies-named)).
The specifications are nonetheless full of things an operator must be able to obtain: of the
sixteen specifications' 2,122 scenarios, 300 name an operator — counted by scanning each
`#### Scenario:` block for the word *operator*, which anyone can re-run. Each is an obligation to make something retrievable or actionable. None of them says
through what.

What *is* settled is the shape of the hole:

- **The namespace is committed in v1.** An administrative path prefix and a control-surface
  hostname are reserved now, so the later capability cannot be locked out of its own namespace —
  [D17](../decisions/d17-capability-scope.md), and
  [the platform's own hostnames are reserved](../../openspec/changes/rebuild-plugboard/specs/routing/custom-domains/spec.md#requirement-the-platforms-own-hostnames-are-reserved).
- **v1's operator surface is machine-shaped by decision, not by omission.** Every operator
  retrieval and action is to land on the operational endpoint with no session, cookie, login or
  other human-facing authentication surface, each citing D17's deferral beside it — task 5.11 in
  [tasks section 5](../../openspec/changes/rebuild-plugboard/tasks.md#5-configuration-validation-provenance-and-operational-surfaces).
  Expect an API and your own tooling, not a console.

And these are gaps this note names rather than papers over:

- **No capability owns the operator principal.** Diagnostics "require authorization" and are
  "scoped to what the requesting principal is entitled to see"; migrations are "authorised against
  an operator principal". The phrase *operator principal* appears in two of the sixteen
  specifications — `operability/schema-migration` and `tenancy/isolation` — and neither defines how
  one is issued, authenticated, or scoped. The role model that *is* specified is tenant-side,
  granted on routing entries
  ([roles](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-roles-carry-defined-and-bounded-authority)),
  and credential authentication runs in one direction only — the sidecar proving itself to the
  proxy
  ([one direction](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-a-sidecar-verifies-what-it-is-about-to-authenticate-to)).
  Operator identity belongs to the deferred capability, which means today it belongs to nobody.
- **Audit retention is a recorded contradiction, and you are the only party who can act on it.**
  The trail is append-only and immutable, removable only by an operator
  ([append-only](../../openspec/changes/rebuild-plugboard/specs/tenancy/isolation/spec.md#requirement-the-audit-trail-is-append-only-and-readable-within-its-own-scope)),
  while credential audit records must outlive the credentials they describe under a retention policy
  no capability states. [D17](../decisions/d17-capability-scope.md) records this as a conflict
  needing a stated resolution — tombstoning, field-level redaction, or a documented refusal —
  rather than as an implementation detail.
- **Where per-tenant bound values come from is deferred.** The specifications require the bounds to
  be enforced installation-wide and observable; the origin of the numbers you configure is one of
  D17's three deferrals.
- **Migration actions assume an operational surface that has no owner.** Applying, undoing,
  confirming, ordering or ending a migration is an operator action against an operational surface
  ([migration is an operator action](../../openspec/changes/rebuild-plugboard/specs/operability/schema-migration/spec.md#requirement-applying-a-migration-is-an-operator-action-and-is-never-reachable-from-tenant-traffic));
  what that surface *is* remains with the deferred capability.

If you find yourself needing an operator affordance that no requirement above names, that is a
finding worth raising rather than a gap to fill wherever you happen to be working — which is
[D17](../decisions/d17-capability-scope.md)'s stated consequence for anyone reading the specs.

## Where to go next

| when you want | read |
|---|---|
| the tenant's half of this split | [the tenant's view](tenant-view.md) |
| the failure classes and the six timers, each with its owning specification | [failure taxonomy](failure-taxonomy.md) |
| the adversaries and controls behind the surface separation above | [threat model](threat-model.md) |
| why an installation rather than a process, and what *instance* means | [D20](../decisions/d20-multi-instance.md), [topology](topology.md) |
| why observability was built before the hot path | [D27](../decisions/d27-observability-first.md) |
| the behaviour itself, which this note does not own | [operability/observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md) |

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
