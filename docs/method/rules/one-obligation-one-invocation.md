---
type: rule
status: current
authority: rationale
---

# An obligation enforced in two places is enforced by one invocation

**Gate:** `ci/gates/parity.py`

An obligation this repository refuses on is invoked from two places — a make target a contributor
reaches through `make precommit`, and a step in a tracked workflow. Where both exist, they are the
same invocation, and where a broken input exists, both reject it. The two invocations are declared
in `ci/vault.json`'s `parity` section by their *sites*, never by their flags: the flags are read out
of the makefiles and the workflows, because a declaration holding a copy of them is a third encoding
and the third encoding is the one that goes stale.

The check is two programs, and neither is sufficient alone.

```
  ci/gates/parity.py     reads both argvs out of the tree, normalises them, and
                         refuses when they differ. Runs inside `make check`, so
                         a flag that drifts on ONE side fails the change that
                         drifted it.

  ci/parity.py           runs both invocations against a tracked broken input
                         and requires both to reject it. Runs on the recurring
                         interval, so a flag that is wrong on BOTH sides -- which
                         is not a difference, and which no comparison of text can
                         see -- is found without a change to anything.
```

A flag both sides spell identically, which the tool accepts and does not act on, passes the first and
fails the second. A flag that drifted on one side fails the first and can pass the second, because an
exit status does not say *why* a tool refused. Each covers the other's blind spot.

## Why

The prior art's local guardrail ran `compile --warning-as-errors` — singular, a switch `mix` accepts
and ignores — while CI ran `mix compile --warnings-as-errors`, the correct spelling, for months
([reference audit](../../history/reference-audit.md), `docs/history/reference-audit.md:257`). Both
invocations existed. Both were green. The only observable difference was that the local one was fast.

Nothing about that state is visible from either side. From the local side the hook runs and passes.
From the CI side the job runs and passes. It is visible only from a position that can see both, and
until this check there was no such position — which is why the defect survived months rather than a
review.

The same repository ran `credo` as a declared dependency that nothing invoked, and a linter set that
had drifted to thirty rules on one component and none on the one terminating untrusted traffic
([reference audit](../../history/reference-audit.md), `docs/history/reference-audit.md:251`). Those
are the same failure at a different scale: an enforcement whose two encodings nobody compared.

## What this rule does not claim

It does not claim an obligation ought to be enforced in both places. Its subject is the pairs, and an
obligation enforced locally and nowhere in CI is a different question that no check here answers.

It does not claim the two invocations are *correct*, only that they are *one*. Two identical
invocations of a tool that decides nothing are in parity, and the executing half is what distinguishes
that case — over one broken input per obligation, which is a floor rather than a proof.

Most obligations here reach CI *through* the same make recipe, which is the arrangement that makes
divergence impossible by construction; the gate verifies that the workflow step still reaches that
recipe rather than assuming it. One obligation has two genuinely independent encodings — the Go
linter, invoked by a caching action in CI and by `ci/make/go.mk` locally — and it is the one this
rule would have caught without running anything.

## The interval as well as the change

A gate is a program with dependencies it does not own, so it can break on a day nobody touched this
repository. Both checks therefore run on a declared recurring interval as well as on change
(`.github/workflows/scheduled.yml`, and the interval is declared in `ci/vault.json` so a dropped one
is a gate failure). What no tracked artifact can state is whether the hosting service fired the
schedule — that is server-side and unreadable here, the same boundary
[the gates actually run](the-gates-actually-run.md) draws for branch protection. What the interval
gives instead is an outcome a person receives without a commit: a run summary written on every run,
passing included, and an issue opened on a failing scheduled run.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
