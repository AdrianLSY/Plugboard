---
type: rule
status: current
authority: rationale
---

# An entry file routes, stays small, and names nothing absent

**Gate:** `ci/gates/entry_points.py`

An entry file links into the vault, names at least one invariant and at least one banned pattern,
stays under the declared size ceiling, and never instructs a reader to use a generated index, tool or
directory the repository does not contain. It does not restate framework or language conventions.

## Why

The third clause is not hypothetical. Before this gate existed, `CLAUDE.md` told every agent to
prefer `graphify query` over grep, described a knowledge graph with god nodes and community
structure, and pointed at a generated wiki index — none of which has ever existed in this
repository. That was roughly a kilobyte of the most-read file describing an absent artifact, in a
file whose own plan capped it at 4 KB while it sat at 4,865 bytes.

An entry file is the one place a false claim is guaranteed to be read first, and the one place a
reader has no context yet to doubt it.

The prior art's `AGENTS.md` was 24 KB, mostly restating framework conventions the model already knew
and almost nothing about the system's own invariants ([harness](../harness.md)). Inverting that ratio
is the point of the ceiling.
