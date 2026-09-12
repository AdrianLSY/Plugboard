# Violating input: banned-patterns

- **Gate:** `ci/gates/banned_patterns.py` (`banned_patterns`)
- **Rule note:** `docs/code/rules/banned-defect-classes.md`
- **Task:** `rebuild-plugboard` task 3.7 — one planted instance per rule, each failing its own check
  and naming its own rule.

## Violations, one per check

| # | Where | Check | Names |
| --- | --- | --- | --- |
| 1 | `sidecar/relay.go:8` | a one-value-per-name container over header fields | `docs/code/banned-patterns/headers-as-a-map.md` |
| 2 | `sidecar/relay.go:12` | a body accumulated before any of it is emitted | `docs/code/banned-patterns/read-all-on-a-proxied-body.md` |
| 3 | `proxy/lib/wire.ex:5` | `inspect/1` outside a log line | `docs/code/banned-patterns/inspect-on-a-wire-payload.md` |
| 4 | `proxy/lib/notifier.ex:3` | a GenServer that monitors and never traps exits | `docs/method/harness.md` |
| 5 | `proxy/lib/mount_controller.ex:5` | `with` in a controller action with no `else` | `docs/method/harness.md` |

Each failure carries the note path, because the contributor who trips a check is reading at the one
moment the defect is worth explaining — and four of the five are defects that actually shipped in the
prior art, with a `file:line` in the audit.

## The negative controls are in the same files

`relay.go` declares `package relay` and imports `io` without either tripping anything; `notifier.ex`
carries a `:DOWN` clause, which is the construct that makes the module a monitor and is not itself a
defect; `mount_controller.ex` has two private functions with no `with` at all. A check that fired on
proximity alone would emit more than five here, and `expect.json` says five.

## What none of these five decides

The rule as written, in every case. "A map **over header fields**" needs to know what a value holds,
and no text check knows that — so check 1 fires only where the line also names a header token declared
in `ci/vault.json`, and a map built into a variable called `h` two lines earlier is invisible. The
trade is false negatives for zero false positives, deliberately: a check that fired on every
`map[string]string` in a Go tree would be switched off inside a week, and the rule would then have no
enforcement rather than partial enforcement. `ci/gates/banned_patterns.py` states the narrowing for
all five.

## Expected

Exit 1, five violations.
