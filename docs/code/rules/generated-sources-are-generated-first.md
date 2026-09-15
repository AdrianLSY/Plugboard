---
type: rule
status: current
authority: rationale
---

# A generated source is generated before anything compiles it

**Gate:** `ci/gates/build_prerequisites.py`

Every make target that type-checks Go lists the generating target among its
prerequisites. Every CI job that reaches the toolchain around make runs the generator
first — first in order, not merely somewhere in the job.

## Why

A generated file in an import graph is a dependency the build system knows about and a
checkout does not. The make graph can state it perfectly and still not reach a step that
never consults the make graph.

That is what happened here. [Build provenance](build-provenance-from-one-place.md) put
`internal/buildstamp` into every Go component's imports; `lint: stamp` and
`test-fast: stamp` declared the edge; `govulncheck` and the golangci-lint action call the
toolchain directly, and the security job failed on
`package plugboard/sidecar/internal/buildstamp is not in std`.

Read alone, neither side was wrong. This is the same shape as
[an obligation enforced in two places](../../method/rules/one-obligation-one-invocation.md):
the defect lives in the relation between two encodings, where no single file shows it.

## Why order and not presence

A step that regenerates a source *after* the step that compiled it contains the command,
and the build still fails. A containment check passes on that arrangement, which makes
containment the wrong question.

## What it cannot decide

Whether the generated source is right — that is
[provenance's](build-provenance-from-one-place.md) rule and `ci/provenance-check.py`'s
job. And a toolchain reached through a variable, a script file or an alias: `run: $TOOL`
runs something no regex can name. The check is a floor.
