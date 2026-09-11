---
type: decision
status: current
authority: decision
---

# D5 — Proxied traffic terminates before application middleware

**In force.** Tenant traffic is handled on a path of its own, so none of the host framework's
ordinary request handling — body parsers, method overrides, HEAD folding, content negotiation,
sessions, CSRF — ever sees a proxied byte. It rules out solving a proxy problem by adding a plug,
and it rules out letting the framework normalise a request before the proxy has looked at it.

This is a structural decision rather than a spec requirement, and it is the one that makes the
fidelity obligations reachable at all: a framework that has already consumed a body cannot hand it
onward intact, which is how the reference broke GraphQL and JSON-RPC without any protocol-specific
code being involved. Reading the proxy, expect a deliberately thin dedicated path that shares no
pipeline with the administrative surface; anything that must happen to a proxied request happens
there or nowhere. The edge is the narrow exception — tunnelling and reflecting method tokens are
refused or answered locally instead of being forwarded. Cited as `D11` before the registers were
consolidated; that number is retired.

- **Full entry, with rationale and alternatives:** [register D5](../../openspec/changes/rebuild-plugboard/design.md#d5-proxied-traffic-terminates-before-application-middleware)
- **Shapes:** [proxy/edge-hygiene](../../openspec/changes/rebuild-plugboard/specs/proxy/edge-hygiene/spec.md), [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
