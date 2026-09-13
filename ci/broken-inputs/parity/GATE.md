# Violating input: parity

- **Gate:** `ci/gates/parity.py` (`parity`)
- **Rule note:** `docs/method/rules/one-obligation-one-invocation.md`
- **Executing half:** `ci/parity.py`, which runs both invocations of each obligation against the
  inputs under `inputs/` below. It is not a vault gate — it needs the real toolchains and is carried
  by the recurring runner, `.github/workflows/scheduled.yml`.
- **Tasks:** `rebuild-plugboard` 3.11 and 3.12.

Both trees mirror the paths `ci/vault.json`'s `parity` section declares — `Makefile`,
`proxy/Makefile`, `sidecar/Makefile`, `.github/workflows/*.yml` — because the gate reads its argvs
out of the tree rather than out of the declaration. Each component Makefile includes a shared
fragment, as the real ones do, so include-following and make-variable expansion are exercised here
and not only against the repository.

The fragments are named `ci/make/proxy-recipes.mk` and `ci/make/go-recipes.mk` rather than
`elixir.mk` and `go.mk`. Nothing in this gate's declaration names them — it names component
Makefiles — and `ci/gates/provenance.py` keys on those two exact paths, so a fixture carrying them
would fail a second gate for a property that is not this one's subject. `ci/gates/meta.py` refuses
that, and rightly: a violating input tripping a second gate makes both demonstrations ambiguous.

## `tree/` — the obligations exist and disagree. Five violations.

1. `ci/make/proxy-recipes.mk` has dropped `mix format --check-formatted` from `lint`, so the
   `elixir-format` obligation is declared enforced locally and is not. `make precommit` is green
   over a property nothing checked.
2. `ci/make/go-recipes.mk` runs `golangci-lint run ./...` with no `--config`, while the workflow's action
   step passes one. Two invocations of one obligation, and they are two different invocations —
   the shape `--warning-as-errors` had, caught without running anything.
3. `.github/workflows/test.yml` carries `- run: mix format --check-formatted` directly. It is a
   second encoding of a checking tool, compared to nothing, and no obligation claims it. This is
   the case that stops `parity.obligations` from being a roster that quietly goes stale.
4. `.github/workflows/scheduled.yml` invokes `make check-gates` behind `if: github.event_name ==
   'push'`, so the run on the interval — the run the file exists for — reaches it never.
5. The same workflow names `python3 ci/parity.py` three times and runs it nowhere — as a step's own
   `name:`, as an `echo` argument in the run-summary step, and as a line of a here-document body —
   so half the recurring runner the declaration describes does not exist.

Cases 4 and 5 are why this workflow carries a summary step and a heredoc at all. The clause was once
a substring test over the uncommented file body, and the real `.github/workflows/scheduled.yml`
prints both declared command names in its summary — `echo "| \`make check-gates\` | …"`. Deleting
both real invocation steps from the repository's own workflow left the gate reporting `no
violations`. The fixture at the time passed only because its minimal workflow had no summary step,
so it demonstrated the case in a shape the governed artifact could not reach.

The gate now matches each declared command against the argv a `run:` step actually executes, and
this tree carries every shape that is a name and not an invocation. The last one is the one a
line-oriented reader gets wrong twice: a `run: |` block was scanned line by line, so each line of a
here-document body — data the shell hands to `cat`, executed by nothing — was yielded as its own
command. With the heredoc handling removed from `ci/gates/parity.py`, this tree emits **three**
violations rather than five: the heredoc's two lines supply both declared commands, unconditionally,
and both scheduled-runner cases go quiet. That is the measurement the fixture exists to hold.

## `tree2/` — every local invocation is correct and the CI half is gone. Five violations.

The makefiles here are right. `.github/workflows/test.yml` reaches none of the declared recipes —
no step reaches `Makefile:test-fast` or `proxy/Makefile:lint`, and no action runs the Go linter —
so four obligations report that half of a dual-invocation obligation is missing. There is no
`.github/workflows/scheduled.yml` at all, which is the fifth.

Each obligation still has one enforcement, which is the state that reads as protection from either
side alone. That is the point: the tree looks fine from the local side and fine from the CI side,
and is wrong.

## The sixth case is repository-scoped, and why

`ci/gates/parity.py` also refuses when a declared obligation's broken input under `inputs/` is
gone. That case is guarded by `on_tracked_tree` for the reason `ci/gates/binary_assets.py` states:
a violating input is deliberately partial and its file set has nothing to do with this manifest's,
so applying the check to one produces a failure that is not a defect. It is not demonstrated by a
tree here. It was observed firing: before `inputs/` was written, the gate reported all three
declared inputs absent, one failure each, against the real tree.

## What the trees cannot demonstrate, and what does instead

Neither tree can show an INERT flag — one both sides spell identically, which the tool accepts and
does not act on. It is identical on both sides, so a text comparison passes. `ci/parity.py` is what
sees it, by running both invocations against `inputs/elixir-warnings-are-errors/` and requiring both
to exit non-zero. Demonstrated by spelling the flag the way the prior art did:

```
ci/make/elixir.mk:  $(MIX) compile --warning-as-errors     # singular
python3 ci/parity.py
  [INERT] elixir-warnings-are-errors
    local  exit 0    ci  exit 0
    NEITHER invocation rejected ci/broken-inputs/parity/inputs/elixir-warnings-are-errors
```

The same edit leaves `ci/gates/parity.py` passing, and that is correct rather than a hole: the two
invocations really are the same invocation. The gate says what it decides, and the two halves cover
each other.

## `inputs/` — what the executing half runs against

Each is a minimal project holding exactly one defect, so that an invocation exiting non-zero over it
did so for the obligation's reason.

- `inputs/elixir-warnings-are-errors/` — one module with an unused binding.
  `elixirc_options: [warnings_as_errors: true]` is deliberately absent from its `mix.exs`: with it
  set, `mix compile` refuses whatever flag it was handed, and the input could no longer tell a
  working flag from an inert one.
- `inputs/elixir-format/` — one module the formatter would rewrite.
- `inputs/go-lint/` — one module discarding an error, which `errcheck` refuses under the repository's
  one `.golangci.yml`.

These sit under `inputs/` rather than under a `tree*/` directory on purpose: `ci/gates/meta.py` and
`ci/gates/fixture_declarations.py` both enumerate `tree*`, and these are not scenarios for this gate
— they are the subjects of a different program.

## Expected

`tree/`: exit 1, five violations. `tree2/`: exit 1, five violations.
`ci/gates/parity.py --report-only` over the repository: exit 0, whatever it found.
