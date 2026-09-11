---
type: rule
status: planned
authority: rationale
---

# The conformance suite outranks any implementation's own tests

**Gate:** planned — the catalogue meta-test of rebuild-plugboard task 15.9 and the
fixture-to-requirement coverage gate of
[task 12.15](../../../openspec/changes/rebuild-plugboard/tasks.md), with the suite among the
required checks recorded at task 1.6

Where an implementation's own tests and the conformance suite disagree about the wire contract, the
suite decides. A green implementation suite is not evidence of conformance, and a case is not
retired, relaxed, or marked expected-failure to accommodate an implementation.

## Why

The prior attempt asserted its contract twice against two fictions: an Elixir test asserted an atom
key (`telephone_channel_test.exs:101` — `%{ts: ^timestamp}`) that cannot survive a JSON round trip,
and the Go tests marshalled a `ProxyResponse` struct (`telephone_test.go:473`) whose tags production
never used, while the real payload was a hand-built map (`telephone.go:910`). Both suites passed;
neither described the wire ([the audit](../../history/reference-audit.md)). Two ends testing their
own idea of a shared contract is how `proxy_res` came to be asserted by nothing at all.

The suite earns the authority by being adversarial and by being written before the code it gates,
and by being proven against deliberately defective counterparts — a case that cannot reject a known
wrong implementation counts as referenced rather than proven. The fixture list and the
before-the-code rule are in [testing](../testing.md#conformance-fixtures-seeded-adversarially).
