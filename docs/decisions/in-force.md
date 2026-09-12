---
type: moc
status: current
authority: none
---

# Decisions in force

Each entry below is a short note saying what the decision
settles; the full rationale and the alternatives considered live in
[the register](../../openspec/changes/rebuild-plugboard/design.md), which wins wherever a note and it
disagree.

**If you disagree with a decision, read its entry before re-litigating it.** Several were argued at
length and one was overturned outright — the runtime choice — after an adversarial review found the
premise that forced it had been fabricated. That history is in the notes, and it is the most useful
thing to know before reopening anything.

| # | Decision | Note |
|---|---|---|
| `D1` | Three primitives, not twelve protocols | [note](d01-three-primitives.md) |
| `D2` | The tunnel exchange is frame-shaped | [note](d02-frame-shaped-tunnel.md) |
| `D3` | Capability negotiation, with refusal rather than degradation | [note](d03-capability-negotiation.md) |
| `D4` | Runtime: Elixir proxy, Go sidecar, Go H3 terminator later | [note](d04-runtime.md) |
| `D5` | Proxied traffic terminates before application middleware | [note](d05-pipeline-before-middleware.md) |
| `D6` | Framing authority is per-hop, never relayed | [note](d06-framing-authority.md) |
| `D7` | Timeout taxonomy replaces the single cap | [note](d07-timeout-taxonomy.md) |
| `D8` | Tenant scoping in the data model, not in queries | [note](d08-tenant-scoping.md) |
| `D9` | Domain ownership verification precedes certificate issuance | [note](d09-domain-ownership.md) |
| `D10` | Carry-forward is explicit and cited | [note](d10-carry-forward.md) |
| `D16` | HTTP/2 to clients is in v1, and the edge listener is a separate component from the start | [note](d16-http2-to-clients.md) |
| `D17` | Five further capabilities are in scope; three are deferred with their dependencies named | [note](d17-capability-scope.md) |
| `D18` | Frame payloads are encoded from a binary interface definition, with generated codecs | [note](d18-frame-payload-encoding.md) |
| `D19` | The v1 tunnel is a WebSocket over TLS on the standard HTTPS port | [note](d19-tunnel-transport.md) |
| `D20` | The proxy is a multi-instance installation in v1 | [note](d20-multi-instance.md) |
| `D21` | Rebuild from scratch; the reference is prior art only | [note](d21-rebuild-from-scratch.md) |
| `D22` | One repository | [note](d22-one-repository.md) |
| `D23` | Contract-first, with a conformance suite | [note](d23-contract-first.md) |
| `D24` | Version skew is the governing constraint | [note](d24-version-skew.md) |
| `D25` | Positioning: multi-tenant platform ingress | [note](d25-positioning.md) |
| `D26` | WebTransport is designed for, not shipped | [note](d26-webtransport-deferred.md) |
| `D27` | Observability before the hot path | [note](d27-observability-first.md) |
| `D28` | Licensing: Apache-2.0 over the authored tree | [note](d28-licensing.md) |

## Retired identifiers

`D11`–`D15` are **permanently unassigned** and will never be reused. They belonged to a second
register that numbered its entries `D1`–`Dn` alongside this one and disagreed with it; the five
decisions they held now live elsewhere in the surviving register.

| retired | what it used to denote | where that decision lives now |
|---|---|---|
| `D11` | Proxied traffic terminates before application middleware | `D5` |
| `D12` | Framing authority is per-hop, never relayed | `D6` |
| `D13` | Tenant scoping in the data model | `D8` |
| `D14` | Domain ownership verification precedes certificate issuance | `D9` |
| `D15` | Observability before the hot path | `D27` |

A citation written against the superseded register resolves through
[the collision table](superseded-register.md), which records all fifteen of its identifiers.

## Namespacing

The unnamespaced `D<n>` sequence belongs to the register alone. A change's own design decisions carry
a prefix naming the change — the vault restructure's ten are `RDV1`–`RDV10`. A namespaced set is not
a register, and `ci/gates/decision_register.py` refuses an unnamespaced identifier introduced
anywhere else.
