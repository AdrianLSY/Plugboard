# CLAUDE.md

## State of the repository

No source yet, no commits. What exists is the plan: `docs/` (rationale, invariants) and
`openspec/changes/rebuild-plugboard/` — `proposal.md`, `design.md`, 16 specs, a 709-item `tasks.md` at
0 done. `reference/` is the previous attempt: gitignored, read-only prior art that **does not work**.
Cite it only with a `file:line`, never as a source of truth for behaviour.

Planned layout (task 1.1): `contract/` · `proxy/` (Elixir) · `sidecar/` · `terminator/` (Go) ·
`conformance/` · `docs/`. One repo, no submodules — a CI guard enforces that.

## Commands

Only OpenSpec commands exist today; `make` targets and test tiers arrive with tasks 1.7 and 2.x.

```bash
openspec list                                 # task progress
openspec show rebuild-plugboard               # the artifacts
openspec validate rebuild-plugboard --strict  # gate for any openspec/ commit
```

Work tasks with `/opsx:apply`, revise the plan with `/opsx:update`; never hand-edit checkboxes
while a skill owns them.

## What to read, in order

`docs/README.md` (the five governing facts, first every time) → `docs/02-architecture.md` →
`design.md` (D1–D20 in force) → `docs/06-carry-forward.md` (before rewriting what the reference
got right) → `docs/07-methodology.md` (before any PR or test). `docs/05-decision-log.md` overlaps
`design.md` and its "Open questions" table is stale — D16–D20 resolved all four. Where they disagree,
`design.md` wins; the contract beats `docs/`.

## Invariants behind every change

- **Version skew is permanent and asymmetric.** You deploy the proxy; tenants deploy sidecars whenever
  or never. The wire schema is the only irreversible artifact — sort work by *reversibility*, not cost.
  Contract changes are additive by default; breaking needs a version bump plus a capability flag.
- **Contract first.** Schema freeze → streaming spine → breadth (`design.md` — Migration Plan). The
  conformance suite — adversarial fixtures written *before* the code they gate — is the authority.
- **Three primitives, not twelve protocols.** No protocol-specific code for anything differing only by
  `Content-Type` and method token.
- **Refuse, never degrade.** A request a sidecar's declared capabilities cannot back is refused with a
  stated reason.
- **Tenant scoping is a key and a signature, not a habit.** Every projection tenant-keyed; every
  mutation takes the acting principal.
- **Vocabulary (D20):** *instance* = one proxy process; *installation* = all of them under one
  operator; *node* = an entry in the mount-point hierarchy.

## Banned patterns — review blockers, CI-checked (task 3.7)

- Headers as a map: `map[string]string`, `Map.new`, `Enum.into(…, %{})` over header fields.
  `Set-Cookie` is the canary (`docs/04-protocol-fidelity.md`, `docs/06-carry-forward.md`).
- Bodies as JSON strings, or any UTF-8 coercion of a body. One binary-safe body path serves both
  primitives; a second is a blocker.
- `io.ReadAll` on a proxied body, or any accumulation before emitting.
- Method allowlists or rewriting; relaying `Content-Length`/`Transfer-Encoding`; letting application
  middleware (parsers, method override, HEAD folding, `:accepts`, session, CSRF) touch proxied traffic.
- `inspect/1` on a wire payload — wire errors are typed codes.
- Any unbounded queue, buffer or accumulator: each needs a bound and an overflow behaviour.
- A test helper that repairs the state it waits on; a test that accommodates a defect instead of
  exposing it; a security property disabled in test config; uncertainty markers or bare `@tag :skip`.

## Conventions

- Every behavioural claim in prose carries a `file:line` citation or a test name; docs bump in the
  same PR, or the body says `docs: n/a` with a reason.
- Keep this file and `AGENTS.md` (unwritten) under 4 KB, pointed at `docs/` — task 1.3 checks it.
- graphify (once code exists): prefer `graphify query` to grep.

## Agent skills

Issues: local markdown in `.scratch/`; triage labels: defaults; domain: single-context.
See `docs/agents/`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
