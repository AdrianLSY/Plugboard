---
type: rule
status: current
authority: rationale
---

# A component's boundary is stated once

**Gate:** `ci/gates/component_boundaries.py`

For every component that exists, one note states what it owns and what it must not own. Every other
place that names the boundary links to that note rather than restating it — a component's own README
included. The set is keyed on the components that exist, so adding a component directory without its
boundary note fails, and a boundary note outliving its component fails too.

## Why

A README is where the second copy of a boundary always appears, and two statements of one boundary
diverge quietly: the note gets updated, the README does not, and a contributor reads whichever they
found first. The prior art shows the endpoint of that process — `MountStore` and `HookStore` were the
same GenServer twice, with 128 of `hook_store.ex`'s 199 non-comment lines appearing verbatim in
`mount_store.ex`, and domain affinities were then bolted *inside* `MountStore` because there was no
third slot ([reference audit](../../history/reference-audit.md)).

The check passes vacuously today: no component directory exists yet. What it buys is that the moment
one appears without its boundary, the build fails — rather than the check being written later,
alongside five components and no boundaries.
