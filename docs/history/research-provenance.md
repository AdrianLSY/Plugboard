---
type: essay
status: current
authority: rationale
---

# Research provenance

Every decision in force is a conclusion. The investigation that produced it — how many passes, which
sources, what was checked by a second reader and what was not — survives only as a sentence or two
inside the register. This note collects it, because a conclusion whose provenance is nowhere can be
reopened for free: the next person to prefer Rust has no way to learn that the argument for it was
already run, and lost on a fabrication rather than on merit.

Read this before reopening anything. The place to disagree with the conclusions themselves is
[decisions in force](../decisions/in-force.md).

## What was investigated

| Pass | Subject | Recorded size | Recorded at |
|---|---|---|---|
| Protocol and runtime research | Nine protocol families, plus a runtime assessment | 12 agents, 492 tool calls | `openspec/changes/rebuild-plugboard/design.md:9`, `docs/how/protocol-fidelity.md:9-12` |
| Adversarial review of that research | The **two** load-bearing conclusions only | not recorded separately | `openspec/changes/rebuild-plugboard/design.md:9` |
| Audit of the prior art | Test depth, code quality, the cross-component contract | 7 auditors + 1 adversarial verifier per auditor's top claims + 1 completeness critic; 15 agents, 741 tool calls | `docs/history/reference-audit.md:20-24` |

Sources for the research pass are recorded as primary: RFCs, W3C specifications, MDN, IETF drafts and
library repositories (`docs/how/protocol-fidelity.md:9-10`). The audit was read-only throughout and
nothing was executed (`docs/history/reference-audit.md:23-24`) — which is why "neither container
boots" was reached by reading a Dockerfile's `ENV` block rather than by running it.

**The agent count is recorded two ways, and this note does not reconcile them.**
`openspec/changes/rebuild-plugboard/design.md:9` reads *twelve research agents over nine protocol
families plus a runtime assessment*; `docs/how/protocol-fidelity.md:9-12` reads *nine research
agents over the protocol families* and then gives *12 agents, 492 tool calls* as the total. Nine
researchers plus a runtime assessment plus two adversarial reviewers is twelve, so the two are
reconcilable — but nothing in this repository says that is the arithmetic intended, and the totals
(12 agents, 492 tool calls) are the only figures both statements agree on. Treat those two as the
provenance; treat the split between research and review as unrecorded.

## The two conclusions that were checked, and what happened to each

Only two conclusions from the research pass were handed to adversarial reviewers
(`openspec/changes/rebuild-plugboard/design.md:9`). Both outcomes are load-bearing, and they went
opposite ways.

**Upheld, with corrections — the WebTransport verdict.** WebTransport stays out of v1, reserved in
the contract, shipped later behind a separate terminator (`docs/how/protocol-fidelity.md:216-218`).
The review left the verdict standing and *corrected the reason*
(`docs/how/protocol-fidelity.md:220`): Safari 26.4 shipped WebTransport with the HTTP/2 fallback, so
"no honest configuration exists" is dead (`docs/how/protocol-fidelity.md:240-242`), and
`draft-ietf-webtrans-http2` turned out to be a usable blueprint rather than only an argument
(`docs/how/protocol-fidelity.md:243`). The conclusion now in force is
[D26 — WebTransport is designed for, not shipped](../decisions/d26-webtransport-deferred.md); the
surviving reasons are enumerated under
[WebTransport in protocol fidelity](../how/protocol-fidelity.md#webtransport).

**Overturned — the runtime recommendation.** The earlier recommendation was Rust for the proxy, on
the premise that WebTransport requires HTTP/3 termination in the same process as the tunnel, which
would have removed the BEAM from consideration on capability grounds
(`openspec/changes/rebuild-plugboard/design.md:88`). The premise did not survive the check.

> **The decision that superseded it:**
> [D4 — Runtime: Elixir proxy, Go sidecar, Go H3 terminator later](../decisions/d04-runtime.md).

## What the overturn caught

Five claims held the Rust recommendation up. Each row below gives the finding as the register records
it, the class of defect, and the check that separated it from a true claim. The five findings are
`openspec/changes/rebuild-plugboard/design.md:92-96`; the verification-method column is this note's
reading of what each check consisted of, stated so the method is reusable rather than admired.

| Claim | Finding | Class | How it was checked |
|---|---|---|---|
| `tokio-quiche` is the Rust stack for QUIC/H3/WebTransport | Neither `quiche` nor `tokio-quiche` implements WebTransport. `cloudflare/quiche#1114` open since 2021-12-11; Cloudflare, 2025-08-26: *"we can't commit to any timeline or prioritization."* No WebTransport item in either published API | Non-existent library capability — and it was the capability the stack had been recommended **for** | Enumerated the published API of both crates, and read the tracking issue for its own status — not the recommendation's description of the crate |
| MDN: *"WebTransport exclusively uses HTTP/3 and does not fall back to HTTP/2"* | Sentence does not exist on the page or in `mdn/content` source. Fabricated — and the entire "same process, therefore no BEAM" chain rested on it | Fabricated quotation | Searched both places the sentence would have to exist: the rendered page, and the `mdn/content` source the page is built from |
| Tokio: *"preemption is out of scope… for the foreseeable future"* | Not on the cited page. The post exists to announce the mitigation (a 128-operation per-task budget since 0.2.14). Fabricated | Fabricated quotation, and inverted — the cited page argues the opposite | Read the cited page end to end, rather than accepting that a citation pointing somewhere real makes the quotation real |
| Pingora: 70% less CPU, nginx→Rust | Figures accurate, attribution wrong. Cloudflare credits *"our new architecture which can share connections across all threads"*; the language comparison is against **Lua** | Misattributed causal claim — true number, invented cause | Read the source of the figure for the cause *it* states, and for what it was measured against |
| No Go equivalent | `quic-go` powers **cloudflared** — structurally this exact product — plus `frp`, `reverst`, Caddy, Traefik | Refuted by counterexample | Looked for a shipped deployment of the shape claimed impossible |

**The transferable lesson is the method, not the tally: check against the published API, not against
a plausible sentence.** Two of these five were quotations, and a fabricated quotation is
indistinguishable in prose from a real one — same register, same specificity, attributed to a real
page. What separated them was going to the artifact and enumerating it: the crate's API index, the
documentation repository's source, the blog post's own stated cause. The same move is what the
citation convention in [the documentation rules](../method/documentation-rules.md) exists to force,
and it is why an admitted gap is preferred here over a confident sentence — see
[obtaining the reference](obtaining-the-reference.md), which declines to guess a `git clone` URL for
exactly this reason.

Note what the overturn did **not** do. It did not find Rust unsuitable. It removed the constraint
that had made the runtime question look already-answered
(`openspec/changes/rebuild-plugboard/design.md:100`), after which a different argument — the work
that has to ship, not the language — decided it. Reopening D4 means engaging that argument, not this
table.

## The audit of the prior art

The prior art was audited by seven independent auditors, each auditor's top claims handed to an
adversarial verifier instructed to refute them and to default to *refuted* when uncertain, with one
completeness critic over the whole digest (`docs/history/reference-audit.md:20-24`). Its output:
**98 findings — 66 confirmed, 28 downgraded or made more precise, 4 killed**
(`docs/history/reference-audit.md:22-23`). So roughly a third of what the auditors produced was
weakened or removed by the verification step; the confirmed remainder is
[the reference audit](reference-audit.md).

Three of its conclusions became decisions, and each is worth tracing back:

- **The contract findings → [D23 — contract-first, with a conformance suite](../decisions/d23-contract-first.md).**
  The audit found the wire contract asserted twice, independently, against two different fictions —
  a test framework that replaces the serializer with a no-op, provably so because
  `telephone_channel_test.exs:101` asserts an atom key that cannot survive JSON, and Go tests
  marshalling a struct whose tags production never uses
  (`openspec/changes/rebuild-plugboard/design.md:259`).
- **The observability finding → [D27 — observability before the hot path](../decisions/d27-observability-first.md).**
  The detail that makes it a decision rather than a preference is a provenance detail: *five of seven
  auditors cited the telemetry as evidence of good instrumentation*
  (`docs/history/reference-audit.md:239-240`), and the completeness critic found no handler was ever
  attached. Emission is visible in review; consumption is not.
- **The completeness critic's root-cause finding → [testing](../code/testing.md).** Quoted from
  `docs/history/reference-audit.md:246-247`:

  > When feedback is slow, an agent (or a person) writes assertions that are cheap to satisfy rather
  > than assertions that are expensive to satisfy.

  Recorded as the audit's most useful sentence (`docs/history/reference-audit.md:243-244`) and
  carried into the register as a named risk with suite latency treated as a correctness control
  (`openspec/changes/rebuild-plugboard/design.md:148`).

**The completeness critic is the shape of pass most worth repeating.** Six auditors examined code
and tests exhaustively; none asked whether the system could be deployed, observed, or contributed to
(`docs/history/reference-audit.md:233-234`). A hole every pass shares is a hole no pass reports, and
adding auditors of the same shape does not find it — the thirteenth agent over the same question buys
less than the first agent over a different one.

And the failure this whole vault is arranged against was itself an audit finding: 148 KB of prior-art
prose containing two documented claims that are verifiably false — a headline "O(1) path matching"
that is O(depth), and a doc comment claiming an error is logged where no logging call exists
(`docs/history/reference-audit.md:284-289`).

## What is not recorded, and is therefore not known

Stated rather than smoothed over, because an unrecorded number invites an invented one.

- **How much of the research went unchecked.** Two conclusions were handed to adversarial reviewers
  (`openspec/changes/rebuild-plugboard/design.md:9`). Nothing records a second reader for the rest,
  so the protocol-family findings in [protocol fidelity](../how/protocol-fidelity.md) carry their
  primary sources but not an adversarial pass.
- **Whether the fabrications were bounded at four.** Four turned up in one of the two reviewed
  conclusions. Nothing in this repository establishes how many are in the unreviewed remainder, and
  the honest reading of a base rate of four-in-one-conclusion is that the remainder has not been
  cleared.
- **The research pass's finding count.** The audit's is recorded as 98 with its disposition; no
  equivalent figure exists for the research pass — not per protocol family, not in total.
- **Which agent produced which finding.** Neither pass records attribution below the level of the
  pass itself, so a finding cannot be traced to its author or re-run against its original prompt.
- **Dates.** Neither pass records when it ran. The newest dated evidence inside the findings —
  Cloudflare's 2025-08-26 comment, Safari 26.4 in March 2026 — bounds them from below and nothing
  bounds them from above, so "how stale is this research" is not answerable from this repository.

> **Unverified.** The audit's per-finding evidence exists as a published report with collapsible
> evidence per finding, whose URL is recorded at `docs/history/reference-audit.md:26-27`, and that
> report is the only place the 98 findings are individually enumerated — this vault carries the
> confirmed subset in prose. Whether that URL is reachable by anyone other than its author has not
> been checked. — needs checking by opening it from an unauthenticated session; if it is not
> reachable, the 66 confirmed findings are checkable only through their `file:line` citations into
> the prior art, per [obtaining the reference](obtaining-the-reference.md).

> Provenance, not behaviour. The register owns the decisions and the specifications own what the
> system does.
