---
type: rule
status: current
authority: rationale
---

# A committed binary states where it came from and on what terms

**Gate:** `ci/gates/binary_assets.py`

Every tracked binary appears in `ci/vault.json`'s `binary_assets` with an origin and the terms it is
carried under. A binary with no entry fails; an entry whose file is gone fails; an entry stating
neither origin nor terms fails.

The manifest is empty today, and that is the intended steady state rather than a gap. Adding a binary
is a deliberate edit to a tracked declaration — which is a place a reviewer looks, unlike a file that
simply appears in a diff as `Bin 0 -> 2429954 bytes`.

## Why

The prior attempt shipped 85 JPEGs whose origin was established nowhere: not their source, not their
terms, not who added them ([the audit](../../history/reference-audit.md)). Nothing in that repository
was *wrong* about them, because nothing in it said anything about them at all — which is the harder
version of the problem, since there is no claim to check.

It is not hypothetical here either. Two compiled Go commands, 2.4 MB each, reached a commit in this
repository before this check existed, left behind by `go build ./...` writing its output into a module
root. They were caught by reading a diffstat, which is not a mechanism.

## What it does not decide

Whether a stated origin is true, and whether the terms permit what this repository does with the file.
Both are review's. This gate decides that the question was answered somewhere a reader can find it.
