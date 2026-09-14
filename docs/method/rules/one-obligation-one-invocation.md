---
type: rule
status: current
authority: rationale
---

# An obligation enforced in two places is enforced the same way in both

**Gate:** `ci/gates/parity.py`

Where one obligation has two **independently written** invocations, both pass the same flags. Where it
has one invocation reached from two places, there is nothing to compare and the declaration says so
rather than the gate skipping it quietly.

The standing checks — the meta-check and this one — also run on a declared interval, not only on
change.

## Why

The prior art ran `mix compile --warning-as-errors` in its local hook. Singular. The flag the compiler
actually takes is `--warnings-as-errors`, so the local guardrail checked **nothing** for months while
CI checked everything, and the two agreed often enough that nobody looked
([reference audit](../../history/reference-audit.md)).

A second encoding does not announce its drift. It simply stops being the same check, and the place it
stops is the place a contributor runs before pushing — the one that is supposed to catch the problem
early and cheaply.

## Why the interval

A gate can be broken by a change **elsewhere**: a dependency moves, a tool changes its output, a
hosting action ships a new major. None of those is a commit here, so a check bound only to change finds
that class whenever somebody next happens to push.

## What it cannot decide

Whether the flags are the right ones, or whether a tool behaves the same across versions. And a command
reached through a variable, a script file or an alias: `run: $SCANNER` runs something no regex can
name. The check is a floor.
