---
type: concept
status: current
authority: rationale
---

# Widget mount

Owned by [the widget-mount specification](../../openspec/changes/add-widget-mount/specs/widget-mount/spec.md).

## Violation A -- a requirement paragraph copied verbatim

A mount point SHALL be refused
when the declared capabilities of the sidecar backing it cannot satisfy the request, and the refusal
SHALL state the capability that was missing rather than degrading the response to one the sidecar is
able to serve, because a degraded answer is indistinguishable from a correct one at the caller.

## Not a violation D -- a short shared sentence

The gate fails and names both locations.
