---
type: decision
status: current
authority: decision
---

# D1 — Three primitives, not twelve protocols

**In force.** The system carries three transport shapes — a request/response byte stream, a
bidirectional frame stream, and QUIC streams with datagrams — and every named protocol a tenant
brings is one of them. It rules out a handler, a branch, or a spec clause keyed to a protocol name.

For anyone reading a request for support for some new protocol, this is the decision that reframes
the question: not "what code does this need" but "which primitive already carries it, and does the
sidecar declare the capabilities that primitive's fidelity requires". Nine of the twelve protocols
originally surveyed turned out to differ only by a `Content-Type` and a method token, so the answer
is usually that nothing new is needed. The third primitive is reserved rather than built — it exists
in the contract so that adding it later does not split the fleet, not because it ships in v1. The
alternative was per-protocol handling, which is what the previous attempt did, and the visible
result there was one code path per protocol quietly diverging from the others.

- **Full entry, with rationale and alternatives:** [register D1](../../openspec/changes/rebuild-plugboard/design.md#d1-three-primitives-not-twelve-protocols)
- **Shapes:** [proxy/http-fidelity](../../openspec/changes/rebuild-plugboard/specs/proxy/http-fidelity/spec.md), [proxy/websocket](../../openspec/changes/rebuild-plugboard/specs/proxy/websocket/spec.md), [tunnel/wire-contract](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
