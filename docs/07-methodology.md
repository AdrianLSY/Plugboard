# Development methodology

**Every rule here is derived from a specific way the previous attempt failed.** None of it is process
for its own sake. Where a rule exists, the finding that motivated it is cited, so you can judge whether
the rule still earns its keep.

The previous system was built by an older-generation model in a harness with no gates. It produced
27,000 lines including more test code than production code, zero `TODO` markers, 148 KB of
documentation — and it does not forward `POST` bodies. **Volume was never the problem. The absence of
constraints was.**

---

## The finding-to-constraint table

| observed failure | constraint |
|---|---|
| Empty bodies forwarded; the one test named for payload passing uses `GET` | One end-to-end test that POSTs bytes and asserts the sidecar received *those exact bytes* — **written before the proxy exists** |
| U+FFFD corruption on HTTP bodies while the WebSocket path base64-encodes correctly | One body-transport abstraction, binary-safe, used by both paths. A second implementation is a review blocker |
| `proxy_res` asserted by nothing; `ws_check` untested and undocumented; timeouts already drifted | A versioned schema, generated types, and a conformance suite both sides run. The contract is enforced by tooling, not discipline |
| A wait helper that calls `reload_all()` on timeout and reports success | **Never let a test helper repair the state it is waiting for.** Drive notifiers with synthetic messages; prove delivery separately in a committing integration test |
| Test config sets `m_cost: 8` and `allow_localhost_hooks: true` | Production-equivalent security config in test. Speed comes from architecture, never from disabling the property under test |
| 27 of 43 files `async: false`; Postgres required for pure-function tests | A pure core with a thin database edge, so the fast suite is what runs on save |
| 75 telemetry emissions, zero handlers, one `Logger` reference and it is a comment | A metric sink and structured logger chosen in week one, with a telemetry-attach test as the gate |
| Neither image boots; the env-var contract lives in three drifting places | Generate the Dockerfile `ENV` block and `.env.example` from one config schema; CI asserts a real health probe, not a curl for 200 |
| Global projection rebuild on every tenant's change | Tenant-scoped projections and tenant-keyed reconciliation as a day-one data-model decision |
| Major dependency bumps auto-merge, then auto-push a submodule pointer | Auto-merge gated on `semver-patch`; a wire-protocol pointer never advances without a human |
| `mix precommit` ran `--warning-as-errors` (singular) for months; CI ran the correct flag | **Test the gates.** A guardrail nobody verified is not a guardrail |
| `hooks_test.exs:425` contains the model's abandoned reasoning as committed comments | Reviewers reject uncertainty markers in tests. A comment saying "actually this shouldn't be circular… let me think again" is a merge blocker |
| Three tests written around defects instead of exposing them | A test that documents a bug in a comment must open an issue instead. Accommodating a defect in a test is how it survives |

That table **is** the methodology. Everything below is its implementation.

---

## Pull requests

**Trunk-based, short-lived branches, PR required.** The reference pushed 119 commits directly to
`main` with messages like `updated code` ×17. The sidecar used PRs and conventional commits and is
visibly the better-maintained half — that difference is the argument.

**Branch protection on `main`:**
- No direct pushes. No force pushes.
- Required checks: fast suite, lint, format, conformance suite, security scan.
- Linear history (squash merge), so `main` reads as one commit per change.

**PR size.** If a PR cannot be reviewed in one sitting, split it. This is a hard constraint for a
solo-maintainer project with outside contributors, because unreviewable PRs are either merged unread or
abandoned — and both happened in the reference.

**Every PR states, in the body:**
1. **What breaks if this is wrong.** Not what it does — what it *breaks*. This one question would have
   caught the empty-body defect.
2. **The wire-contract impact**: `none` / `additive` / **`BREAKING`**. A `BREAKING` answer requires a
   version bump and a capability flag, and cannot be merged without one.
3. **What was tested, and what the test would catch that a wrong implementation would not.**

### PR template

```markdown
## What breaks if this is wrong?

## Wire contract impact
- [ ] None
- [ ] Additive (new optional field / reserved frame type now used)
- [ ] **BREAKING** -- requires version bump + capability flag

## Tests
Name the specific wrong implementation each new test would reject.

## Checklist
- [ ] Fast suite passes locally (no Postgres required)
- [ ] Conformance suite passes
- [ ] No new `async: false` without a comment saying why
- [ ] No uncertainty markers in tests (no "actually…", no "let me think", no `@tag :skip`
      without a linked issue)
- [ ] Docs updated, or "docs: n/a" with a reason
```

---

## Code review

**A checklist, because the failures were systematic rather than clever.** Reviewers check these in
order; the first four are the ones that would have caught actual shipped defects.

1. **Does the body survive?** Any change touching the request or response path: does the payload cross
   the boundary intact, and is there a test asserting the exact bytes?
2. **Are headers still an ordered list of pairs?** Any `Map.new`, `Enum.into(…, %{})`, or
   `map[string]string` over headers is a review blocker. `Set-Cookie` is the canary.
3. **Does the method pass through unmodified?** No allowlist, no rewriting.
4. **Does it stream, or does it aggregate?** Any `io.ReadAll`, any accumulation into a list before
   emitting, any size check that requires the whole body first.
5. **Does the test prove the thing?** Specifically: would this test fail against a plausible wrong
   implementation? If a reviewer cannot name that implementation, the test is decorative.
6. **Is the mutation authorized in its signature?** Every context mutation takes the acting principal.
   A caller-side check is not sufficient — that is exactly how `update_token/2` became a cross-tenant
   write.
7. **Is the queue bounded?** The reference has exactly one bounded queue in 20,000 lines. Every new
   buffer, mailbox, or accumulator needs a bound and an explicit overflow behaviour.
8. **Is the error typed?** No `inspect(reason)` on the wire — no client can branch on an Elixir term
   rendering.

**Reviewers reject, not fix.** A reviewer who fixes the problem removes the author's chance to learn
the pattern, and in a solo-maintainer project with AI-assisted contributors that is how the same defect
returns.

### AI-generated PR review

Assume a fraction of contributions are model-written, because they will be. The audit gives the
signature to look for:

- **Tests that accommodate a defect** rather than exposing it — usually visible as a comment explaining
  why the test avoids the obvious case.
- **Abandoned reasoning committed as comments.** "Actually this shouldn't be…", "let me think again",
  "for now we just…".
- **Named for one thing, asserting another.** Four tests in the reference assert the negation of their
  own name, three of them saying so in their own comments.
- **`@tag :skip` with a false claim about coverage elsewhere.** The reference skipped its only
  mount-point hook success test, claiming another file covered it. It did not.
- **Tautological assertions** — asserting a value the test just set, or asserting only that a call did
  not raise.
- **Volume where depth is needed.** A 637-line test file against a 245-line config module is a signal,
  not a virtue.

---

## Testing

**Three tiers, and the first one is a correctness control.**

```
  FAST         no Postgres, no network, no sleeps, fully async.
               Target: under 10 seconds. This is what runs on save.
               Pure functions, changesets, framing, parsing, routing logic.

  INTEGRATION  real Postgres, real sockets, committing transactions.
               Notifier delivery lives here -- NOT in the fast tier, because
               pg_notify is transactional and a sandbox never commits.

  CONFORMANCE  the wire contract, run against every implementation.
               The authority. Adversarial fixtures, not happy paths.
```

**Why the fast tier is a correctness control, not a convenience.** The completeness critic's
conclusion, and the most useful sentence in the whole audit:

> When feedback is slow, an agent (or a person) writes assertions that are cheap to satisfy rather
> than assertions that are expensive to satisfy.

The reference's suite required Postgres for tests of pure functions and serialised 27 of 43 files.
That is upstream of the test-quality problem, not parallel to it. **Treat suite latency as a defect
class.**

### Mutation thinking as the review standard

For any new test, the author states: *name a one-line change to the code under test that this test
would not catch.* If the answer is "none", good. If the answer is easy, the test is weak. This is the
probe that surfaced most of the audit's test findings, and it is cheap to apply in review.

### Conformance fixtures, seeded adversarially

The suite starts from cases that break naive implementations, **written before the implementation**:

- a lone `0x80` byte in a body (kills UTF-8 coercion)
- two `Set-Cookie` lines (kills header maps)
- both `Content-Length` and `Transfer-Encoding` (must be rejected, not reconciled)
- `%2F` inside a path segment (must not be normalised)
- a trailing-slash collection URI (WebDAV depends on it)
- a `HEAD` with non-zero `Content-Length`
- a fragmented WebSocket message (kills message-level libraries)
- a response that emits headers then stalls 90 seconds (kills total-timeout designs)
- a `PROPFIND` (kills method allowlists)
- a response body larger than memory (kills aggregation)
- a client that disconnects mid-stream (proves cancellation propagates)

**Never disable a property in test config to make a test pass or fast.** If Argon2 is too slow for
tests, the architecture is wrong — not the cost parameter.

---

## Changelog and versioning

The reference has **no changelog anywhere** and 119 commits of `updated code`. Two version streams
matter and they are independent:

**The wire contract** is versioned separately from the software, and is the one users depend on.
`contract/CHANGELOG.md` records every version with:
- what was added (new frame type, new capability flag, new optional field)
- what was deprecated, and the earliest version that may drop it
- **which sidecar versions remain compatible** — the question a tenant actually has

Contract changes are **additive by default**. A breaking contract change requires a new major version,
a capability flag, and a documented period during which both are served. Since old sidecars are
permanent, "breaking" means "supported forever in parallel", so the bar is high.

**The software** (proxy, sidecar, terminator) uses semantic versioning with conventional commits, which
the sidecar already did well (`#2`–`#32`) and the proxy did not. Changelog entries are generated from
commit messages, so commit messages are a reviewed artifact.

**Release notes state the contract version range**, because that is what determines whether a tenant
must act.

---

## Documentation

The reference had 148 KB of prose against a history of `updated code`, and two documented claims are
verifiably false. The lesson is not "write less" — the prose is where intent was recorded and is the
most valuable thing in the repository. The lesson is **the docs must be falsifiable.**

**Rules:**

1. **Every behavioural claim carries a `file:line` citation or a test name.** A claim with neither is a
   claim nobody can check, and two such claims in the reference were false.
2. **Configuration documentation is generated**, not written. The reference's env-var tables were the
   *reliable* half of its docs precisely because they tracked something mechanical. Generate the
   Dockerfile `ENV` block, `.env.example`, and the config reference from one schema.
3. **Docs bump in the same PR as the behaviour.** Not "afterwards" — the reference's `AGENTS.md` said
   *"After completing any task, review and update README.md, AGENTS.md and CLAUDE.md"*, and it drifted
   anyway, because a rule with no gate is a wish.
4. **The gate:** a PR touching the wire contract, a public API, or a documented behaviour and *not*
   touching docs must say `docs: n/a` with a reason. CI checks for the marker's presence, not its
   correctness — the reviewer checks correctness.
5. **Record deliberate omissions next to the code.** `router.ex:47-49` is the standard: a security
   control dropped, with the reason. That comment is more valuable than the 60 KB README.
6. **`docs/` is for orientation and rationale; the contract is for behaviour.** When they disagree, the
   contract wins and `docs/` is wrong. Say so explicitly at the top of any doc that describes
   behaviour.

---

## AI harness

The previous system's quality ceiling was set by its harness. **This is the most leveraged artifact in
the rebuild**, and it works by making the wrong thing hard rather than by asking for the right thing.

### Structural gates, not instructions

An instruction the model can skip is not a gate. Enforce in CI:

- **Format and lint on the proxy too.** The reference had `credo` as a declared dependency that nothing
  ever invoked, no format check, no Dialyzer, no Sobelow, no dependency audit — while the *sidecar* had
  30 linters and weekly vulnerability scans. The harness improvement landed on the component with the
  smaller attack surface. The proxy terminates untrusted traffic, runs the admin UI, and holds every
  credential.
- **A module-size and function-size ceiling.** The reference has an **813-line `render/1`** inside a
  1,380-line LiveView handling four unrelated resources with 20 `handle_event` clauses. A CI ceiling
  makes that unwritable rather than merely discouraged.
- **A duplication gate.** `MountStore` and `HookStore` are the same GenServer twice — 128 of
  `hook_store.ex`'s 199 non-comment lines appear verbatim in `mount_store.ex`, including a byte-identical
  12-line reconcile block with its comments. Domain affinities were then bolted *inside* `MountStore`
  because there was no third slot. A duplication check would have forced the abstraction on the second
  instance.
- **Ban the specific defect classes** with lint rules or a custom check: header maps, `io.ReadAll` on a
  proxied body, `with` in a controller action without an `else`, `start_link` without `trap_exit` in a
  GenServer that monitors, `inspect/1` on a wire payload.
- **Test the gates.** `mix precommit` ran `compile --warning-as-errors` (singular, wrong flag) while CI
  ran the plural. Nobody checked whether the checker checked. Add a test that a deliberately-broken
  commit fails each gate.

### Spec-first, enforced by the workflow

OpenSpec is already in the repository. Use it: `proposal.md` → `specs/` → `design.md` → `tasks.md`,
then implement. The reference's `feature.md` was a 37 KB specification for a hooks subsystem whose
central feature — enriching the request body — **was never wired up**. A spec that is not traceable to a
test is a wish; the workflow exists to make that traceability mechanical.

### Agent context files

Keep `CLAUDE.md` / `AGENTS.md` short and pointed at `docs/`. The reference had a 24 KB `AGENTS.md`
mostly restating Phoenix conventions the model already knows, and almost nothing about the system's own
invariants. Invert that ratio: name the invariants, the banned patterns, and the citations. Framework
tutorials are not context.

### What to put in front of an agent, in order

1. `docs/README.md` — the five governing facts
2. `docs/02-architecture.md` — the primitives and the contract
3. The relevant OpenSpec artifacts for the change at hand
4. `docs/06-carry-forward.md` — before writing anything the reference already got right

### Verify agent output adversarially

The single most valuable technique from this session: **have one agent produce findings and a second
agent try to refute them, defaulting to refuted when uncertain.** In the runtime research, that pass
caught two fabricated quotes, one non-existent library capability, and one misattributed causal claim —
and **overturned the recommendation.** The first answer was confident, well-cited-looking, and wrong.

Apply it to anything expensive to reverse: architecture decisions, dependency choices, security claims,
and any assertion about what a library or spec does. Verify library capabilities against the published
API, not against a plausible sentence.

---

## Supply chain

- **Dependabot on**, auto-merge gated on `version-update:semver-patch` **only**. The reference invoked
  `fetch-metadata` and never referenced its `update-type` output, so major bumps merged on the same terms
  as patches.
- **`govulncheck` and Trivy on push, PR, and a weekly cron**, so newly disclosed CVEs surface without a
  code change. Port the sidecar's `security.yml`; add the equivalent for the proxy, which has none.
- **No automated pointer advance for anything encoding the wire protocol.** A human approves.
- **Establish provenance for every binary asset.** The reference ships 85 JPEGs of unestablished origin
  under a blanket MIT claim with no attribution — for a feature that is inert in production for three
  independent reasons.

---

## Contributor experience

Three audiences with conflicting wants ([System](01-system.md)); this is the part that serves
contributors specifically.

- **`make dev` works from a clean clone.** No 16-variable scavenger hunt. The no-defaults configuration
  policy is right for production and hostile for development — resolve it by shipping a complete
  `.env.example` generated from the schema, reporting *every* missing variable at once, and providing a
  dev profile.
- **The fast suite runs without Postgres.** Non-negotiable, per the correctness argument above.
- **The conformance suite is the on-ramp.** "Write a sidecar in your language; here is the suite that
  tells you when you are done" is the best-scoped, highest-status contribution an outside contributor
  can make, and it exists as a side effect of D3.
- **Good first issues are the reserved-but-unimplemented frame types.** Trailers, 1xx interim responses,
  Range — each is a bounded piece of work against an existing primitive with a conformance fixture
  already written.
- **`CONTRIBUTING.md` must exist.** The reference's README linked to it, and to `FUTURE_WORK.md`, and
  **both were dead links.** First impressions of a portfolio project are made of exactly this.
