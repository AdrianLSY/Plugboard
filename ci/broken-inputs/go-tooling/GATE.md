# Violating input: the Go checking commands

- **Checked by:** `ci/go-tooling-check.py` (a SCRIPT, not a gate module — declared in `ci/vault.json`
  `gate_policy.script_paired_inputs`)
- **Rule note:** `docs/code/rules/language-conventions-keyed-on-source.md`
- **Tasks:** `rebuild-plugboard` 3.2 and 3.3 on the Go side, and the violations task 2.3 verified by
  hand rather than committing.

## One violating module per checking command

Each directory is a complete, standalone Go module. That is simpler than the Elixir half, which has to
overlay a fixture onto a copy of `proxy/` because `mix format`'s inputs are `{config,lib,test}/**`.

| module | refused by | the case |
| --- | --- | --- |
| `tree-gofmt` | `golangci-lint` | `File is not properly formatted` |
| `tree-errcheck` | `golangci-lint` | `(errcheck)` — an unchecked type assertion |
| `tree-gocyclo` | `golangci-lint` | `(gocyclo)` — complexity 20 against a ceiling of 15 |
| `tree-race` | `go test -race` | `DATA RACE` |

## Why `go fmt` is not one of the commands

It **rewrites** the file and then succeeds. A rewriter checks nothing, so the format obligation is
reached through `golangci-lint`'s `gofmt` formatter, which reports a file it would have rewritten as
an issue. Task 3.2 asks for a format *gate*; `make fmt` is not one and was never going to be.

## The assertion the Elixir checker did not have at first

A tree's declared `tool` must appear in its declared `fails`. Without it the roster is satisfied by
the **label**: swapping two trees' tool names leaves every tool bound to no input at all and the check
still passes. An adversarial review found exactly that in `ci/proxy-tooling-check.py`, so this one
carries the assertion from the start. Demonstrated by swapping a label and observing two failures.

## Expected

Exit 0 on the tree as committed, with one `[ok  ]` line per module. Exit 1 naming the module if any
command stops refusing its own input.
