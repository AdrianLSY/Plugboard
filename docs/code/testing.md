---
type: essay
status: current
authority: rationale
---

# Testing

**Three tiers, and the first one is a correctness control.** Both facts are stated once, as rules
rather than as prose here: [every test runs in one of three declared tiers](rules/test-tiers.md), and
[the fast tier stays inside ten seconds](rules/fast-tier-latency-budget.md) — the budget that makes
that tier a correctness control rather than a convenience. Above both sits
[the conformance suite's authority](rules/conformance-suite-is-the-authority.md) over any
implementation's own tests.

What follows is the orientation those rules do not carry: the probe a reviewer applies to a new test,
the fixtures the suite starts from, and what a change description says about its tests.

## Mutation thinking as the review standard

For any new test, the author states: *name a one-line change to the code under test that this test
would not catch.* If the answer is "none", good. If the answer is easy, the test is weak. This is the
probe that surfaced most of the audit's test findings, and it is cheap to apply in review.

Whether a stand-in rather than the real subject can carry a verification is settled by one criterion
the plan applies, stated once in
[the change's design register](../../openspec/changes/rebuild-plugboard/design.md#staged-delivery-and-the-task-that-closes-each-stage)
rather than here.

## Conformance fixtures, seeded adversarially

The suite starts from cases that break naive implementations, **written before the implementation**:

- a lone `0x80` byte in a body (kills UTF-8 coercion)
- two `Set-Cookie` lines (kills header maps)
- both `Content-Length` and `Transfer-Encoding` (must be rejected, not reconciled)
- `%2F` inside a path segment (must not be normalised)
- a trailing-slash collection URI (WebDAV depends on it)
- a `HEAD` with non-zero `Content-Length`
- a fragmented WebSocket message (kills message-level libraries)
- a response that emits headers then stalls 90 seconds (kills total-timeout designs)
- a `PROPFIND` (kills method allowlists)
- a response body larger than memory (kills aggregation)
- a client that disconnects mid-stream (proves cancellation propagates)

---

## What a PR says about its tests

The change description asks the author to name the specific wrong implementation each new test would
reject. The template carrying that question is in [reviewing](reviewing.md#pr-template); the standard
for the answer is mutation thinking, above.

---

## Prohibitions on test shape

Four shapes are review blockers, and `CLAUDE.md` lists them as such. Each is now its own rule note
with its own stable anchor, its own cited defect and its own enforcement status, so that a reviewer
raising one cites a rule rather than a paragraph — the split
[task 6.12](../../openspec/changes/archive/2026-09-12-restructure-docs-as-vault/tasks.md) called for, and a move rather
than a rewrite. Each note cites the observed failure it came from, which is also in
[the finding table](../method/harness.md#the-finding-to-constraint-table).

- [A test helper never performs the state transition it is written to wait for](rules/no-helper-repairing-awaited-state.md)
  — the wait helper that called `reload_all()` on timeout and reported success.
- [A test asserts the intended behaviour, never the defective behaviour it found](rules/no-test-accommodating-a-defect.md)
  — the three tests that explained in a comment why they avoided the obvious case.
- [A security or correctness property is never weakened or disabled in test configuration](rules/no-property-weakened-in-test-config.md)
  — `m_cost: 8` and `allow_localhost_hooks: true`, which made the property under test the one
  property not under test.
- [No uncertainty marker, and no unconditional skip, stands in for a failing assertion](rules/no-uncertainty-marker-or-skip.md)
  — the committed "let me think again", and the skip whose coverage claim was false.

The review-side signatures these four point at are in
[reviewing](reviewing.md#ai-generated-pr-review).

> Orientation, not behaviour. The specifications win.
