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
commit it is and whether the tree it was built from was clean. The Go mains print it first; the proxy
prints it from its application callback, `Plugboard.Application.start/2`, before its supervision tree
starts.

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

## Why the check reads code rather than text

Three of this gate's own defects were the same mistake in different clothes: a regex asked a text
question about a language question. `//` inside a string is not a comment; `#{` in Elixir is an
interpolation; `//go:generate` is a comment the build *executes*; and a Python docstring naming
`subprocess` and `git` satisfied a substring test over a file that had stopped calling either.

Where the question is "does this run", the answer comes from a scanner that tracks string state, or
from `ast`. A substring is evidence of nothing.

## Why the subject set follows invocations

A roster that lists its subjects stops growing silently. A roster that discovers them under the
component roots stops at the roots: a derivation in a shell script that a make file invokes is under
none of them, and the build file naming the script names no git itself. Both halves read clean while
the derivation runs on every make invocation.

So the set is component sources, the build files, **and whatever those build files hand to an
interpreter**.

## What it cannot decide

Whether the values are right. That needs each component started and the line it prints compared, field
by field, with two things: its generated stamp, read from the source `ci/stamp.py` wrote, and git, read
independently. Each comparison passes over what the other catches. A component reporting something
other than its stamp — a build time from its own clock — agrees with git about everything git knows; a
blank or stale stamp reported faithfully agrees with itself. That is `ci/provenance-check.py`'s job, and
it runs in CI.

It observes startup rather than calling the function that formats the line. An earlier version ran the
proxy with its application suppressed and called `Plugboard.provenance_line/0` itself, and passed while
the proxy had no startup path that printed anything.

Note that its dirty-marker probe reports **inconclusive** rather than a pass when the tree it runs on is
already dirty; a check that cannot tell those apart is one that claims a pass it did not earn.

Whether a released artifact carries a stamp at all — that is task 70.7's, and is not this gate's.
