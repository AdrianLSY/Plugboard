---
type: banned-pattern
status: planned
authority: rationale
---

# A body is octets end to end, and no character encoding is applied to it

<a id="body-as-a-string"></a>

**Gate:** planned — the transcoding defective counterpart of rebuild-plugboard task 15.3 and the
body-octet-coercion counterpart of task 26.2, both pinned by the octet-digest test of
[task 4.3](../../../openspec/changes/rebuild-plugboard/tasks.md)

Prohibited: carrying a body as a JSON string, a `String`/`string` conversion of body octets, or any
other coercion into a character encoding. One binary-safe body path serves both primitives; a second
body path is itself the finding, whether or not it is correct.

## Why

The prior attempt converted response octets to a string as it read them —
`telephone.go:853` (`chunks = append(chunks, string(buf[:n]))`), then `telephone.go:914`
(`"body": resp.Body`) and `message.go:65` (`json.Marshal(arr)`), with the same defect in the request
direction at `telephone.go:791`. Every octet sequence that is not valid UTF-8 came out as U+FFFD, and
a multi-byte character straddling a read boundary was corrupted even in text
([the audit](../../history/reference-audit.md)).

The instructive part is that the *same codebase* got it right once: the WebSocket path base64-encodes
frame payloads unconditionally in both directions (`websocket.go:201`, `manager.go:377` — see
[carry-forward](../../history/carry-forward.md#base64-frame-payloads)). Two body paths, no shared
abstraction, one wrong. That is why a second body implementation is prohibited rather than reviewed.

The fixture is a lone `0x80` byte in a body ([testing](../testing.md#conformance-fixtures-seeded-adversarially)).

## Related

- [Header fields are an ordered list of pairs](headers-as-a-map.md).
- [Framing is decided per hop](relayed-framing-headers.md) — coercion changes a body's length, which
  is why relaying the length it arrived with compounds this one.
