# Contributing to Plugboard

**There is no product code yet.** This repository is the plan — sixteen capability specifications, a
decision register, a task list and the vault that explains them. [Start here](docs/start-here.md) is
the entry point; [the README](README.md) says what the product is meant to be.

That shapes what a contribution looks like today. The highest-value thing you can do is not a feature:
it is a fixture, a gate, or a defect found in a specification before anything is built against it.

## The one command

```bash
make check
```

Every gate a merge depends on, in one run, with the roots each covered printed even when it passes. It
needs Python 3 and [OpenSpec](openspec/config.yaml) on `PATH`; nothing else. If it is red, nothing
else matters yet.

## The three test tiers

Every test runs in exactly one declared tier — **fast**, **integration**, or **conformance** — stated
once in [the tier rule](docs/code/rules/test-tiers.md), with the reasoning in
[testing](docs/code/testing.md). The two properties that matter to you before you write a test:

- The **fast** tier needs no Postgres, no network and no sleeps, and it is what runs on save. Its
  latency is treated as a correctness control, not a convenience — see
  [the latency budget](docs/code/rules/fast-tier-latency-budget.md).
- A test is judged by [mutation thinking](docs/code/testing.md#mutation-thinking-as-the-review-standard):
  name the wrong implementation it would reject. If you cannot, it is decorative.

## The on-ramp: the conformance suite

*"Write a sidecar in your language; here is the suite that tells you when you are done."* That is the
best-scoped, highest-status contribution an outside contributor can make, and it exists as a side
effect of [contract-first](docs/decisions/d23-contract-first.md). The reasoning, and what else the
contributor experience owes you, is in [contributor experience](docs/code/contributing.md).

Good first issues are the conformance fixtures. Each is bounded work against an existing primitive,
and the corpus is written *before* the code it gates — so a fixture can land ahead of the
implementation it holds to account.

---

The three lists below are **named here and stated elsewhere.** Each is single-sourced in
[reviewing](docs/code/reviewing.md) and cited by number, so "checklist item 4" means one thing. This
file names every item and restates none of them, and
[`ci/gates/review_obligations.py`](ci/gates/review_obligations.py) fails the build if an item is added
there and not named here — [the rule](docs/code/rules/review-obligations-single-sourced.md).

## The change-description questions

Four, answered in [the PR template](docs/code/reviewing.md#pr-template), stated at
[the canonical anchor](docs/code/reviewing.md#the-change-description-questions):

1. [What breaks if this is wrong](docs/code/reviewing.md#the-change-description-questions)
2. [The wire-contract impact](docs/code/reviewing.md#the-change-description-questions)
3. [What was tested, and what the test would catch that a wrong implementation would not](docs/code/reviewing.md#the-change-description-questions)
4. [Which pre-submit checks were run](docs/code/reviewing.md#the-change-description-questions)

## The review checklist

Nine, in order, at [the canonical anchor](docs/code/reviewing.md#the-review-checklist). The first four
would each have caught a defect that actually shipped in the prior art:

1. [Does the body survive?](docs/code/reviewing.md#the-review-checklist)
2. [Are headers still an ordered list of pairs?](docs/code/reviewing.md#the-review-checklist)
3. [Does the method pass through unmodified?](docs/code/reviewing.md#the-review-checklist)
4. [Does it stream, or does it aggregate?](docs/code/reviewing.md#the-review-checklist)
5. [Does the test prove the thing?](docs/code/reviewing.md#the-review-checklist)
6. [Is the mutation authorized in its signature?](docs/code/reviewing.md#the-review-checklist)
7. [Is the queue bounded?](docs/code/reviewing.md#the-review-checklist)
8. [Is the error typed?](docs/code/reviewing.md#the-review-checklist)
9. [Does it change how a gate finds its subjects?](docs/code/reviewing.md#the-review-checklist)

## Blocking objections

Sixteen, and the set is **closed**: an objection outside it is a comment, not a refusal. A rule in
[the quarantine](docs/code/rules/preferences/) carries no gate and is never one of these. Stated at
[the canonical anchor](docs/code/reviewing.md#blocking-objections); each item links the note that owns
its rule.

1. [Headers as a map](docs/code/banned-patterns/headers-as-a-map.md)
2. [A body carried as a string, or coerced to a character encoding](docs/code/banned-patterns/body-as-a-string.md)
3. [A proxied body accumulated before it is emitted](docs/code/banned-patterns/read-all-on-a-proxied-body.md)
4. [A method allowlisted or rewritten](docs/code/banned-patterns/method-allowlists.md)
5. [A received `Content-Length` or `Transfer-Encoding` relayed](docs/code/banned-patterns/relayed-framing-headers.md)
6. [Application middleware reaching proxied traffic](docs/code/banned-patterns/middleware-on-proxied-traffic.md)
7. [A term rendering on the wire in place of a typed code](docs/code/banned-patterns/inspect-on-a-wire-payload.md)
8. [A queue, buffer or accumulator with no bound](docs/code/banned-patterns/unbounded-accumulator.md)
9. [A mutation whose signature does not take the acting principal](docs/code/reviewing.md#blocking-objections)
10. [A helper that performs the transition it waits for](docs/code/rules/no-helper-repairing-awaited-state.md)
11. [A test that accommodates a defect instead of exposing it](docs/code/rules/no-test-accommodating-a-defect.md)
12. [A property weakened or disabled in test configuration](docs/code/rules/no-property-weakened-in-test-config.md)
13. [An uncertainty marker, or a skip standing in for a failing assertion](docs/code/rules/no-uncertainty-marker-or-skip.md)
14. [A module or a function past its ceiling, or duplication past the threshold](docs/code/rules/module-size-ceiling.md)
15. [A change description leaving one of the four questions unanswered](docs/code/reviewing.md#blocking-objections)
16. [A fix with no case that failed before it](docs/code/fixing-a-bug.md)

---

## Procedures

- [Adding a feature](docs/code/adding-a-feature.md) — the order the artifacts are touched.
- [Fixing a bug](docs/code/fixing-a-bug.md) — starting from a case that fails.
- [Authoring a note](docs/method/conventions.md) — fifteen conventions, each with its gate.
- [Reviewing a change](docs/code/reviewing.md) — how a change is proposed, described and refused.

## Two things that will trip you first

- **Never hand-edit a generated file.** `docs/index.md`, every `docs/*/index.md`,
  [`docs/rule-index.md`](docs/rule-index.md) and [`docs/method/conventions.md`](docs/method/conventions.md)
  are produced by the tools under `ci/gen/`. Regenerate and commit the result; the drift gate reads the
  bytes, not the intent.
- **Every claim carries a citation** into a tracked file or an obtainable artifact, or an explicit
  `Unverified` marker — [the rule](docs/method/rules/citations.md). A confident unsourced sentence is
  the failure mode this repository exists to remove.

> The contract wins, then the specifications, then the decisions in force, then the vault notes, then
> the generated indexes. [Stated once](docs/method/authority-precedence.md).
