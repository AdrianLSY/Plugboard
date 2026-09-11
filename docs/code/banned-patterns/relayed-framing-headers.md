---
type: banned-pattern
status: planned
authority: rationale
---

# Framing is decided per hop, and a received `Content-Length` or `Transfer-Encoding` is never relayed

<a id="relayed-framing-headers"></a>

**Gate:** planned — the framing-authority fixtures of rebuild-plugboard task 12.4 and the
reconciling defective counterpart of
[task 15.11](../../../openspec/changes/rebuild-plugboard/tasks.md)

Prohibited: copying a `Content-Length` or `Transfer-Encoding` field from one hop onto the next,
carrying either over the tunnel, and reconciling a message that arrives with both instead of
refusing it. Each hop states the framing of what it is actually sending.

## Why

The prior attempt relayed `Content-Length` verbatim (`proxy_controller.ex:445-449`) while the body
it described was being changed underneath — U+FFFD substitution alters an octet count, so the
declared length and the delivered length disagreed and the exchange stalled or truncated
([the audit](../../history/reference-audit.md)). A relayed length is a claim about a body the
relaying hop is no longer the author of.

Refusal, not reconciliation, is the rule for the ambiguous case: a message carrying both a length
and a chunked coding has two answers, and choosing one silently is how request smuggling gets in.
The decision is D6, framing authority is per-hop; the fixture is a message carrying both
([testing](../testing.md#conformance-fixtures-seeded-adversarially)).

## Related

- [A body is octets end to end](body-as-a-string.md) — the reason the relayed length was wrong.
- [Header fields are an ordered list of pairs](headers-as-a-map.md).
