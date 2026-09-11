---
type: capability
status: planned
authority: rationale
---

# The sidecar registry

**`tunnel/sidecar-registry`** — which sidecars are eligible to serve a mount at any instant, which one
a given request goes to, and what is observed when they appear, vanish, drain or disagree about what
they can do.

This is the join between routing and the tunnel. Matching has already produced a mount and a
remainder and deliberately stopped there; the registry is what turns *a tunnel exists somewhere in
this installation* into a tenant-scoped answer to *who serves this request* — and, when the answer is
nobody, into its own distinguishable outcome rather than a generic failure with a guessed cause.

The one idea to carry in is the unit. A **registry entry** describes one tunnel: not one sidecar
deployment, not one host, not one mount. A reconnecting sidecar is a new incarnation with its own
entry, and a superseded incarnation never takes its successor down with it — the shape that goes wrong
first when the unit is "a sidecar". **Eligibility** likewise begins and ends with the tunnel, and
capability filtering happens before selection rather than after, so a request the fleet cannot back is
refused with a reason instead of dispatched and then failed. Both terms are in
[the glossary](../glossary.md#the-tunnel).

Its frame of reference is the installation, not one process: a sidecar holding a tunnel to one
instance serves requests arriving at any instance, and the registry converges after a partition
without anyone intervening. It is also the only place that knows which contract versions and
capabilities are actually deployed across a fleet nobody can force forward — the projection
[version skew](../why/version-skew.md) makes necessary. The prior art's disconnect handling is worth
re-deriving: it failed every waiting caller fast and notified every socket handler instead of leaving
them to time out (`telephone_channel.ex:417-452`,
[carry-forward](../history/carry-forward.md#failure-fan-out-on-disconnect)). Its reconnect path had
the right jitter and none of the tests (`reconnect.go:234-238`).

## What it owns

- eligibility, and the entry describing one tunnel with its version, capabilities and holding instance
- registration authorised against a live mount of the credential's tenant, and incarnation supersession
- selection: total, deterministic in outcome, spread across eligible entries, capability-filtered first
- affinity bindings as bounded registry state, and the outcome when a bound entry is unreachable
- end-to-end liveness, departure, bounded reselection, and *no sidecar available* as an outcome of its own
- draining from either side, spread withdrawal, cross-instance convergence, and the deployed-version view

## What it does not own

- what is spoken on the tunnel it selects — [the wire contract](tunnel-wire-contract.md)
- accepting the connection, and establishing who the peer is — [the listener](tunnel-listener.md), [sidecar credentials](auth-sidecar-credentials.md)
- which mount a request matched in the first place — [mount points](routing-mount-points.md)
- how a sidecar behaves once it has been chosen — [the sidecar program](sidecar-program.md)

## Depends on

Nothing. Its specification names no other capability. The dependency runs the other way: it is named
by `tunnel/wire-contract`, which carries only the key and the mount an exchange was matched to and
leaves selection here.

## Shaped by

- [D20 — The proxy is a multi-instance installation in v1](../decisions/d20-multi-instance.md) — cross-instance service, convergence after a partition and installation-wide per-tenant accounting are the subject, not deployment luck
- [D3 — Capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md) — put capability filtering ahead of selection, and made an unbackable request a refusal
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — made the deployed version and capability spread something an operator can see, and mixed-version registry state a requirement
- [D10 — Carry-forward is explicit and cited](../decisions/d10-carry-forward.md) — the disconnect fan-out and the reconnect jitter are re-derived from citations rather than remembered

## The specification

[`tunnel/sidecar-registry`](../../openspec/changes/rebuild-plugboard/specs/tunnel/sidecar-registry/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
