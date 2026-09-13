# Violating input: provenance

- **Gate:** `ci/gates/provenance.py` (`provenance`)
- **Rule note:** `docs/code/rules/build-provenance-from-one-place.md`
- **Task:** `rebuild-plugboard` task 3.13 — three trees, because one of the cases cannot be read out
  of a tree at all.

## `tree/` — the component-side cases, with a negative control

`sidecar/` violates three at once, and they are the three that describe one component honestly:

1. `sidecar/Makefile` carries a `version` target running `git -C '$(REPO_ROOT)' rev-parse --short
   HEAD`. That is a **second copy of the discovery**: this component's idea of what the build is and
   the stamp's can now differ, and neither side can see the other from where it stands.

   The spelling is load-bearing and is the reason this line is not the bare `git rev-parse` a first
   draft reaches for. A copy of the discovery is not freshly invented when it arrives — it is pasted
   from `ci/make/go.mk:102`, which writes `git -C '$(STAMP_SRC)' rev-parse HEAD`, because whoever
   added it wanted the behaviour that file already has. A check testing for the substring
   `git rev-parse` matches neither line, so it would have caught only the copy nobody would write
   while passing over every copy of the real thing. The gate matches git's own option syntax between
   `git` and its subcommand, and this fixture is what holds it to that on the hard case.
2. `sidecar/cmd/telephone/main.go` prints its banner and nothing else. The stamp is generated beside
   it and **reaches no output** — the prior art's shape exactly, where 75 telemetry events were
   emitted and no handler was ever attached.
3. Nothing under `sidecar/` names `startupReport`. `main_test.go` is present and passes; it reads the
   banner. **The reported build is asserted by no test**, which is how a startup line drifts from the
   stamp at the first refactor while every suite stays green.

`proxy/` sits beside it as the negative control and is reported for nothing: an Elixir component
whose `application.ex` calls `report_provenance` and whose test names it. A check that reported every
component in a tree containing one bad one would emit five failures here. `expect.json` says three.

## `tree2/` — a stamp that lies, and the one case that is executed rather than read

`ci/make/go.mk` here emits all five fields, a real commit, a real version and a build time. Its tree
marker is the constant `clean`. Nothing in the emitted source says so, and nothing in the recipe reads
as wrong — finding it takes **running the mechanism twice over one revision**, once clean and once
with a single file modified, which is what the gate does. The two markers come back equal and the gate
fails.

This is the check task 3.13 asks for in its own words, and it is the reason that case is not a grep.

Every other field is emitted honestly and in its promised shape, and that is deliberate. The gate also
holds whatever it finds at this path to the stamp's value contract by running it, so a miniature that
emitted a blank `version` would fail this tree twice and the count in `expect.json` would stop saying
which case did the work. One tree, one defect.

## `tree3/` — no one place, and a second one

`ci/make/go.mk` declares no `stamp` target: every component it serves is built with no provenance and
each of them looks exactly as it did before. `ci/make/elixir.mk` declares none either, and carries a
`release` target holding a **verbatim paste of the one place's discovery** — the same three reads,
the same `-C '$(STAMP_SRC)'`, the same `--no-optional-locks`. That is the second copy one level up
from a component, which is where it actually arrives: a second language needs a stamp, delegating
looks like a detour, and the recipe that already works gets copied.

All three reads are in one `release` recipe and the gate reports them as **one** violation naming all
three markers, not three — the defect is the copy, and a fragment that pasted the discovery once is
not three times as wrong as one that pasted a third of it.

## The case that is not here, and why

A **tracked** generated stamp — committing one makes the tree dirty the moment it is regenerated, so
the marker it carries stops being true. That case is scoped to the repository by `on_tracked_tree`,
the guard `binary_assets`, `component_boundaries`, `index_drift` and `out_of_scope` each arrived at
separately: a violating input is untracked by construction, so the check would report nothing here
either way.

## What the gate does not decide, stated here as well

Whether a configuration item collides with a provenance field. Task 3.13 asks for that check and it
is not written: no component has a configuration schema yet (tasks 5.1 and 5.2 build them), and a
check with no subject reports the same green as one that examined four.

## Expected

`tree`: exit 1, three violations. `tree2`: exit 1, one violation. `tree3`: exit 1, three violations.
