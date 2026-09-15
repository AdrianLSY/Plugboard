# Violating input: build-prerequisites

- **Gate:** `ci/gates/build_prerequisites.py` (`build-prerequisites`)
- **Rule note:** `docs/code/rules/generated-sources-are-generated-first.md`
- **Origin:** the CI failure that followed `rebuild-plugboard` task 3.13.

## What this gate is made of

Task 3.13 put a **generated** package — `internal/buildstamp` — into every Go
component's import graph. The make targets declared the dependency (`lint: stamp`,
`test-fast: stamp`). Two CI jobs reach the Go toolchain **without going through
make** — `govulncheck` in `security.yml`, the golangci-lint action in `test.yml` —
so the make graph's edge never reached them, and the security job failed on
`package plugboard/sidecar/internal/buildstamp is not in std`.

Neither encoding was wrong read alone. The make file was right. The workflow was
right about what it ran. What was missing was the relation **between** them.

## Violations

**`tree-make-missing-prereq` — the make graph loses the edge.** `stamp` still
exists and `lint` still declares it, so the two targets side by side look
consistent. `test-fast` type-checks the generated package without generating it.

**`tree-elixir-missing-prereq` — the same lost edge, in the other language.**
`lint` and `test-fast` declare `stamp`; `test-integration` does not, and
`mix compile --warnings-as-errors` over a missing `Plugboard.BuildStamp` is a failed build
rather than a warning. This tree exists because the **first version of this gate named only
the Go make files**, so this exact defect reached CI while the gate reported green — a gate
whose declared coverage omits half its subject reports green over that half.

**`tree-workflow-unstamped` — a job bypasses make and never generates.** The step
is `- run: echo "make stamp"`. That **is** a run body and it **does** contain the
command — the exact shape that defeated two earlier gates in this repository (a
scanner satisfied by its step's `name:`, then a parity check satisfied by
`echo "make check-gates"`). Command-position matching in `ci/gates/_workflow.py`
is what refuses it, and this tree is here to keep that refusal pinned.

**`tree-workflow-wrong-order` — the generator runs, too late.** Containment is
satisfied and the build still fails. This is the case that makes the gate read
*order* rather than *presence*.

**`tree-bypasses` — four ways past the first version, found by attacking it.** An underscore in
a target name (the rule regex demanded `[a-z][a-z0-9-]*`, so the recipe was never read); a literal
`go build` reached after `&&` (the markers were `$(GO) <verb>` literal strings); `go install`, a
verb that was not on the list; and a `.yaml` workflow whose job key carried a trailing comment —
two bypasses at once, since the file was globbed as `*.yml` only and the job regex demanded a bare
key ending the line.

Three of those four are **silent non-coverage**: the gate read nothing and reported green, which
is worse than reporting a problem. Toolchains are now declared as invocation + verb rather than as
literal strings, and both regexes were widened to what make and YAML actually accept.

## Why the make half is keyed on the operation, not the target name

The first draft keyed on `$(GO)` appearing anywhere in a recipe and flagged `fmt`.
Checked rather than argued about: with `internal/buildstamp` deleted,
`go fmt ./...` exits 0 while `go vet ./...` fails. `go fmt` does not type-check, so
it is not a compiling site. Keying on the **operation** says that; an exemption
list keyed on the name `fmt` would have said only that one target was forgiven.

## What this still cannot decide

Whether the generated source is correct — `ci/gates/provenance.py` holds where it
comes from and `ci/provenance-check.py` holds what it says. A toolchain reached
through a variable, a script or an alias: `run: $TOOL` runs something no regex can
name. A floor, not a proof.

## Expected

Exit 1 against each of the five trees: one violation each, except `tree-bypasses`, which emits four.
