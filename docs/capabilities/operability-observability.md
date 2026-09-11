---
type: capability
status: planned
authority: rationale
---

# Observability

**`operability/observability`** — what an operator can see and do while the system is running.

The capability has one motivating question: a tenant says their tunnel is stuck, and an operator has
to answer it without shell access, a code change or a restart. Everything else here — the signals,
the correlation identifier, the phase attribution, the enumerated measurements — exists so that
question has an answer that does not depend on guessing.

The one idea worth carrying away is that emission is not the bar; **delivery** is. A signal produced
into a destination nobody configured satisfies nothing here, and a signal class with no destination
is a startup refusal rather than a silent default. That inverts the usual arrangement, in which
instrumentation is assumed to work because the call site exists.

The second idea is topological, and it comes from [D20](../decisions/d20-multi-instance.md). A
sidecar's tunnel is held by one instance while the client's request arrives at whatever instance the
load balancer picked, so the state of a single instance cannot answer the question above. Two rules
therefore run through the whole capability: an answer covering less than the installation is labelled
as partial rather than presented as complete, and every record, measurement and diagnostic value
names the instance it came from. An unlabelled partial answer during a partition is precisely when an
operator draws the wrong conclusion.

The prior art is the argument for [D27](../decisions/d27-observability-first.md): its documentation
described an error log call at `proxy_controller.ex:51` that does not exist anywhere in the code
([reference audit](../history/reference-audit.md)). The sidecar's sentinel errors and real health
server are the half worth porting ([carry-forward](../history/carry-forward.md#sentinel-errors-health-server)).

## What it owns

- Signal delivery, the produced-signal inventory, and observability failure never becoming a traffic failure
- One outcome record per admitted exchange, and the cause-to-outcome mapping for the whole system
- The correlation identifier spanning all three hops, and elapsed time attributed to enumerated phases
- The enumerated measurable quantities, and the cardinality bound on their labels
- Liveness and readiness as distinct signals, on a surface separated from tenant traffic
- The stuck-exchange diagnostic, answerable while stuck, and the operator actions on it
- Degraded announcements, drain visibility, build provenance at runtime, one-pass configuration validation
- Signal identifiers treated as a stable interface, and the exclusion of secrets and tenant payload

## What it does not own

- Registry convergence after a partition — [sidecar registry](tunnel-sidecar-registry.md)
- What a stopped artifact declares about itself — [packaging](operability-packaging.md)
- The endpoint the operational surface is bound to — [the listener](tunnel-listener.md)
- What the edge strips or regenerates per hop — [edge hygiene](proxy-edge-hygiene.md)

## Depends on

- [packaging](operability-packaging.md) — provenance and the configuration schema are declared by the
  artifact; this capability owns only what the running component reports from them
- [sidecar registry](tunnel-sidecar-registry.md) — convergence and cross-instance selectability are
  taken as given, so that what is left here is what an operator sees *before* they happen
- [the listener](tunnel-listener.md) — the operational surface is a listening endpoint like any other
- [edge hygiene](proxy-edge-hygiene.md) — the causes recorded at the client hop are enumerated there

## Shaped by

- [D27 — Observability before the hot path](../decisions/d27-observability-first.md) — the sink and the
  logger are chosen first, and a test asserts a handler is attached and receiving
- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — every
  obligation is stated for the installation, never for whichever instance a query reached

## The specification

[`operability/observability`](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
