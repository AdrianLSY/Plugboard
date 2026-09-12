---
type: guide
status: current
authority: rationale
---

# terminator

The Go edge component that terminates HTTP/2 from clients in v1, and HTTP/3 with WebTransport later.
A contract speaker, replaceable on its own.

**Boundary:** stated once, in [docs/code/boundaries/terminator.md](../docs/code/boundaries/terminator.md).
This file routes; it does not restate.

**Skeleton only.** The Go module and its command are in place, sharing exactly one linter
configuration with the sidecar. What is not here is any termination code: HTTP/2 from clients
arrives at [task 54.4](../openspec/changes/rebuild-plugboard/tasks.md), and it speaks the contract
rather than reimplementing the proxy.
