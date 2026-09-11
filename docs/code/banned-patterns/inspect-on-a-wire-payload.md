---
type: banned-pattern
status: planned
authority: rationale
---

# A wire error is a typed code, and no term rendering crosses the wire

<a id="inspect-on-a-wire-payload"></a>

**Gate:** planned — the `inspect/1`-on-a-wire-payload banned-defect-class check of
[rebuild-plugboard task 3.7](../../../openspec/changes/rebuild-plugboard/tasks.md)

Prohibited: `inspect/1` — or any language's debug formatter — applied to a value that leaves the
process, whether as a frame field, an error reason, or a response body. A peer receives an
enumerated code and the fields that code declares.

## Why

The prior attempt's refresh-token error path shipped `inspect(reason)` over the channel
(`telephone_channel.ex:106`): an Elixir term rendering, which no client can branch on and which
changes shape whenever the internal term does
([carry-forward](../../history/carry-forward.md#typed-error-reason-vocabulary)). A peer that cannot
branch on an error either treats every failure alike or parses a debug string, and the second is
worse.

The same codebase again shows the right answer: the sidecar's typed reason vocabulary at
`types.go:63-76` — `connection_refused`, `connection_timeout`, `invalid_upgrade`, `backend_error`,
`invalid_frame_data`, `invalid_path` — is stable, machine-readable, and carried forward. Standardise
on that style everywhere.

A debug rendering is also an exfiltration surface: a term carries whatever was in scope, including
credentials, which is the second reason this is a prohibition rather than a preference.
