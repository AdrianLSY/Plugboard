# Plugboard — documentation index

You are working on a **from-scratch rebuild**. The working code in `reference/` is prior art, is
read-only, and does not work correctly. Do not treat it as a source of truth for behaviour.

## Read in this order

| # | Document | Read it when |
|---|---|---|
| 1 | [System](01-system.md) | Always. What this is, what it sells, and what it explicitly refuses. |
| 2 | [Architecture](02-architecture.md) | Before touching any design or code. The three primitives, the wire contract, the topology, the runtime. |
| 3 | [Reference audit](03-reference-audit.md) | Before reusing anything from `reference/`. What failed and why, with citations. |
| 4 | [Protocol fidelity](04-protocol-fidelity.md) | When implementing anything that carries traffic. What must survive a round trip. |
| 5 | [Decision log](05-decision-log.md) | When you disagree with a decision, or want to know if it was already argued. Includes reversals. |
| 6 | [Carry-forward](06-carry-forward.md) | When you are about to write something the reference already got right. |
| 7 | [Methodology](07-methodology.md) | Before opening a PR, writing a test, or bumping a doc. |

Planning artifacts live in `openspec/changes/rebuild-plugboard/` — `proposal.md` (why and scope)
and `design.md` (how). Specs and tasks are not written yet.

## Orientation in one screen

```
   tenant's client                     YOU OPERATE THIS          TENANT OPERATES THIS
   ==============                      ================          ====================

   browser / curl / DAV client
   HLS player / gRPC-Web client
              |
              |  HTTP/1.1, HTTP/2, WebSocket
              v
        +-----------------+
        |    PLUGBOARD    |   routes on path prefix or Host header
        |     (proxy)     |   matches a MOUNT POINT in a tenant-scoped cache
        +-----------------+   selects a registered sidecar for that mount
              |
              |  the TUNNEL -- one persistent connection, frame-multiplexed,
              |  versioned wire contract, capability-negotiated
              v
        +-----------------+
        |    TELEPHONE    |   lives in the tenant's own infrastructure,
        |    (sidecar)    |   next to their backend
        +-----------------+
              |
              |  plain HTTP / WebSocket over loopback or LAN
              v
        tenant's backend (Rails, Express, Django, anything)
```

The sidecar dials **out** to the proxy, so the tenant's backend needs no inbound ports, no public
IP, and no firewall change. That is the product.

## The five facts that govern every decision

1. **Version skew is permanent and asymmetric.** You deploy the proxy. Tenants deploy sidecars into
   their own infrastructure, on their own schedule, or never. Production always runs an unbounded
   spread of sidecar versions against one proxy.

2. **Therefore the wire schema is the only irreversible artifact.** An ordered header list added in
   v2 does not help the tenant pinned to v1, and you cannot force the upgrade. Sort work by
   *reversibility*, not by cost — the cheap schema decisions are the urgent ones.

3. **The protocol list is three primitives, not twelve protocols.** Nine of the twelve protocols
   originally requested differ from each other only by `Content-Type` and method token. See
   [Architecture](02-architecture.md).

4. **The previous attempt's tests did not catch that `POST` bodies arrive empty.** 27,000 lines,
   more test code than production code, zero `TODO` markers. Test volume is not evidence. See
   [Reference audit](03-reference-audit.md).

5. **Slow feedback causes bad tests.** The single most useful conclusion from the audit: when
   feedback is slow, an agent or a person writes assertions that are cheap to satisfy rather than
   assertions that are expensive to satisfy. Suite latency is a correctness control, not a
   convenience. See [Methodology](07-methodology.md).

## Conventions in these documents

- **Every claim about `reference/` carries a `file:line` citation.** If you find one that does not,
  distrust it. If you find one that is wrong, fix it and note the correction.
- **Citations point at the reference commit that was audited**: `reference/Plugboard` at `6756a07`,
  `reference/Telephone` at `9ccba86`.
- "Decided" means recorded in [the decision log](05-decision-log.md) with its rationale. "Open"
  means genuinely undecided, listed as such. Anything else is neither — ask.
