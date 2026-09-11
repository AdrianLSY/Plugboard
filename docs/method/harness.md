---
type: essay
status: current
authority: rationale
---

# The harness, and the findings that built it

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

That table **is** the methodology. Everything below, and everything in the five notes it now points
at, is its implementation:

- [Reviewing a change](../code/reviewing.md) — pull requests, the change description, the
  review checklist
- [Testing](../code/testing.md) — the tiers, mutation thinking, adversarial fixtures, and the four
  prohibitions on test shape
- [Contributing](../code/contributing.md) — what a contributor meets first
- [Documentation rules](documentation-rules.md) — falsifiability, and one copy of requirement text
- [Supply chain](supply-chain.md) — dependencies, provenance, changelog and versioning

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

1. `docs/start-here.md` — the five governing facts
2. `docs/how/architecture.md` — the primitives and the contract
3. The relevant OpenSpec artifacts for the change at hand
4. `docs/history/carry-forward.md` — before writing anything the reference already got right

Those are the paths this change moves them to; the ordered reading path itself is owned by
`docs/start-here.md`.

### Verify agent output adversarially

The single most valuable technique from this session: **have one agent produce findings and a second
agent try to refute them, defaulting to refuted when uncertain.** In the runtime research, that pass
caught two fabricated quotes, one non-existent library capability, and one misattributed causal claim —
and **overturned the recommendation.** The first answer was confident, well-cited-looking, and wrong.

Apply it to anything expensive to reverse: architecture decisions, dependency choices, security claims,
and any assertion about what a library or spec does. Verify library capabilities against the published
API, not against a plausible sentence.

### Prototype a check before you require one

Refutation catches a wrong claim. It does not catch a rule that is right in prose and unusable in
practice, because that failure is invisible until something runs. The cheap version is to build the
check in a scratch directory, run it against the real tree, and open every single thing it flags.

The numbers from the one time this was done properly are the argument. Five requirements about gate
soundness were drafted, and each was then prototyped and run over the vault before its text was
fixed: between them the literal readings produced roughly **1,071 findings, and almost none were
defects**. One trigger — "published in a tracked artifact a reader is routed to" — narrowed nothing at
all, because an in-force requirement already makes nearly every note reachable from an entry point.
Another demanded a value six gates have no way to supply. A sixth requirement was cut outright after
483 findings yielded zero true positives and a measured regression against the rule already in force.

None of that was visible by reading. All of it was visible in ten minutes of running.
[The gate-harness design](../../openspec/changes/harden-vault-harness/design.md) records each
reversal with the measurement that forced it, which is the part worth imitating: a decision reversed
on evidence is more useful to the next reader than a decision that was right first time. Its
[task list](../../openspec/changes/harden-vault-harness/tasks.md) then orders the work so that every
declaration lands before the gate that reads it and the runner lands last — a check introduced
against a red tree teaches everyone to ignore it.

> Orientation, not behaviour. The specifications win.
