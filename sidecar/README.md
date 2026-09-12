---
type: guide
status: current
authority: rationale
---

# sidecar

The Go program a tenant runs beside their own backend. It dials out, so no inbound path into the
tenant's network is required.

**Boundary:** stated once, in [docs/code/boundaries/sidecar.md](../docs/code/boundaries/sidecar.md).
This file routes; it does not restate.

**Skeleton only.** The Go module, its command under `cmd/telephone/`, and the shared linter
configuration are in place. What is not here is any contract code: the schema is frozen first
([section 17](../openspec/changes/rebuild-plugboard/tasks.md)), because a hand-written codec landing
ahead of it is the two-independent-fictions failure the conformance suite exists to remove.
