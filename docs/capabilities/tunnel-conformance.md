---
type: capability
status: planned
authority: rationale
---

# Conformance

**`tunnel/conformance`** — the independently executable suite that decides whether an implementation
speaks the wire contract, and what a passing result entitles it to claim.

It is what makes *write a sidecar in any language* an offer rather than an aspiration, and it is the
only lever the operator has over implementations they do not control and cannot upgrade. Everything
about its shape follows from that audience: a third party has to be able to obtain it and run it
against their own code, it supplies every party in a run except the **implementation under test**, and
it makes its assertions on the wire rather than against either side's internals. See
[the glossary](../glossary.md#capability-and-conformance) for that term, *run* and *declaration-based
skip*.

The one idea worth carrying away is that coverage is counted against requirements rather than against
assertions, and that the suite is itself proven — by being run against implementations broken on
purpose, so a case that would pass anything is caught before it is trusted. The prior art is the whole
argument for that inversion. It asserted its wire contract twice, on both sides, and each assertion
ran against a different fiction: a channel test that replaced the serializer with a no-op, and Go
tests that marshalled struct tags production never used (`telephone_channel_test.exs:101`,
`telephone_test.go:473`). Both sides were green while `POST` bodies arrived empty. The same audit
names the sharper version — a wait helper that repaired the state it was waiting on, so 947 lines of
tests covered a mechanism that had never once run (`mount_notifier_test.exs:554-560`). See
[the reference audit](../history/reference-audit.md#the-contract-is-asserted-twice-against-two-fictions)
and [D23](../decisions/d23-contract-first.md).

Two boundaries keep a verdict meaning something. A declaration-based skip is the only admissible
kind, reported apart from a failure — and declaring almost nothing is not therefore a cheap route to
a pass. And a verdict says nothing about how the subject is deployed: topology is invisible to it,
while mixed-version pairings are exercised on purpose, because that is the condition production is
permanently in.

## What it owns

- the suite as an obtainable artifact a third party runs against their own implementation
- both contract roles, mixed-version pairings, and a run scoped to one version and one declared capability set
- coverage counted per requirement, cases derived only from normative text, published cases frozen
- determinism, case independence, timing expressed against declared bounds, and a bounded full run
- machine-readable results, and a human summary that names the violated requirement
- the gate that fails its caller on a non-conformant verdict, and the suite's own proof against broken implementations

## What it does not own

- the behaviour under test, or the vocabulary a violation is reported in — [the wire contract](tunnel-wire-contract.md)
- the version range an artifact declares about itself without being run — [packaging](operability-packaging.md)
- the tests a component writes for its own internals — [testing](../code/testing.md)
- what a sidecar has to do to be worth running against the suite — [the sidecar program](sidecar-program.md)

## Depends on

- [packaging](operability-packaging.md) — an artifact declares the contract-version range it speaks, readable without running it, which is what makes a pairing judgeable before a run and a run scopeable to one version

## Shaped by

- [D23 — Contract-first, with a conformance suite](../decisions/d23-contract-first.md) — made the suite, not either side's unit tests, the authority on wire behaviour, and put its adversarial cases before the code they gate
- [D3 — Capability negotiation, with refusal rather than degradation](../decisions/d03-capability-negotiation.md) — made declaration the thing a run is scoped to, and so made the declaration-based skip the only honest skip
- [D24 — Version skew is the governing constraint](../decisions/d24-version-skew.md) — made mixed-version pairings and a frozen published case set part of the subject rather than refinements
- [D1 — Three primitives, not twelve protocols](../decisions/d01-three-primitives.md) — fixed what breadth of coverage means: exchange shapes and fidelity classes, never a protocol roster

## The specification

[`tunnel/conformance`](../../openspec/changes/rebuild-plugboard/specs/tunnel/conformance/spec.md)
owns the behaviour. Where this note and it disagree, it wins.
