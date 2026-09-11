---
type: decision
status: current
authority: decision
---

# D27 — Observability before the hot path

**In force.** The metric sink and the structured logger are chosen in the first week of work, and the
thing that proves it is a test asserting a handler is attached and receiving. It rules out the
sequencing everyone prefers — build the streaming spine, learn which signals matter, instrument
afterwards.

Why this is a decision rather than a scheduling preference is worth carrying: in the previous attempt
seventy-five telemetry events were emitted, nothing anywhere consumed them, and most of the auditors
who read that code cited it as evidence of good instrumentation. Emission is visible in review and
consumption is not, which is why the gate has to assert the consumer and why "we will attach handlers
later" cannot be told apart from never. Two things follow. Telemetry lands before the hot path, since
the hot path is where retrofitting costs the most and touches the most. And a review that accepts an
emitted-but-unconsumed signal as instrumentation has reproduced the exact failure this decision
exists to prevent, however good the event names look.

- **Full entry, with rationale and alternatives:** [register D27](../../openspec/changes/rebuild-plugboard/design.md#d27--observability-before-the-hot-path)
- **Shapes:** [operability/observability](../../openspec/changes/rebuild-plugboard/specs/operability/observability/spec.md)
- **Rule notes citing it:** created by [section 6 of this change](../../openspec/changes/restructure-docs-as-vault/tasks.md)

> The register wins where this note and it disagree.
