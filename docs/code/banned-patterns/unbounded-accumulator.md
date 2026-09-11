---
type: banned-pattern
status: planned
authority: rationale
---

# Every queue, buffer and accumulator carries a bound and a stated overflow behaviour

<a id="unbounded-accumulator"></a>

**Gate:** planned — the bounded-constructor check of
[rebuild-plugboard task 61.7](../../../openspec/changes/rebuild-plugboard/tasks.md), which fails on
a direct unbuffered or unbounded channel, an append-into-slice accumulator, and an unbounded map
keyed on a peer-supplied value

Prohibited: any queue, mailbox, buffer, accumulator, or map keyed on peer-supplied data that grows
without a declared bound. Each one declares a bound on both axes it can grow on — count and octets —
and what happens on overflow, with the reason distinguishable from every other reason.

## Why

The prior attempt had **one** bounded queue in 20,000 lines. Everything else grew: one channel
process serialised every request and frame for a mount, fed by unbounded `send/2`
(`proxy_handler.ex:275`, `telephone_channel.ex:364-375`), so there was no backpressure at any hop
and a slow backend became the proxy's memory problem
([the audit](../../history/reference-audit.md)).

The one bounded case is the model to generalise, not an exception to tolerate: pre-connect WebSocket
frame buffering bounded on both axes at once (`proxy_handler.ex:34-35`, `:107-136` —
`@max_buffer_frames 100`, `@max_buffer_bytes 1_048_576`), emitting a telemetry reason that
distinguishes `:frame_count` from `:byte_size` and closing with code 1009
([carry-forward](../../history/carry-forward.md#bounded-websocket-frame-buffer)). Bounded, with an
explicit failure that says which bound was reached.

## Related

- [A proxied body is emitted as it arrives](read-all-on-a-proxied-body.md) — the accumulator most
  likely to be written by accident.
