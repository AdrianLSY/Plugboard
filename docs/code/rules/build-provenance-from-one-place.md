---
type: rule
status: current
authority: rationale
---

# Every component is stamped from one place, and reports what it was stamped with

**Gate:** `ci/gates/provenance.py`

Four facts about a build — version, commit, dirty-tree marker, build time — and the component they
belong to are computed by one recipe, `ci/make/go.mk`'s `stamp` target (`ci/make/go.mk:100`), emitted
into one generated source per component, and reported by that component at startup. They are reported
under five names: `component`, `version`, `commit`, `tree`, `built_at`. `ci/make/elixir.mk` delegates
to that target rather than carrying a second copy (`ci/make/elixir.mk:71`).

Nothing else may ask version control what a build is. A `git rev-parse` in a component's own build
file or source fails the gate, and so does one in a second build fragment.

## Why one place rather than one per component

Two copies of the discovery is how one component comes to report a dirty tree while another reports
nothing, and neither side can see the drift from where it stands. The repository has already watched
that happen with a different subject: the prior art carried a linter configuration per repository,
and the sidecar ended with thirty linters while the component terminating untrusted traffic had no
format check, no Dialyzer and no dependency audit at all
([the audit](../../history/reference-audit.md)). Nobody decided that. It is what two copies become.

The same argument makes the delegation in `ci/make/elixir.mk` worth its one recursive `make`: the
copy arrives when a second language needs a stamp and delegating looks like a detour.

## Why it is stamped at build time, and never committed

A stamp carries a build time and a commit, so its content differs on every run. That rules out a tool
under `ci/gen/`, where every generator is held against a pinned expected output
(`ci/gates/generators.py:1`) — an expectation this one could never satisfy. It also rules out
committing the generated source: a tracked stamp makes the tree dirty the moment it is regenerated,
so its own `tree` marker stops being true about the tree it describes. The generated source is
ignored beside its component, and a component that was never stamped does not compile — a binary that
cannot say what it was built from is not one this repository ships.

## Why the startup report needs a test, per component

An emission nothing reads is not instrumentation. The prior art emitted 75 telemetry events and
attached zero handlers ([the audit](../../history/reference-audit.md)), and the gate can only decide
that a test *names* the reporter — never that it asserts anything. What carries that weight is the
test itself, one per component: it calls the startup reporter and compares what comes back to the
five stamped values, looked up by name and spelled out in the order they are reported
(`sidecar/cmd/telephone/build_stamp_test.go:11`). A reporter that quietly drops the dirty-tree marker
fails it, naming both strings.

Each of those tests is deliberately small. The three Go components are three modules, so they share
no helper without one importing another — which [the boundaries](../boundaries/index.md) forbid for
better reasons than this. So the value shapes are bound once, in the sidecar's second test, and each
component binds only that it reports what it was stamped with.

## The one case that is executed rather than read

Two builds of one revision that differ by one modified file must produce different `tree` markers.
No reading of a recipe decides that, and a marker that never moves is indistinguishable from an
honest one in every artifact it appears in — so the gate runs the mechanism twice over a throwaway
repository and compares (`ci/gates/provenance.py:177`). The demonstration is a stamp whose marker is
the constant `clean` (`ci/broken-inputs/provenance/tree2/ci/make/go.mk:1`).

## What this rule does not cover

**A configuration item that restates a provenance field.** Task 3.13 asks for a check refusing one,
and it is not written: no component has a configuration schema yet, and a check with no subject
reports the same green as one that examined four. It belongs beside the schemas
([tasks 5.1 and 5.2](../../../openspec/changes/rebuild-plugboard/tasks.md)), and the vocabulary it
must refuse is the five fields above.

**Reading provenance out of a stopped artifact**, which
[task 70.7](../../../openspec/changes/rebuild-plugboard/tasks.md) owns. What is decided here is what
a running component reports and what a build recipe computes.

**Whether a reported value is true.** That the commit is the commit and the build time is the build
time: nothing in the tree decides either, and no gate here claims to.
