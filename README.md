# Plugboard

**Dynamic ingress for multi-tenant platforms.** It replaces static reverse-proxy configuration files
with routing that applications register for themselves at runtime, over a persistent outbound tunnel.

> ### Status: there is no product code.
>
> This repository is **the plan** — sixteen capability specifications, a decision register, a
> documentation vault, and a CI harness that fails the build when the prose drifts from the tree.
> The system described below has not been built; `proxy/`, `sidecar/`, `contract/` and `conformance/`
> do not exist yet. Nothing here proxies traffic.
>
> What *is* here is checked. Every claim a gate can decide is decided on every push by
> [one command](#run-it-yourself) — and the claims no gate can decide are
> [named as undecided](docs/method/documentation-rules.md) rather than left to look enforced. The
> largest of those: most claims about the prior art rest on citations into a tree no reader can yet
> obtain. → [the gap, stated](docs/history/obtaining-the-reference.md)
>
> That is deliberate. → [why](openspec/changes/rebuild-plugboard/proposal.md) ·
> [what is decided](docs/decisions/in-force.md) · [what is refused](docs/why/scope-refusals.md)

---

## The shape of it

```
   tenant's client                       YOU OPERATE THIS          THE TENANT OPERATES THIS
   ---------------                       ----------------          ------------------------
   browser · curl · HLS player
   WebDAV client · gRPC-Web
              |
              |  HTTP/1.1 · HTTP/2 · WebSocket
              v
      +------------------+
      |    PLUGBOARD     |   routes on path prefix or Host header
      |   Elixir proxy   |   resolves a mount point in a tenant-scoped cache
      +------------------+   selects a registered sidecar for that mount
              |
              |  THE TUNNEL -- one persistent connection, frame-multiplexed,
              |  versioned contract, capability-negotiated
              v
      +------------------+
      |    TELEPHONE     |   a static binary, running in the tenant's own pods
      |    Go sidecar    |
      +------------------+
              |
              |  plain HTTP / WebSocket over loopback or LAN
              v
      tenant's backend   (Rails · Express · Django · anything)
```

**The sidecar dials out.** The tenant's backend needs no inbound port, no public IP, no firewall
change and no inbound security-group rule. That is the product.

Four things that buys, and the machinery is in the specifications rather than here:

| what the shape buys | why it follows |
|---|---|
| **No inbound network path** | The tunnel is outbound-only, from the tenant's network to yours. |
| **Routing changes without restarts** | Mount points live in the database and are projected into an in-memory cache. Adding a route touches no config file and bounces no process. |
| **Registration is the deploy** | A backend that starts up and connects a sidecar is routable; one that dies stops being routable. Autoscaling needs no service-discovery wiring. |
| **Custom domains per tenant** | Mapped onto mount points, so a tenant's traffic arrives on their own hostname rather than a path prefix under yours. |

→ [what it is](docs/why/what-it-is.md) · [the architecture](docs/how/architecture.md) ·
[ngrok, cloudflared, frp, Funnel, and dynamic-config Caddy](docs/why/alternatives.md)

---

## The five facts that govern every decision

**1 · Version skew is permanent and asymmetric.** You deploy the proxy. Tenants deploy sidecars into
their own infrastructure, on their own schedule, or never. Production always runs an unbounded spread
of sidecar versions against one proxy — and *a monorepo makes the repository consistent; it does
nothing for production.* → [version skew](docs/why/version-skew.md)

**2 · Therefore the wire schema is the only irreversible artifact.** An ordered header list added in
v2 does not help the tenant pinned to v1, and you cannot force the upgrade. So work sorts by
**reversibility**, not by cost: the cheap schema decisions are the urgent ones.
→ [the wire contract](openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md)

**3 · The protocol list is three primitives, not twelve protocols.** Nine of the twelve protocols
originally requested differ from one another only by `Content-Type` and method token. None of them
justifies a line of protocol-specific code. *Protocols are not features. Fidelity is the feature.*
→ [three primitives](docs/how/three-primitives.md)

**4 · The previous attempt's tests did not catch that `POST` bodies arrive empty.** More test code
than production code, zero `TODO` markers, and 27,000 lines of tests never noticed. **Test volume is
not evidence.** → [the reference audit](docs/history/reference-audit.md)

**5 · Slow feedback causes bad tests.** When feedback is slow, an agent or a person writes assertions
that are cheap to satisfy rather than assertions that are expensive to satisfy. Suite latency is
treated here as a correctness control, not a convenience. → [testing](docs/code/testing.md)

---

## What is being rebuilt, and from what

The prior art is two components — an Elixir proxy and a Go sidecar — and **it does not work.** It
works for `GET` requests returning text. The two elementary obligations of a reverse proxy, *carry
the request through* and *carry the bytes through unchanged*, are both broken:

- **Request bodies never reach the sidecar.** A body parser runs ahead of the router, so the
  forwarding path re-reads an already-consumed body and forwards the empty string. The test named
  *"correctly passes request payload to telephone"* uses `GET` and asserts only on the method.
- **Binary payloads are corrupted in transit.** `[]byte` is converted to `string` per chunk and
  JSON-encoded, so every image, PDF, protobuf, gzip and media segment is mangled — and even valid
  UTF-8 breaks when a multi-byte character straddles a read boundary. The WebSocket path, written
  later, base64-encodes and gets it right. *Same codebase, two body paths, no shared abstraction,
  one wrong.*
- **Neither container boots.** A required secret is raised for at startup and set nowhere the runtime
  can see it.

Seven independent auditors, each of whose top claims went to an adversarial verifier instructed to
refute them and to default to *refuted* when uncertain. The findings are the reason this is a rebuild
rather than a repair, and the reason the reference is cited **by `file:line` or not at all**.

→ [the audit](docs/history/reference-audit.md) ·
[what is worth carrying forward](docs/history/carry-forward.md) ·
[D21 — rebuild from scratch](docs/decisions/d21-rebuild-from-scratch.md) ·
[obtaining the prior art](docs/history/obtaining-the-reference.md)

---

## The design, in four commitments

**The tunnel is frame-shaped, not message-shaped.** The unit on the wire is a frame carrying a stream
id, not a message carrying a whole exchange. *The stream is the exchange* — which deletes the
correlation-id map, the `waiting_callers` table, the selective receive, the leak, and the head-of-line
blocking between a tenant's 2 GB download and their 50 ms API call. Every frame type is reserved at
v1 even where unimplemented, because *reserving a frame type costs nothing today; adding one later
splits the fleet permanently.* → [the tunnel](docs/how/the-tunnel.md)

**Refuse, never degrade.** A sidecar declares its capability set at tunnel join. A request a connected
sidecar cannot back is refused with an explicit status and reason — never silently served at reduced
fidelity. This is load-bearing because selection round-robins across a mount: without it, two
identical requests to the same URL behave differently depending on which sidecar version answered.
→ [D3](docs/decisions/d03-capability-negotiation.md)

**Contract first, with a conformance suite as the authority.** Adversarial fixtures are written
*before* the code they gate — a lone `0x80` byte in a body, two `Set-Cookie` lines, both
`Content-Length` and `Transfer-Encoding`, `%2F` inside a path segment, a fragmented WebSocket message,
a response that emits headers then stalls ninety seconds, a `PROPFIND`, a body larger than memory.
*A specification with no fixture ahead of it is a wish.*
→ [D23](docs/decisions/d23-contract-first.md) ·
[the suite](openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)

**Tenant scoping is a key and a signature, not a habit.** Every projection is tenant-keyed and every
mutation takes the acting principal, because *"one tenant cannot affect another"* is a sold promise
and the only structural answer to it is a schema decision taken on day one.
→ [D8](docs/decisions/d08-tenant-scoping.md) ·
[who it is for](docs/why/audiences.md)

Elixir for the proxy, Go for the sidecar — a choice that **reversed** an earlier recommendation after
an adversarial review found the premise forcing it had been fabricated. The reversal is the readable
part. → [D4 — runtime](docs/decisions/d04-runtime.md) · [topology](docs/how/topology.md)

---

## What it will not do

Refusals with reasons, kept separate from deferrals, because *a refusal here is a refusal, not a
maybe*:

| refused | why |
|---|---|
| WebRTC **media and data channels** | SRTP and SCTP-over-DTLS over ICE-negotiated UDP. The component that relays that is a TURN server — bandwidth-priced with a latency SLA, a different product. WebRTC *signalling* is carried for free as an ordinary stream. |
| Web Push with VAPID | Nothing traverses the proxy. Zero work required. |
| NTLM / SPNEGO to tenant backends | Connection-bound authentication cannot be expressed through a tunnel that multiplexes independent streams. The honest "cannot be done" item. |
| TLS passthrough | Encrypted Client Hello encrypts the single field such a mode routes on. |
| Full gRPC at the ingress | `grpc-status` must travel as a trailer even on success. gRPC-Web *is* in scope; the bridge belongs in the sidecar. |
| Response caching in v1 | No cache-key design, therefore no cache-poisoning surface. |

**Deferred, not refused:** WebTransport (reserved in the contract, shipped later as a separate HTTP/3
terminator), HTTP/3 at the edge, trailers, 1xx interim responses, Range/206 — all cheap later
*because the frame types are reserved in v1*.

→ [scope and refusals](docs/why/scope-refusals.md) · [protocol fidelity](docs/how/protocol-fidelity.md)

---

## The unusual part: the documentation is the artifact under test

There is no product code, so the thing this repository actually ships is a vault whose claims are
mechanically enforced. The governing principle is that **a rule with no gate is a wish** — and its
corollary, that *a gate no runner invokes is a wish with a Python file attached*.

Gates that run on every push and pull request, in the standard library, with no dependencies:

- **Every link resolves, anchors included** — and a missing anchor is reported distinctly from a
  missing file, because the two have different fixes.
- **Every note is reachable from an entry point**, reported as a *path*, not a yes/no.
- **Every note carries a classification**, from a closed enumeration held in one retrievable location.
- **A spine note never states behaviour a specification owns** — a normative `MUST` in an orientation
  note is refused, because a note that states behaviour has quietly become a second source of truth.
- **A cited artifact names an obtaining note, with its revision pinned** — whether the fetch step
  actually works is a person's job, and today it is
  [an open gap](docs/history/obtaining-the-reference.md). The gate narrows the surface; it does not
  close it, and it says so.
- **Requirement text has exactly one copy.** A second copy fails; one copy and a link is the fix.
- **A generated index cannot drift**, and a generator is verified against something other than a
  re-run of itself.
- **Every rule names its gate, and every gate names its rule** — so the rule index publishes what
  proportion of the rules nothing actually enforces.
- **Every gate is demonstrated to fail.** Each gate is paired with a deliberately broken input under
  `ci/broken-inputs/`, and a meta-gate fails if any gate *passes* on its own violating input.

A green run **states its own coverage** — which roots it examined and which it excluded, by name —
rather than implying it covered everything. And every entry file is held under a size ceiling and
checked for naming artifacts the repository does not contain, because *an entry file is the one place
where a false claim is guaranteed to be read first*.

→ [the rule index, with what is and is not enforced](docs/rule-index.md) ·
[authority precedence](docs/method/authority-precedence.md) ·
[authoring conventions](docs/method/conventions.md) ·
[documentation rules](docs/method/documentation-rules.md)

---

## Run it yourself

Requirements: **Python 3** (standard library only — no dependencies, no lockfile) and a full-history
clone. [OpenSpec](openspec/config.yaml) is needed only for the two planning commands.

```bash
make check          # every vault gate; one command, and CI runs it
```

```bash
make check-gates    # the meta-check: every gate proven to fail on its own broken input
```

```bash
make check-links    # the link-resolution gate alone
```

```bash
make check-report   # every gate, report-only; always exits zero
```

```bash
openspec list                                   # task progress
openspec validate rebuild-plugboard --strict    # the gate for any openspec/ commit
```

`make check` enumerates every gate it ran and the roots each covered, so the gate inventory is a
build output rather than a number in prose. There is deliberately no `make test`, `make dev` or
`make lint` yet — those arrive with the component skeletons they would dispatch to, and claiming them
now would be the exact defect this harness exists to catch.

### Every number this page computes, and the command that computes it

The repository's own standard is that a figure a reader cannot recompute is a figure that will go
stale and tell nobody — it has already deleted its own task counts on exactly that reasoning. So the
live figures are not printed here; these are the commands that produce them:

```bash
openspec list                                                    # tasks done / total, per change
ls openspec/changes/rebuild-plugboard/specs/*/*/spec.md | wc -l  # specifications
grep -rh '^### Requirement:' openspec/changes/rebuild-plugboard/specs | wc -l
grep -rh '^#### Scenario:' openspec/changes/rebuild-plugboard/specs | wc -l
python3 ci/gates/citations.py                 # citations, and where each one resolved
python3 ci/gates/rule_gate_correspondence.py  # rules, and how many carry a gate today
```

The figures about the **prior art** above — the auditor count, the 27,000 lines of tests, the three
blocking defects — are the exception, and are attributed rather than advanced: they are the audit's
own figures, taken against `reference/Plugboard` at `6756a07` and `reference/Telephone` at `9ccba86`,
and no command in this repository reproduces them, because that tree is not in it.

---

## Repository layout

| path | what it holds |
|---|---|
| [`docs/`](docs/index.md) | The vault. Orientation, rationale, decisions, glossary, code standards — an [Obsidian](https://obsidian.md) vault with its reader settings tracked and per-person state ignored. States no behaviour. |
| [`openspec/`](openspec/changes/rebuild-plugboard/tasks.md) | The plan. Proposal, decision register, the task list, and the sixteen capability specifications. Owns behaviour. |
| `ci/` | The gate harness: one Python module per gate, a paired broken input per gate, and the generators for the indexes that must not drift. |
| `.github/` | The runner. No path filter, no branch filter, no `continue-on-error` — each checked by a gate, so the workflow comment is not the enforcement. |
| [`CLAUDE.md`](CLAUDE.md) · [`AGENTS.md`](AGENTS.md) | Routers for coding agents. Both are entry files under a size ceiling; neither carries content. |
| [`.agents/`](.agents/README.md) | Project skills for Codex and other agents that read `.agents/skills/`. Includes OpenSpec workflows and Matt Pocock skills; the guide explains their place in this repository. |
| `reference/` | Read-only prior art. Gitignored, absent, and **not a source of truth for behaviour**. |
| `proxy/` `sidecar/` `terminator/` `contract/` `conformance/` | Declared, planned, and **not yet created**. |

---

## Where to start reading

**Read [`docs/start-here.md`](docs/start-here.md) first.** It carries the five facts above, an
orientation diagram, and a routing table keyed by what you are doing — the point being that you read
the row that matches your task, not the whole vault.

| you want | read |
|---|---|
| the argument, end to end | [what it is](docs/why/what-it-is.md) → [who it is for](docs/why/audiences.md) → [version skew](docs/why/version-skew.md) → [the architecture](docs/how/architecture.md) |
| the behaviour | [the wire contract](openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md), then the capability that owns what you are touching |
| a capability, before a thousand-line specification | [the capability notes](docs/capabilities/index.md) — what each owns, what it explicitly does not, and what breaks if it changes |
| to disagree with a decision | [decisions in force](docs/decisions/in-force.md) — read its entry before re-litigating; one was overturned outright |
| what a word means here | [the glossary](docs/glossary.md), which also names the terms nothing defines — the more useful half |
| how something fails | [the failure taxonomy](docs/how/failure-taxonomy.md): one failure, three viewpoints, and the silent class |
| the system from one side | [the operator's view](docs/how/operator-view.md) · [the tenant's view](docs/how/tenant-view.md) |
| security | [the threat model](docs/how/threat-model.md) — adversary, asset, control, and the gaps named as gaps |
| to write code here | [reviewing](docs/code/reviewing.md) · [testing](docs/code/testing.md) · [the eight banned patterns](docs/code/banned-patterns/index.md) |

The canary among the banned patterns is **headers as a map**. `map[string]string`, `Map.new`, or
`Enum.into(…, %{})` over header fields — with `Set-Cookie` as the case that proves it, because a login
endpoint issuing a session cookie and a CSRF cookie returns one of them, the user appears logged in,
and every subsequent `POST` fails validation.

---

## Contributing

[Contributor experience](docs/code/contributing.md) states the bar: `make dev` from a clean clone, a
fast suite that needs no Postgres, and **the conformance suite as the on-ramp** — *"write a sidecar in
your language; here is the suite that tells you when you are done."* Good first issues are intended to
be the reserved-but-unimplemented frame types, each a bounded piece of work against an existing
primitive with a fixture already written.

None of that exists yet — there is no conformance suite to be an on-ramp to. What does exist is
[`CONTRIBUTING.md`](CONTRIBUTING.md), and it arrived with the check that keeps it honest: the three
canonical enumerations it carries are read from [reviewing](docs/code/reviewing.md) on every run, so
an item added there fails the build until `CONTRIBUTING.md` names it. The reference attempt's README
linked to a `CONTRIBUTING.md` that was never written, and *first impressions of a portfolio project
are made of exactly this*.

`make check` must be green, every claim carries a citation or an explicit `Unverified` marker, new
commits carry a [sign-off](DCO), and [the conventions](docs/method/conventions.md) are generated from
the same enumeration the gates key on, so the list you read and the list that fails you cannot
diverge.

---

## Authority, in one line

The contract wins, then the specifications, then the decisions in force, then the vault notes, then
the generated indexes. Where two disagree, the higher one is right — and a note that contradicts the
specification it points at is simply wrong.
→ [precedence](docs/method/authority-precedence.md)

---

## Licence

[Apache-2.0](LICENSE) — the work this repository authors: the notes, the sixteen specifications, the
gate harness, and the component directories when they exist. Contributions arrive under the same terms
by §5 of that licence, which does not depend on this repository living on GitHub. The name is not part
of the grant: §6 conveys no trademark rights, so *Plugboard* stays governed separately from the code.

`.claude/` and `.agents/` are excluded, and [`LICENSE`](LICENSE) says so above the Apache text rather
than leaving it to a notice. They are vendored agent harnesses this repository did not author. The
Claude harness still carries an unresolved provenance gap
([notice](.claude/THIRD-PARTY-NOTICES.md)); the Codex harness records its three MIT-licensed upstreams,
their copyright notices and the installed Matt Pocock skill hashes
([notice](.agents/THIRD-PARTY-NOTICES.md), [lock](skills-lock.json)).

→ [why Apache-2.0, and the alternative it beat](docs/decisions/d28-licensing.md)
