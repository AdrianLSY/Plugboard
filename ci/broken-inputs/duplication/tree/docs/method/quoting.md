---
type: procedure
status: current
authority: rationale
---

# Quoting owned text

Owned by [the widget-mount specification](../../openspec/changes/add-widget-mount/specs/widget-mount/spec.md).

## Violation C -- the same paragraph indented into a blockquote

Wrapping a copy in quote markers does not make it one copy:

> A capability flag SHALL be additive, and a mount point whose sidecar declares a flag the proxy does not
> recognise SHALL be accepted with the unrecognised flag ignored, because a tenant deploys its sidecar on
> its own schedule and a flag newer than the proxy is version skew rather than an error to report.

## Not a violation F -- fenced code shared with the specification

The block below is byte-identical to one in the specification and is long enough to clear both floors,
and it still does not fire: fenced code is not requirement text.

```bash
# run the duplication gate against its own violating input, both ways
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree --report-only
python3 ci/gates/note_roots.py --root ci/broken-inputs/duplication/tree
python3 ci/gates/note_roots.py --root ci/broken-inputs/duplication/tree --report-only
```
