---
type: guide
status: current
authority: rationale
---

# conformance — the boundary

`conformance/` holds the executable suite that is the authority on the contract. Not a test directory
belonging to one side: a separately runnable artifact any implementation in any language is pointed
at, which is what makes "a sidecar in any language" an offer rather than an aspiration
([D23](../../decisions/d23-contract-first.md)).

## What it owns

- The adversarial fixture corpus — a lone `0x80` byte, two `Set-Cookie` lines, both framing headers on
  one message, `%2F` inside a path segment, a `HEAD` carrying a non-zero length, a fragmented frame, a
  response that emits its head and then stalls.
- The runner that executes a case against an implementation and reports at the octet level.
- The coverage report that pairs each requirement identifier with the cases exercising it, and the
  defective counterparts that prove a case can fail.
- Cross-compiled binaries for the declared platform set, so the suite runs where the implementation
  does.

## What it must not own

- **The schema.** Registers and vectors are read from `contract/`. A suite that owned the schema could
  be made to agree with itself.
- **Implementation helpers.** Nothing here is imported by `proxy/`, `sidecar/` or `terminator/`. A
  shared helper between the subject and its test is how a test comes to assert the implementation's
  own fiction back at it.
- **Happy-path coverage as a goal.** Cases are written before the code they gate, and a case with no
  defective counterpart is reported as unproven rather than counted as passing.

## Why it is separated this way

The prior art carried more test code than production code and never noticed that request bodies
arrived empty: each side tested its own fiction of the other, and no artifact held the two to one
account ([reference audit](../../history/reference-audit.md)). A suite that is neither side's property
is the smallest structural change that makes that impossible.

Component root: [`conformance/`](../../../conformance/README.md).
Behaviour: [tunnel/conformance](../../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md).
