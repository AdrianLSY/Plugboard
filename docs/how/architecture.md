---
type: essay
status: current
authority: rationale
---

# The architecture

The whole system in one page. When another note says "the architecture", this is the note it means;
the three notes it points at carry the argument.

Three claims hold the design together, and each has its own note:

| | the claim | note |
|---|---|---|
| **what is carried** | Twelve named protocols are three transport primitives, and nine of the twelve are the same one. There is no protocol-specific code. | [three primitives](three-primitives.md) |
| **how it is carried** | The unit on the wire is a frame carrying a stream id, not a message carrying a whole exchange — which deletes a multiplexer the previous attempt hand-built, and which is refused rather than degraded when a sidecar cannot back it. | [the tunnel](the-tunnel.md) |
| **where it runs** | An Elixir proxy, a Go sidecar in the tenant's pods, a deferred Go terminator for HTTP/3 — with every edge protocol behind the versioned contract so a terminator is swappable. | [topology](topology.md) |

Read them in that order the first time. The middle one is the one that earns the reading: it is the
claim the previous attempt got wrong, and its consequences reach every other component.

**This note states no behaviour.** Orientation is layer 4 of the precedence order — below the
machine-checked contract, below the specifications' `SHALL` statements, below the decisions in
force — so where a sentence here and a specification disagree, the specification wins, and where a
sentence here and [the register](../../openspec/changes/rebuild-plugboard/design.md) disagree, the
register wins.

## Where to go next

| when you want | read |
|---|---|
| the primitive that carries a protocol somebody just asked for | [three primitives](three-primitives.md) |
| the frame vocabulary, or why there is no correlation-id map | [the tunnel](the-tunnel.md) |
| what the edge owns and never relays, or why Elixir and Go | [topology](topology.md) |
| what must survive a round trip, tier by tier, and per protocol family | [protocol fidelity](protocol-fidelity.md) |
| the decisions in force, and the one that was overturned | [decisions in force](../decisions/in-force.md) |
| the behaviour itself, which no note here owns | [the specifications](../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md) |
