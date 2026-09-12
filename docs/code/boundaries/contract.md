---
type: guide
status: current
authority: rationale
---

# contract — the boundary

`contract/` is the root artifact of the repository, not one component among five. Everything else in
the tree is generated from it, checked against it, or speaks it.
[D23](../../decisions/d23-contract-first.md) makes the versioned schema the thing every implementation
derives from; [D24](../../decisions/d24-version-skew.md) makes it the one artifact a later release can
never correct, because a tenant's sidecar is upgraded on the tenant's schedule or never.

## What it owns

- The interface definition for frame payloads and the codecs generated from it, per
  [D18](../../decisions/d18-frame-payload-encoding.md).
- The declared registers that travel with a version: reserved frame kinds, capability names, the
  error-code space, and the connection parameters with their floor and ceiling.
- The published encode-and-decode vectors, and the changelog that pairs each version tag with the
  support window it declares.
- Requirement identifiers, so a conformance case can name the obligation it exercises.

## What it must not own

- **Transport.** Which pipe the frames travel through is [D19](../../decisions/d19-tunnel-transport.md)'s
  choice and [tunnel/listener](../../../openspec/changes/rebuild-plugboard/specs/tunnel/listener/spec.md)'s
  behaviour. The framing is transport-independent by construction, and welding it to one here would
  make a later transport change a redesign.
- **The suite.** Fixtures, the runner and the coverage report live in `conformance/`. A schema that
  ships its own test corpus can be edited to agree with it.
- **Runtime behaviour.** No process starts here. What a proxy instance or a sidecar does on receiving
  a frame is owned by the specifications, not by the schema that shapes it.

## Why it is separated this way

The prior art asserted its wire contract twice, independently, against two different fictions — the
Elixir side replaced the serialiser with a no-op, the Go side marshalled struct tags production never
used, and neither noticed that request bodies never arrived. One schema with generated codecs removes
the second fiction by removing the second hand-written encoder
([reference audit](../../history/reference-audit.md)).

Component root: [`contract/`](../../../contract/README.md).
Behaviour: [tunnel/wire-contract](../../../openspec/changes/rebuild-plugboard/specs/tunnel/wire-contract/spec.md).
