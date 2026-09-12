---
type: moc
status: current
authority: none
---

# Start here

This repository is a **from-scratch rebuild**. The working code in `reference/` is prior art, is
read-only, and **does not work correctly** — `POST` bodies arrive empty, binary payloads are
corrupted, neither container boots. Never treat it as a source of truth for behaviour. Cite it with a
`file:line` or not at all.

No product code exists yet. What exists is the plan, and this vault is how you navigate it.

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

The sidecar dials **out** to the proxy, so the tenant's backend needs no inbound ports, no public IP,
and no firewall change. That is the product.

## The five facts that govern every decision

1. **Version skew is permanent and asymmetric.** You deploy the proxy. Tenants deploy sidecars into
   their own infrastructure, on their own schedule, or never. Production always runs an unbounded
   spread of sidecar versions against one proxy. → [version skew](why/version-skew.md)

2. **Therefore the wire schema is the only irreversible artifact.** An ordered header list added in
   v2 does not help the tenant pinned to v1, and you cannot force the upgrade. Sort work by
   *reversibility*, not by cost — the cheap schema decisions are the urgent ones.

3. **The protocol list is three primitives, not twelve protocols.** Nine of the twelve protocols
   originally requested differ from each other only by `Content-Type` and method token.
   → [three primitives](how/three-primitives.md)

4. **The previous attempt's tests did not catch that `POST` bodies arrive empty.** 27,000 lines, more
   test code than production code, zero `TODO` markers. Test volume is not evidence.
   → [reference audit](history/reference-audit.md)

5. **Slow feedback causes bad tests.** The most useful conclusion from the audit: when feedback is
   slow, an agent or a person writes assertions that are cheap to satisfy rather than assertions that
   are expensive to satisfy. Suite latency is a correctness control, not a convenience.
   → [testing](code/testing.md)

## Read in this order

| # | Note | Read it when |
|---|---|---|
| 1 | [What it is](why/what-it-is.md) | Always. What this is and what it sells. |
| 2 | [Who it is for](why/audiences.md) | When a requirement seems to contradict another. Three audiences, and the conflict is named rather than resolved. |
| 3 | [Version skew](why/version-skew.md) | Before estimating anything. The constraint that inverts normal prioritisation. |
| 4 | [Scope refusals](why/scope-refusals.md) | When someone asks for WebRTC, Web Push, NTLM or TLS passthrough. Refusals with reasons, and what is merely deferred. |
| 5 | [Architecture](how/architecture.md) | Before touching any design or code. The hub for the three primitives, the tunnel and the topology. |
| 6 | [Protocol fidelity](how/protocol-fidelity.md) | When implementing anything that carries traffic. What must survive a round trip, in three tiers. |
| 7 | [Reference audit](history/reference-audit.md) | Before reusing anything from the prior art. What failed and why, with citations. |
| 8 | [Carry-forward](history/carry-forward.md) | When you are about to write something the reference already got right. |
| 9 | [Decisions in force](decisions/in-force.md) | When you disagree with a decision. Every decision in force, the retired identifiers, and the collision table. |
| 10 | [Reviewing](code/reviewing.md) · [Testing](code/testing.md) · [Contributing](code/contributing.md) | Before opening a PR, writing a test, or picking up a first issue. |
| 11 | [Documentation rules](method/documentation-rules.md) · [Harness](method/harness.md) · [Supply chain](method/supply-chain.md) | Before bumping a doc, changing agent instructions, or adding a dependency. |
| 12 | [Threat model](how/threat-model.md) | Before touching anything that carries traffic, holds a key, or accepts a hostname. Adversary, asset, control, and who owns it — with the gaps named. |
| 13 | [Failure taxonomy](how/failure-taxonomy.md) | When something is broken and you need to know what class it is. The six timers, refusals, resets — and the silent class. |
| 14 | [Operator's view](how/operator-view.md) · [Tenant's view](how/tenant-view.md) | When you need the system from one side rather than in the middle. |
| 15 | [Alternatives](why/alternatives.md) | When asked why not ngrok, cloudflared, frp, Funnel, or a dynamic-config reverse proxy. |
| 16 | [Success criteria](why/success-criteria.md) | When deciding whether something is finished. One observable bar per audience. |
| 17 | [Obtaining the prior art](history/obtaining-the-reference.md) | Before trying to check any `file:line` citation into `reference/`. |
| 18 | [Research provenance](history/research-provenance.md) | Before re-opening a settled question. What was investigated, what was upheld, and what an adversarial pass overturned. |

## Everything else

[The capability notes](capabilities/index.md) are the layer between orientation and normative
behaviour: eighteen notes, each saying what one capability is for, what it owns, what it explicitly
does not, and which capabilities depend on it — readable whole before you open a thousand-line
specification. Asking "what breaks if `tunnel/listener` changes?" is answered by that note's inbound
links without opening a specification at all.

[The rule index](rule-index.md) lists every rule this repository states with its enforcement status —
gated, gate planned, or preference — and the proportion carrying no gate. It is generated, so a guide
drifting toward unenforced opinion shows up as a number rather than as somebody eventually noticing.

[The glossary](glossary.md) defines every term the specifications fix — and names the ones nothing
defines, which is the more useful half. [The full index](index.md) lists every note in the vault by
directory; it is generated, so it cannot fall behind the tree.

[The repository README](../README.md) is the front door for someone arriving from outside the vault.
It routes here, and it is held to the same link and reachability gates as any note.

## If you are an agent

Read [`CLAUDE.md`](../CLAUDE.md) first — it is a router, not content. Then, by task:

| doing | read |
|---|---|
| anything at all | the five facts above |
| design or code | [architecture](how/architecture.md), then the specification that owns the behaviour |
| writing something the reference already got right | [carry-forward](history/carry-forward.md) |
| a PR, a test, or a doc bump | [reviewing](code/reviewing.md), [testing](code/testing.md), [documentation rules](method/documentation-rules.md) |
| disagreeing with a decision | [decisions in force](decisions/in-force.md) — read its entry before re-litigating |
| reaching for a term you are not sure of | [the glossary](glossary.md) |
| security, or a hostname, or a key | [the threat model](how/threat-model.md) |
| checking a claim about the prior art | [obtaining the prior art](history/obtaining-the-reference.md) |

Planning artifacts live in `openspec/` — [proposal](../openspec/changes/rebuild-plugboard/proposal.md)
for why and scope, [design](../openspec/changes/rebuild-plugboard/design.md) for the decisions in
force, [tasks](../openspec/changes/rebuild-plugboard/tasks.md) for the work, and
[the specifications](../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) for
behaviour.

## Conventions

- **Every claim about `reference/` carries a `file:line` citation.** If you find one that does not,
  distrust it. If you find one that is wrong, fix it and note the correction.
- **Citations point at the revision that was audited**: `reference/Plugboard` at `6756a07`,
  `reference/Telephone` at `9ccba86`. The prior art is not in this repository — it is gitignored.
- "Decided" means recorded in
  [the register](../openspec/changes/rebuild-plugboard/design.md) with its rationale. "Open" means
  genuinely undecided and listed as such. Anything else is neither — ask.
- **Nothing in this vault states behaviour.** These notes are orientation and rationale; the
  specifications own what the system does, and the contract beats both. Where a note and its owning
  artifact disagree, the note is wrong.
