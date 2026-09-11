---
type: guide
status: planned
authority: rationale
---

# The tenant's view

What the other half of the deployment looks like. A tenant runs the sidecar; the operator runs the
proxy and cannot reach the tenant's machine, read its logs, or upgrade the artifact on it. Everything
below follows from that asymmetry.

> **Planned.** Nothing here can be done yet. `sidecar/` does not exist in this repository — the
> program is built by
> [task 29](../../openspec/changes/rebuild-plugboard/tasks.md#29-the-sidecars-dialler-and-startup-sequence-sidecar),
> [task 37](../../openspec/changes/rebuild-plugboard/tasks.md#37-backend-dialling-and-origination-in-the-sidecar)
> and
> [task 61](../../openspec/changes/rebuild-plugboard/tasks.md#61-the-sidecar-as-a-tenant-run-program),
> its release artifact by
> [task 70](../../openspec/changes/rebuild-plugboard/tasks.md#70-packaging-declarations-provenance-and-the-start-gate),
> and its configuration surfaces by
> [task 5](../../openspec/changes/rebuild-plugboard/tasks.md#5-configuration-validation-provenance-and-operational-surfaces).
> There is no artifact to download, no schema to interrogate and no readiness signal to poll. This
> note is the shape of the obligation, not a runbook.

**This note states no behaviour.** Every row and bullet below links to the requirement that owns it;
where a sentence here and that requirement disagree, the requirement wins. See
[the architecture](architecture.md) on the precedence order.

## Why a tenant would want this

The sidecar dials **out**. The tenant's backend needs no inbound network path — no public IP, no port
forward, no firewall change, no inbound security-group rule — which is the whole product claim and is
argued in [what it is](../why/what-it-is.md#what-that-buys).

Their side of the bargain is the rest of this note: a process in their pods, next to their backend,
holding a credential the operator issued, that their platform team has to be willing to allow.

## What they install

One artifact per deployable component, and for the sidecar that artifact is the deployment:

- **One self-contained thing.** Exactly one artifact per component, carrying everything it needs to
  start and declaring what it needs from outside —
  [one artifact](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-every-deployable-component-releases-as-exactly-one-artifact),
  [self-contained](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-carries-everything-it-needs-to-start-and-declares-what-it-needs-from-outside).
  The sidecar is Go, which is [D4](../decisions/d04-runtime.md).
- **Readable before it runs.** The platform team's veto is the reason the artifact has to answer
  questions while stopped: its
  [configuration schema](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-configuration-schema-is-retrievable-from-every-artifact-without-running-it),
  its
  [contract version range](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-each-artifact-declares-the-contract-version-range-it-speaks-readable-without-running-it),
  its
  [dependency inventory](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-dependency-inventory-is-discoverable-from-the-artifact-and-matches-its-contents),
  and its
  [identity, independent of where it was obtained](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-carries-a-verifiable-identity-independent-of-where-it-was-obtained).
- **Narrow on the machine it shares.** No more privilege than the component needs
  ([packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-an-artifact-requires-no-more-privilege-than-the-component-needs)),
  nothing in the artifact beyond what it runs
  ([packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-artifact-contains-only-what-the-component-needs-to-run)),
  and no filesystem footprint beyond the one configured store path
  ([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-sidecars-footprint-on-the-tenants-machine-is-the-configured-store-path-alone)).
- **Whether the pairing works at all** is answerable from the two artifacts, before either runs —
  [packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-pairing-viability-is-determinable-from-the-artifacts-alone).

## What they configure

**The schema is the enumeration, not this note.** The plan deliberately does not fix configuration
item *names* here: the sidecar's schema is
[the single enumeration of every value its behaviour depends on](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-configuration-is-a-declared-schema),
it is
[retrievable from the artifact without running it](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-configuration-schema-is-retrievable-from-every-artifact-without-running-it),
and the artifact's shipped configuration and example are
[generated from that same schema](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-the-artifacts-declared-configuration-is-generated-from-the-configuration-schema).
So a name in a note here would be a second copy that could go stale. What the specifications *do*
fix is which subjects a tenant must decide about:

| the tenant decides | owning requirement |
|---|---|
| the backend origin to dial — and it comes from local configuration only, never from a request | [the backend origin is taken only from local configuration](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-backend-origin-is-taken-only-from-local-configuration) |
| whether the backend hop is protected, and the identity or trust source to expect — with no setting that accepts any identity | [protection of the backend hop is decided by configuration](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-protection-of-the-backend-hop-is-decided-by-configuration-and-cannot-be-waived-silently) |
| the bounds on the backend hop: connect, first response octet, between successive body octets | [backend connection bounds are the sidecar's own](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-backend-connection-bounds-are-the-sidecars-own-and-distinct-from-the-proxys) |
| the store location for the persisted credential — one location, and nowhere else | [the credential store is one configured location](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-credential-store-is-one-configured-location-exclusively-held-with-three-distinguishable-states) |
| the sidecar's own ceilings: concurrent exchanges, octets buffered per exchange and in total, frames buffered before a stream's far hop is joined, backend connections, translation working memory | [the sidecar bounds its own footprint](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-sidecar-bounds-its-own-footprint-on-every-dimension-it-can-grow-on) |
| the drain period and the shutdown deadline it must complete inside | [validation covers relationships between items](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-validation-covers-form-range-and-relationships-between-items), [shutdown withdraws readiness first](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-shutdown-withdraws-readiness-first-releases-the-backend-hop-and-exits-successfully) |
| whether gRPC-Web translation is on, and for which mount and content types | [translation is applied only where configured](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-translation-is-applied-only-where-configured-and-is-otherwise-inert) |

Not every item is the tenant's to choose: each declared item states one of two origins, operator-issued
or tenant-determined. Which items fall on the operator's side is stated in the schema itself
([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-declared-configuration-states-which-items-only-the-operator-can-issue)),
and nothing the tenant configures can widen the contract range or add a capability the build cannot
perform
([packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-a-declared-range-is-the-range-the-component-enforces-and-neither-is-widenable)).

### Configuration fails fast, and reports everything at once

The tenant's first ten minutes are a configuration loop with nobody to ask, so the loop is designed
to close in one pass rather than one item per restart:

- Validation
  [completes before the credential, the endpoint, or the backend is touched](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-validation-completes-before-the-credential-the-endpoint-or-the-backend-is-touched)
  — so the refusal is reachable with the endpoint unresolvable, no credential store and no backend
  running, and names the same faults it would with all three up.
- It covers
  [form, range, and relationships between items](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-validation-covers-form-range-and-relationships-between-items),
  and a relationship fault names both items rather than one.
- A misspelling is not silently an omission: an unknown item in the sidecar's own namespace is
  reported with the declared name it most closely resembles
  ([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-configuration-is-a-declared-schema)).
- An empty or whitespace-only required value is a named failure, distinguishable from absence, and no
  shipped default fills in for it
  ([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-each-value-in-force-is-attributable-to-the-operator-or-to-the-shipped-configuration)).
- There is no reload. A change takes effect by starting a new process
  ([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-configuration-is-fixed-for-the-lifetime-of-the-process)),
  which is also why the diagnostics have to be good at the default verbosity — raising it would
  require the restart that destroys the state being diagnosed.

## What they verify

Every check below is answerable from inside the tenant's own infrastructure, without proxy access.
That is the constraint that shapes the list: the party diagnosing a tunnel that will not establish is
the one party who cannot reach the proxy.

| the tenant asks | owning requirement |
|---|---|
| "did it take exactly the configuration I gave it?" — every item in force, with each value attributed to me or to the shipped default, secrets as presence alone | [retrievable on demand](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-configuration-in-force-is-retrievable-on-demand-and-secrets-are-reported-as-presence-alone), [attributable](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-each-value-in-force-is-attributable-to-the-operator-or-to-the-shipped-configuration) |
| "how far did startup get?" — validation, local surface, endpoint verification, credential, tunnel, backend reachability, readiness, in that order, with a failure naming its own step | [startup is an ordered sequence](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-startup-is-an-ordered-sequence-with-observable-intermediate-states) |
| "why am I not ready?" — an enumerated reason that discloses no secret | [readiness states an enumerated reason](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-readiness-states-an-enumerated-reason-that-discloses-no-secret) |
| "is my backend actually reachable?" — proven by the sidecar's own means, not inferred from the tunnel being up or from the last exchange having succeeded | [backend reachability is proven, never inferred](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-backend-reachability-is-proven-by-the-sidecar-and-never-inferred) |
| "what does this build speak?" — the contract range and the capabilities it can declare, answerable with the tunnel endpoint unresolvable | [answerable from inside the tenant's infrastructure](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-contract-range-and-capability-set-are-answerable-from-inside-the-tenants-infrastructure) |
| "does the operator see the same build I do?" | [the provenance a tenant reads and the provenance the proxy records are the same](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-provenance-a-tenant-reads-and-the-provenance-the-proxy-records-are-the-same) |
| "what did my exit status mean?" — distinct, stable statuses per failure class, and fatal-at-startup distinguished from survivable | [exit statuses](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-failure-classes-have-distinct-stable-exit-statuses), [fatal versus survived](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-conditions-fatal-at-startup-are-distinguished-from-conditions-to-be-survived) |

### When it is stuck

The one surface worth knowing about in advance is the local diagnostic, which is required to answer
while every exchange is blocked and the tunnel is unresponsive, without a restart and without the
proxy's cooperation, and to describe carried traffic without reproducing any of it —
[an operator inside the tenant's infrastructure can diagnose without proxy access](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-an-operator-inside-the-tenants-infrastructure-can-diagnose-without-proxy-access).

Its waiting conditions come from the same published enumeration the proxy-side diagnostic uses, which
is the point: a tenant on a support call and an operator looking at
[the registry](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-the-registry-is-inspectable-while-a-tunnel-is-stuck)
describe one stuck exchange with the same word. Never confirm a credential from output: no output at
any verbosity carries credential or key material
([sidecar](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-no-output-at-any-verbosity-carries-credential-or-key-material)).

## When a capability their backend needs is refused

This is the outcome most likely to surprise a tenant, and it is deliberate rather than a bug.
**Refuse, never degrade** is [D3](../decisions/d03-capability-negotiation.md) — read that note for
why, and read the requirements for what:

- [capability declaration](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-capability-declaration)
  — what each side declares when a tunnel is established, and that the declared set is fixed for that
  tunnel's life.
- [refusal rather than silent degradation](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-refusal-rather-than-silent-degradation)
  — the refusal itself, and the after-dispatch case.
- [eligibility is filtered by capability before selection, not after](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md#requirement-eligibility-is-filtered-by-capability-before-selection-not-after)
  — why an old sidecar in the fleet does not make one URL behave two ways.
- [a requirement describing an optional capability binds only where it is declared](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-a-requirement-describing-an-optional-capability-binds-only-where-it-is-declared)
  — the general rule the two above are instances of.

The practical shape for a tenant: the sidecar declares what **this build and this configuration** can
do, so a capability is a statement rather than a hope, and the fix for a refusal is on the tenant's
side — configure or upgrade the sidecar until it can declare what the route needs. The gRPC-Web
translation is the worked example, including the case where an unconfigured sidecar declares nothing
at all:
[the gRPC-Web to gRPC translation is a declared capability, never an assumption](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md#requirement-the-grpc-web-to-grpc-translation-is-a-declared-capability-never-an-assumption).

Two consequences to design around rather than discover:

- A refusal is legible and immediate; a degraded success would not be. Selection spreads a mount's
  requests across every eligible sidecar, so a fidelity that varied by sidecar version would make two
  identical requests differ non-deterministically — [version skew](../why/version-skew.md) is why
  that fleet is heterogeneous in the first place, permanently.
- A need discovered after dispatch resets the stream rather than dropping the part that cannot be
  carried, so a client sees a truncated response instead of a quietly wrong one
  ([refusal rather than silent degradation](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md#requirement-refusal-rather-than-silent-degradation)).

## What no specification owns yet

Two things a tenant needs on day one are, as of this note, owned by nothing in the sixteen
specifications. They are named here as gaps rather than filled in, because a note inventing them
would be a claim with no owner.

- **Where the artifact comes from, and how a tenant learns a newer one exists.** Packaging assumes a
  distribution location — the release gate must obtain the artifact "from where it is published"
  ([packaging](../../openspec/changes/rebuild-plugboard/specs/operability/packaging/spec.md#requirement-a-release-gate-starts-the-published-artifact-and-asserts-its-own-readiness-signal))
  — but no requirement names that location, says who may publish to it, or gives a tenant any
  notification path for a new version. Given that tenants pin sidecar versions indefinitely
  ([version skew](../why/version-skew.md)), that is the gap with the longest tail.
- **How the credential reaches the tenant.** The secret is returned only in the result of the
  operation that creates it, and never again
  ([sidecar-credentials](../../openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md#requirement-the-secret-is-presented-exactly-once)).
  Which principal may run that operation *is* specified — every credential operation is authorised
  against an acting principal. What is unspecified is the channel by which the secret reaches the
  tenant's platform team once issued.

## Read next

- [The operator's view](operator-view.md) — the same deployment from the other side.
- [The failure taxonomy](failure-taxonomy.md) — every failure class a tenant can observe, enumerated.
- [The tunnel](the-tunnel.md) — what the sidecar actually speaks, and why it is frame-shaped.
- [Protocol fidelity](protocol-fidelity.md) — what a tenant's traffic is guaranteed to survive.
- [Who it is for](../why/audiences.md) — the tenant is one of three audiences, and the conflicts are
  named rather than resolved.
- [sidecar/program](../../openspec/changes/rebuild-plugboard/specs/sidecar/program/spec.md) — the
  specification that owns everything above.

## On the requirement titles named above

Where this note names a specification's own requirement, it does so because a reader checking the
claim should land on the obligation itself rather than on a paraphrase. Those summaries are
**non-normative**: the owning specification wins where it and this note disagree, and where this note
is narrower or wider than the requirement it names, the requirement is right.
