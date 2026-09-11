---
type: rule
status: current
authority: rationale
---

# Every gate is demonstrated to fail

**Gate:** `ci/gates/meta.py`

Each gate holds a deliberately violating input and is proven to fail on it, and to fail *by its own logic* — with its violation recording neutered, a sound gate exits zero. A gate that passes on its own violating input fails the build.

## Why

The reason this exists rather than being trusted: the reference project's `mix precommit` ran `compile --warning-as-errors` -- singular, the wrong flag -- while CI ran the plural one, so the checker did not check and nobody noticed. A gate that is never proven to fail is indistinguishable from a gate that cannot fail.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.
Read [`ci/gates/meta.py`](../../../ci/gates/meta.py) for exactly what it decides — and, where it
matters, what it deliberately does not.
