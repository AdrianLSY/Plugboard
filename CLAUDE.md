# CLAUDE.md

A router. Everything below is one hop away; nothing here is the source of truth.

**Read [`docs/start-here.md`](docs/start-here.md) first, every time.** It carries the five governing
facts, the reading order, and a routing table for what to read per task.

## State

No product code. What exists is the plan: the vault under [`docs/`](docs/index.md) and
[`openspec/`](openspec/changes/rebuild-plugboard/tasks.md) — 717 tasks at 0 done. The prior art is
gitignored and **does not work**; cite it with a `file:line` or not at all, and see
[obtaining it](docs/history/obtaining-the-reference.md) before trying to check one.

## Commands

```bash
make check                                    # every vault gate; the one command CI runs
openspec list                                 # task progress
openspec validate rebuild-plugboard --strict  # gate for any openspec/ commit
```

Work tasks with `/opsx:apply`, revise the plan with `/opsx:update`; never hand-edit checkboxes while
a skill owns them.

## The invariants

- **Version skew is permanent and asymmetric.** You deploy the proxy; tenants deploy sidecars
  whenever or never. The wire schema is the only irreversible artifact — sort by *reversibility*, not
  cost. → [version skew](docs/why/version-skew.md)
- **Contract first.** Schema freeze → streaming spine → breadth. The conformance suite — adversarial
  fixtures written *before* the code they gate — is the authority.
- **Three primitives, not twelve protocols.** → [three primitives](docs/how/three-primitives.md)
- **Refuse, never degrade.** A request a sidecar's declared capabilities cannot back is refused with
  a stated reason.
- **Tenant scoping is a key and a signature, not a habit.** Every projection tenant-keyed; every
  mutation takes the acting principal.

Vocabulary is fixed: *instance* = one proxy process, *installation* = all of them, *node* = an entry
in the mount hierarchy. → [glossary](docs/glossary.md)

## Banned patterns

Eight of them, each its own note with the defect it prevents and its citation →
[banned patterns](docs/code/banned-patterns/). The canary is headers as a map: `map[string]string`,
`Map.new`, `Enum.into(…, %{})` over header fields, with `Set-Cookie` as the case that proves it.
Every rule in this repository, with whether a check actually enforces it →
[rule index](docs/rule-index.md).

## Authority

[Precedence is stated once](docs/method/authority-precedence.md): contract, then specifications, then
[decisions in force](docs/decisions/in-force.md), then vault notes, then generated indexes. A note
never states behaviour a specification owns. Where two disagree, the higher one is right.

## Before writing a note

[Conventions for authoring a note](docs/method/conventions.md) — fifteen of them, each with the gate
that enforces it. A first draft that violates one fails the build rather than a review.

## Before a PR, a test, or a doc bump

[reviewing](docs/code/reviewing.md) · [testing](docs/code/testing.md) ·
[documentation rules](docs/method/documentation-rules.md)
