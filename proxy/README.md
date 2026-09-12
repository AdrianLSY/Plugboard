---
type: guide
status: current
authority: rationale
---

# proxy

The Elixir application the operator runs: routing, the sidecar registry, tenant-scoped state, and the
tunnel endpoint a sidecar dials.

**Boundary:** stated once, in [docs/code/boundaries/proxy.md](../docs/code/boundaries/proxy.md).
This file routes; it does not restate.

**Skeleton only.** The mix project compiles with `--warnings-as-errors` and carries the five quality
tools the prior art declared and never invoked. There is no Phoenix endpoint and no middleware, per
[D5](../docs/decisions/d05-pipeline-before-middleware.md): proxied traffic terminates before any of
it, and a default stack something is later carved out of is how that gets lost.
