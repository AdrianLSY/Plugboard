# AGENTS.md

A router for coding agents. Same content as [`CLAUDE.md`](CLAUDE.md) reaches; this file exists so an
agent that looks for `AGENTS.md` finds a door rather than nothing.

**Start at [`docs/start-here.md`](docs/start-here.md).** It has a routing table keyed by what you are
doing. Do not read the whole vault; read the row that matches your task.

## What will fail your work if you skip it

- **[The rule index](docs/rule-index.md)** — every rule, with whether a check enforces it today.
  A rule marked *preference* may never be raised as a blocking objection against you, and you may not
  raise one either.
- **[Banned patterns](docs/code/banned-patterns/)** — eight prohibited constructs, each with the
  defect it prevents. Headers as a map is the canary.
- **`make check`** — the aggregating target. It enumerates every gate it ran and the roots each
  covered, so a green run states its own coverage rather than implying total coverage.

## The invariants you cannot design around

**Version skew is permanent and asymmetric** — the wire schema is the only irreversible artifact, so
sort work by reversibility rather than by cost ([why](docs/why/version-skew.md)).
**Refuse, never degrade** — a request a sidecar cannot back is refused with a stated reason, never
served at reduced fidelity. **Tenant scoping** is a key and a signature, not a habit.

## Two rules about what you write

1. **A note never states behaviour a specification owns.** Link the owning specification instead.
   Normative modals in the spine are refused by a gate, so if you find yourself writing "MUST", you
   are restating a spec ([precedence](docs/method/authority-precedence.md)).
2. **Every claim carries a citation, or an explicit `Unverified` marker.** A confident unsourced
   sentence is the defect this whole vault exists to prevent — the prior art carried 148 KB of prose
   with two verifiably false documented claims ([documentation rules](docs/method/documentation-rules.md)).

## Before you write a note

[The conventions](docs/method/conventions.md) — generated from the same enumeration the gates key on,
so the list you read and the list that fails you cannot diverge.

## Procedures

[Adding a feature](docs/code/adding-a-feature.md) · [fixing a bug](docs/code/fixing-a-bug.md) ·
[reviewing](docs/code/reviewing.md) · [testing](docs/code/testing.md)

Work tasks with `/opsx:apply`; revise the plan with `/opsx:update`. Never hand-edit a task checkbox.
