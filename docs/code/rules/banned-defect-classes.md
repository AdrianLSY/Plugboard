---
type: rule
status: current
authority: rationale
---

# Five defect classes are banned by name, and checked

**Gate:** `ci/gates/banned_patterns.py`

Five constructs are refused in tracked Elixir and Go source, and a failure names the note stating the
one it broke:

1. A one-value-per-name container over header fields —
   [headers as a map](../banned-patterns/headers-as-a-map.md).
2. A proxied body accumulated before any of it is emitted —
   [read-all on a proxied body](../banned-patterns/read-all-on-a-proxied-body.md).
3. A term rendering that can reach a peer —
   [`inspect/1` on a wire payload](../banned-patterns/inspect-on-a-wire-payload.md).
4. A `GenServer` that monitors and never traps exits.
5. `with` in a controller action with no `else`.

The last two carry no note of their own because they are shapes rather than constructs; both come from
[the finding table](../../method/harness.md#the-finding-to-constraint-table), and neither is a
[blocking objection](../reviewing.md#blocking-objections) — that set is closed and numbered, and
adding to it is an edit there.

## Why these five

Each is a defect that shipped. Headers were typed as a single-valued map on **both** sides, so every
`Set-Cookie` past the first was deleted with no error and no log line. The "streaming" path read the
whole body into a list and then decided whether it was chunked. The refresh-token error path shipped
an Elixir term rendering over the channel, which no client can branch on. The notifier linked without
trapping exits, so it died before its `:DOWN` clause could run and the documented exponential backoff
was unreachable ceremony. All four are in [the audit](../../history/reference-audit.md) with a
`file:line`.

## What the checks do not decide

The rule as written, in every case — no text check knows what a value holds. Each is narrowed to
something decidable, and the narrowing is stated in the gate's own module rather than left for a
reader to assume. The trade is deliberate and one-directional: **false negatives, never false
positives.** A check firing on every `map[string]string` in a Go tree is switched off inside a week,
and the rule then has no enforcement rather than partial enforcement.

Two of the five carry an explicit escape — a comment with the declared marker and a reason — because
reading a configuration file at startup and rendering a term into a log line are both legitimate and
have to stay writable. What the rule refuses is doing either silently on something a peer will see.
