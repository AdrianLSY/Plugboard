# Violating input: provenance

- **Gate:** `ci/gates/provenance.py` (`provenance`)
- **Rule note:** `docs/code/rules/build-provenance-from-one-place.md`
- **Task:** `rebuild-plugboard` 3.13.

## Violations

One tree per direction, because a single tree carrying all three would let any one of them
pass unnoticed behind the others.

**`tree-second-derivation` — a component derives its own.** The sidecar shells out to
`git rev-parse --short HEAD`. It compiles, it runs, and it prints a plausible line. It also
asks git for the **short** hash where the one place asks for the full one, so this binary and
the other three now disagree about what "the commit" means — and each is internally consistent,
which is why nobody notices.

**`tree-one-place-gutted` — the one place stops deriving.** The fields are all still there, the
function is still called `values()`, every component still compiles and starts. They all report
`unknown`. **The first version of this gate could not detect this case at all**, because it only
ever looked for a *second* derivation; removing the first was invisible to it.

**`tree-uninvoked` — nothing generates the stamp.** A `go.mk` with no `stamp` target. On a clean
checkout the buildstamp package is simply absent or empty, and the binary's startup line is
indistinguishable from one built before stamping existed.

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
present, because they are violating trees either way.

What pins it is **the real tree**. Every subject file in this repository mentions git in prose — a
comment in `go.mk`, a `@doc` heredoc in `plugboard.ex`, a comment in each of the three Go mains — and
none of them runs it. Revert `strip_prose` to the identity and `make check` goes red with four false
positives on the working tree. The fix is load-bearing in the only place that can prove it.

## What this still cannot decide

Whether the reported values are **right**: `ci/provenance-check.py` runs all four components and
compares against a commit and a tree status it reads from git independently, so the assertion cannot be
built out of the value under test. Whether a released artifact carries the stamp — task 70.7. Whether a
configuration item collides with a provenance field — needs the schema task 5.2 builds.

## Expected

Exit 1 against each tree, one violation each.
