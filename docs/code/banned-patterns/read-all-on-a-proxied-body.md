---
type: banned-pattern
status: current
authority: rationale
---

# A proxied body is emitted as it arrives, and nothing accumulates it first

<a id="read-all-on-a-proxied-body"></a>

**Gate:** `ci/gates/banned_patterns.py` — every `ReadAll` in production Go, with an explicit escape
for a read that is not a body in transit. The accumulate-into-a-list shape it cannot see is held by
[the aggregate-before-emitting defective counterpart](../../../openspec/changes/rebuild-plugboard/tasks.md)
of task 15.4.

Prohibited: `io.ReadAll` on a proxied body, appending chunks into a list or buffer before emitting
any of them, and any size or content check that needs the whole body first. A hop reads a chunk and
writes a chunk.

## Why

The prior attempt's "streaming" read the entire body into a `[]string`, *then* decided whether it
was chunked — `chunked := len(chunks) > 1` at `telephone.go:881`, inside `telephone.go:829-901` —
and then shipped every chunk inside one message ([the audit](../../history/reference-audit.md)). So
the code path named for streaming had the memory profile and the latency of full aggregation, and
server-sent events could not exist over it. On the proxy side `proxy_controller.ex:250` called
`read_body(conn)` for the same purpose.

Aggregation is also invisible in a test suite of small fixtures, which is why the corpus carries a
response body larger than memory and a client that disconnects mid-stream
([testing](../testing.md#conformance-fixtures-seeded-adversarially)).

## Related

- [Every queue, buffer and accumulator carries a bound](unbounded-accumulator.md) — an accumulator
  that is permitted at all still declares its bound.
- [A body is octets end to end](body-as-a-string.md).
