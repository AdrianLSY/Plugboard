---
type: rule
status: current
authority: rationale
---

# Build provenance is derived in one place, and read everywhere else

**Gate:** `ci/gates/provenance.py`

Four values — version, commit, dirty-tree marker, build time — are derived by `ci/stamp.py` and by
nothing else. Each component reads a generated stamp. No component asks git anything.

Every component reports the line at startup, so an operator holding a running process can say which
commit it is and whether the tree it was built from was clean.

## Why

A second derivation does not announce itself. It is a reasonable-looking four lines in one component's
`main`, it compiles, and it prints something plausible. It drifts only when the two sides ask git
slightly different questions — `--short HEAD` against `HEAD`, `describe --dirty` against
`status --porcelain` — and then each component is internally consistent while the installation as a
whole no longer agrees on what commit it is running.

This matters here more than it would elsewhere. [Version skew is permanent and
asymmetric](../../why/version-skew.md): you deploy the proxy, tenants deploy sidecars whenever or
never, and the first question about any misbehaving pair is *which builds are these two*. An answer
assembled from two disagreeing derivations is worse than no answer, because it is believed.

## Why the dirty marker is read from the working tree

`git describe --dirty` appends its suffix only when a tag exists to describe. On a repository with no
tags it reports a bare hash and says nothing about the tree, so a build from modified sources is
indistinguishable from a clean one. The marker is therefore derived from `git status --porcelain`,
separately, and it is two words rather than a boolean — a boolean read out of a log line is a coin
flip about which way round the author meant it.

## What it cannot decide

Whether the values are right. That needs the components run and their output compared against git read
independently, which is `ci/provenance-check.py`'s job and runs in CI. Note that its dirty-marker probe
reports **inconclusive** rather than a pass when the tree it runs on is already dirty; a check that
cannot tell those apart is one that claims a pass it did not earn.

Whether a released artifact carries a stamp at all — that is task 70.7's, and is not this gate's.
