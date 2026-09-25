# Violating input: provenance

- **Gate:** `ci/gates/provenance.py` (`provenance`)
- **Rule note:** `docs/code/rules/build-provenance-from-one-place.md`
- **Task:** `rebuild-plugboard` 3.13.

## Violations

One tree per direction, because a single tree carrying all three would let any one of them
pass unnoticed behind the others.

**`tree-second-derivation` — a component derives its own.** The sidecar shells out to git. It
compiles, it runs, and it prints a plausible line. It is also asking a *different question* than
the one place asks, so this binary and the other three disagree about what "the commit" means —
and each is internally consistent, which is why nobody notices.

The gate's marker is `git` itself, in executable text, rather than any particular command
spelling or execution primitive. A wider marker — `exec.Command`, `os/exec`, `System.cmd` — was
tried and flagged four conformance files, rightly on its own terms and wrongly in fact: the
conformance harness starts processes for a living. A component naming **git** has no second
reading.

**`tree-one-place-gutted` — the one place stops deriving.** The fields are all still there, the
function is still called `values()`, every component still compiles and starts. They all report
`unknown`. **The first version of this gate could not detect this case at all**, because it only
ever looked for a *second* derivation; removing the first was invisible to it.

**`tree-uninvoked` — nothing generates the stamp.** A `go.mk` with no `stamp` target. On a clean
checkout the buildstamp package is simply absent or empty, and the binary's startup line is
indistinguishable from one built before stamping existed.

**`tree-hidden-derivations` — three ways to hide a real derivation from a regex.** All three were
found by a reviewer attacking this gate, and all three passed before the fix:

- A `//` **inside a Go string literal**. A regex deleting from `//` to end of line deletes the rest
  of that line — and with it the `exec.Command("git", ...)` on the next. The file compiles and vets
  clean.
- A `//go:generate` directive. It is a comment to the compiler and an **instruction to
  `go generate`, which runs it**. Comment-stripping deletes it by construction, so the one kind of
  comment that executes was the one kind guaranteed to be invisible.
- `#{` in Elixir, which begins an **interpolation**, not a comment. A regex deleting from `#` ate a
  `System.cmd("git", ...)` that mix really compiles and really runs.

The repair is a scanner that knows whether it is inside a string, and that keeps `//go:` directives
as executable text. Stripping is still necessary — seven files in the real tree mention git in prose
— but it now has to be done properly rather than with a substitution.

**`tree-shell-indirection` — the derivation moved one file sideways.** `ci/make/go.mk` names no
git; the derivation lives in `ci/derive-provenance.sh`, which the make file invokes:

```make
PROV := $(shell sh $(REPO_ROOT)/ci/derive-provenance.sh)
```

A check that reads only the build files finds nothing. A check that reads only component sources
finds nothing either — the script is under no component root. The derivation runs at make **parse**
time, on every invocation of every target, and asks for the short hash where the one place asks for
the full one.

The roster now follows the invocation: a script a build file hands to an interpreter is a subject.
Sweeping in every tracked `*.sh` would also have caught it, and would have caught scripts no build
runs; following the invocation catches exactly the set that can derive anything.

## The one place is read as code, not as text

Direction 2 asked whether `ci/stamp.py` still contained `subprocess` and `git`. That file's own
**docstring** contains both words while running neither, so the check could not fail: a reviewer
deleted the entire derivation and watched the gate stay green.

It is now parsed with `ast` — standard library, so the gate keeps its no-dependency rule — and asks
whether a call actually passes `git` as a command argument and whether `subprocess` is actually used.

## The case that matters most, and why it is here

The first attempt at this gate matched `git rev-parse`, `git describe` and `git status --porcelain`
as plain substrings. `ci/stamp.py` calls `_git("rev-parse", "HEAD")` — the declared strings never
appear — so the gate passed over the one file it most needed to hold. Patching its matching back to
the condemned form left **every fixture still green**, which is the tell: nothing was pinned to the
repair.

This version is keyed on **execution** instead. A second derivation has to run a subprocess; there is
no other route from Go, Elixir or make to git, and `exec.Command` / `System.cmd` / `os/exec` do not get
respelled the way a command string does.

## What pins the repair, and what does not

Honestly: **the three trees here do not pin it.** They fail whether or not the comment-stripping fix is
present, because they are violating trees either way. Nor do they pin the roster being *discovered*
rather than listed — that repair was forced by a reviewer planting `sidecar/cmd/probe/main.go`, a new
Go main deriving its own commit, which the listed version passed over because the list did not name
the new file. A discovered roster has no such blind spot, and the count it prints moves when the tree
does.

What pins it is **the real tree**. Every subject file in this repository mentions git in prose — a
comment in `go.mk`, a `@doc` heredoc in `plugboard.ex`, a comment in each of the three Go mains — and
none of them runs it. Revert `strip_prose` to the identity and `make check` goes red with four false
positives on the working tree. The fix is load-bearing in the only place that can prove it.

## What this still cannot decide

Whether the reported values are **right**: `ci/provenance-check.py` runs all four components and
compares against a commit and a tree status it reads from git independently, so the assertion cannot be
built out of the value under test. Whether a released artifact carries the stamp — task 70.7. Whether a
configuration item collides with a provenance field — task 5.3's, against the schema task 5.1
validates.

## Expected

Exit 1 against each tree, one violation each.
