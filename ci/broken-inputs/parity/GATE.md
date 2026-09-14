# Violating input: parity

- **Gate:** `ci/gates/parity.py` (`parity`)
- **Rule note:** `docs/method/rules/one-obligation-one-invocation.md`
- **Tasks:** `rebuild-plugboard` 3.11 and 3.12.

## Violations

**Drift between two encodings of one obligation (task 3.11).** `ci/make/go.mk` passes `--timeout 5m`
and the workflow's `args:` does not; the workflow passes `--fix` and the make recipe does not. Neither
side is obviously wrong read alone — that is the whole difficulty. The prior art ran
`mix compile --warning-as-errors` locally, **singular and therefore inert**, against the plural flag in
CI, for months, and the two agreed often enough that nobody looked.

One finding per divergent **flag**, with the number of CI invocations it diverges in — not one per
invocation. The real tree has three `golangci-lint-action` steps, one per Go module, so a single
drifted flag reported per step is one defect printed three times.

**The recurring runner, satisfied by nothing (task 3.12).** No `schedule` trigger, and both standing
checks merely echoed.

## The case that matters most, and why it is here

`- run: echo "make check-gates"` **is** a `run:` body and it **does** contain the command. The first
attempt at this check compared the declared commands against the whole file and passed on exactly this
shape; the second read `run:` bodies and *still* passed on it, which I found by feeding the gate its
own counter-example rather than by reading the code.

So a command must now appear at a **command position** — the start of a line, or after `&&`, `||`,
`;` or a pipe. `cd proxy && mix sobelow --exit` runs sobelow; `echo "mix sobelow --exit"` does not, and
the difference is exactly where the string sits relative to those separators. The same fix went into
`ci/gates/security_scan.py`, which had the same gap.

## What this still cannot decide

A command reached through a variable, a script file or an alias. `run: $SCANNER` runs something no
regex can name. The check is a floor, not a proof, and `ci/gates/_workflow.py` says so.

## Expected

Exit 1, five violations.
