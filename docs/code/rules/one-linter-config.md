---
type: rule
status: current
authority: rationale
---

# One linter configuration, one copy, for every Go module

**Gate:** `ci/gates/linter_config.py`

Every Go module in this repository is linted by the same configuration file, there is exactly one
copy of it, and every module's build file reaches it — through
[the shared include](../../../ci/make/go.mk) or by naming the path. A second copy fails, an absent one
fails while any module exists, and a module pointing at neither fails.

## Why

The prior art was two repositories. The sidecar carried thirty linters; the component terminating
untrusted traffic — the one handling bytes from the public internet — had no format check, no static
analysis pass and no dependency audit at all ([reference audit](../../history/reference-audit.md),
`docs/history/reference-audit.md:253`). Nobody decided that. It is what two configurations become,
because each drifts toward whatever its own module found inconvenient, and neither drift is visible
from the other side.

The third case is the one that looks redundant and is not. A single file at the root proves nothing if
a module never points at it: that is a copy with extra steps, and it is the state a check counting
files would pass over.

## What it does not reach

Whether the configuration is any good, and whether the linter is installed. The first is review's. The
second fails loudly at `make lint` rather than silently — a lint target that skips when its tool is
absent reports green over an unlinted module, which is the same defect in a third costume.
