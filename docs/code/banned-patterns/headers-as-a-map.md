---
type: banned-pattern
status: planned
authority: rationale
---

# Header fields cross every hop as an ordered list of pairs, never a map

<a id="headers-as-a-map"></a>

**Gate:** planned — the banned-defect-class check of [rebuild-plugboard task 3.7](../../../openspec/changes/rebuild-plugboard/tasks.md), with the field-collapsing defective counterpart of task 15.3

Prohibited: `map[string]string`, `Map.new`, `Enum.into(…, %{})`, or any other one-value-per-name
container over header fields — in either direction, at any hop, including a struct field typed that
way. A repeated field name is ordinary, and the order of the pairs is part of the message.

## Why

`Set-Cookie` is the canary: two of them in one response is routine, and a map keeps one. The prior
attempt typed headers as a single-valued map on both sides — `proxy_controller.ex:496`
(`Enum.into(conn.req_headers, %{})`) and `telephone.go:85` — so every `Set-Cookie` past the first
was deleted with no error and no log line, recorded in
[the audit](../../history/reference-audit.md). Nothing failed; the session simply did not arrive.

Two `Set-Cookie` lines is therefore one of the adversarial fixtures written before the code it
gates ([testing](../testing.md#conformance-fixtures-seeded-adversarially)), and
[the review checklist](../reviewing.md#code-review) asks the header question second because a map
reads as tidier than the thing that is correct.

## Related

- [A body is octets end to end](body-as-a-string.md) — the same shape of loss, on the payload.
- [Framing is decided per hop](relayed-framing-headers.md) — the two header fields a hop never
  relays.
