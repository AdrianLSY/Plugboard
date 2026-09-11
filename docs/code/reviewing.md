---
type: essay
status: current
authority: rationale
---

# Reviewing a change

How a change is proposed, described and refused. Each check below is derived from a defect that
shipped; the findings are in [the finding table](../method/harness.md#the-finding-to-constraint-table).

---

## Pull requests

**Trunk-based, short-lived branches, PR required.** The reference pushed 119 commits directly to
`main` with messages like `updated code` ×17. The sidecar used PRs and conventional commits and is
visibly the better-maintained half — that difference is the argument.

**Branch protection on `main`:**
- No direct pushes. No force pushes.
- Required checks: fast suite, lint, format, conformance suite, security scan.
- Linear history (squash merge), so `main` reads as one commit per change.

**PR size.** If a PR cannot be reviewed in one sitting, split it. This is a hard constraint for a
solo-maintainer project with outside contributors, because unreviewable PRs are either merged unread or
abandoned — and both happened in the reference.

### The change-description questions

The canonical enumeration. Four questions, cited by number; every artifact that asks for a change
description links to this anchor instead of keeping its own copy of the list
([the rule](rules/review-obligations-single-sourced.md)).

1. **What breaks if this is wrong.** Not what it does — what it *breaks*. This one question would have
   caught the empty-body defect.
2. **The wire-contract impact**: `none` / `additive` / **`BREAKING`**. A `BREAKING` answer requires a
   version bump and a capability flag, and cannot be merged without one.
3. **What was tested, and what the test would catch that a wrong implementation would not.**
4. **Which pre-submit checks were run**, item by item, so a reviewer reads what the author claims
   rather than inferring it.

### PR template

```markdown
## What breaks if this is wrong?

## Wire contract impact
- [ ] None
- [ ] Additive (new optional field / reserved frame type now used)
- [ ] **BREAKING** -- requires version bump + capability flag

## Tests
Name the specific wrong implementation each new test would reject.

## Checklist
- [ ] Fast suite passes locally (no Postgres required)
- [ ] Conformance suite passes
- [ ] No new `async: false` without a comment saying why
- [ ] Read against every item of the review checklist (docs/code/reviewing.md#the-review-checklist)
- [ ] No blocking objection stands (docs/code/reviewing.md#blocking-objections)
- [ ] Docs updated, or "docs: n/a" with a reason
```

The template's four headings are [the four questions above](#the-change-description-questions), in
the order a body answers them; its checklist points at the two enumerations below rather than
repeating their items, because a template is the artifact most likely to be copied and then left
behind. The standard the *Tests* answer is judged against is
[mutation thinking](testing.md#mutation-thinking-as-the-review-standard). That each of the three
enumerations has one home is itself a rule:
[review obligations are single-sourced](rules/review-obligations-single-sourced.md).

---

## Code review

### The review checklist

**A checklist, because the failures were systematic rather than clever.** Reviewers check these nine
in order; the first four are the ones that would have caught actual shipped defects. This is the
canonical enumeration: an item is cited by its number ("checklist item 4"), and nothing else lists
them again ([the rule](rules/review-obligations-single-sourced.md)).

1. **Does the body survive?** Any change touching the request or response path: does the payload cross
   the boundary intact, and is there a test asserting the exact bytes?
2. **Are headers still an ordered list of pairs?** Any `Map.new`, `Enum.into(…, %{})`, or
   `map[string]string` over headers is a review blocker. `Set-Cookie` is the canary.
3. **Does the method pass through unmodified?** No allowlist, no rewriting.
4. **Does it stream, or does it aggregate?** Any `io.ReadAll`, any accumulation into a list before
   emitting, any size check that requires the whole body first.
5. **Does the test prove the thing?** Specifically: would this test fail against a plausible wrong
   implementation? If a reviewer cannot name that implementation, the test is decorative.
6. **Is the mutation authorized in its signature?** Every context mutation takes the acting principal.
   A caller-side check is not sufficient — that is exactly how `update_token/2` became a cross-tenant
   write.
7. **Is the queue bounded?** The reference has exactly one bounded queue in 20,000 lines. Every new
   buffer, mailbox, or accumulator needs a bound and an explicit overflow behaviour.
8. **Is the error typed?** No `inspect(reason)` on the wire — no client can branch on an Elixir term
   rendering.
9. **Does it change how a gate finds its subjects?** Any change to
   [`ci/gates/_common.py`](../../ci/gates/_common.py)'s `tracked_markdown`, `candidates`, `notes` or
   `classify` is checked against every gate's reported subject count before and after, because that
   module is imported by all of them and is the one thing no gate covers: it is excluded from
   [the meta-check](../method/rules/gates-are-demonstrated-to-fail.md) by name, and a fixture tree
   takes the other branch of `tracked_markdown`, so a break confined to the work-tree branch is
   invisible to it. Narrowing one predicate there collapses twelve gates' subject sets by roughly
   80% while every one of them still reports `[ok]`. This is the weakest-protected surface in the
   harness, and the only reason it is a checklist item rather than a gate is that no cheap check
   closes it — [the gate-harness design](../../openspec/changes/archive/2026-09-12-harden-vault-harness/design.md)
   records that trade-off rather than dressing it up.

**Reviewers reject, not fix.** A reviewer who fixes the problem removes the author's chance to learn
the pattern, and in a solo-maintainer project with AI-assisted contributors that is how the same defect
returns.

### Blocking objections

The canonical set, numbered and closed: an objection outside it is a comment rather than a refusal.
Each item names where its rule is stated and none of them restates it here, because a second copy of
a rule is how the two copies come to disagree. A rule in [the quarantine](rules/preferences/) carries
no gate and is never one of these — raising a preference as a refusal is itself a review defect.

Wire and structure, one note per construct:

1. [Headers as a map](banned-patterns/headers-as-a-map.md)
2. [A body carried as a string, or coerced to a character encoding](banned-patterns/body-as-a-string.md)
3. [A proxied body accumulated before it is emitted](banned-patterns/read-all-on-a-proxied-body.md)
4. [A method allowlisted or rewritten](banned-patterns/method-allowlists.md)
5. [A received `Content-Length` or `Transfer-Encoding` relayed](banned-patterns/relayed-framing-headers.md)
6. [Application middleware reaching proxied traffic](banned-patterns/middleware-on-proxied-traffic.md)
7. [A term rendering on the wire in place of a typed code](banned-patterns/inspect-on-a-wire-payload.md)
8. [A queue, buffer or accumulator with no bound](banned-patterns/unbounded-accumulator.md)
9. A mutation whose signature does not take the acting principal — checklist item 6, and an invariant
   in [`CLAUDE.md`](../../CLAUDE.md).

Test shape and size:

10. [A helper that performs the transition it waits for](rules/no-helper-repairing-awaited-state.md)
11. [A test that accommodates a defect instead of exposing it](rules/no-test-accommodating-a-defect.md)
12. [A property weakened or disabled in test configuration](rules/no-property-weakened-in-test-config.md)
13. [An uncertainty marker, or a skip standing in for a failing assertion](rules/no-uncertainty-marker-or-skip.md)
14. A module or a function past its ceiling, or duplication past the threshold —
    [module](rules/module-size-ceiling.md), [function](rules/function-size-ceiling.md),
    [duplication](rules/duplication-threshold.md).

Description and procedure:

15. A change description leaving one of [the four questions](#the-change-description-questions)
    unanswered, or answering `BREAKING` with no version bump and no capability flag.
16. A fix with no case that failed before it — [fixing a bug](fixing-a-bug.md).

### AI-generated PR review

Assume a fraction of contributions are model-written, because they will be. The audit gives the
signature to look for:

- **Tests that accommodate a defect** rather than exposing it — usually visible as a comment explaining
  why the test avoids the obvious case.
- **Abandoned reasoning committed as comments.** "Actually this shouldn't be…", "let me think again",
  "for now we just…".
- **Named for one thing, asserting another.** Four tests in the reference assert the negation of their
  own name, three of them saying so in their own comments.
- **`@tag :skip` with a false claim about coverage elsewhere.** The reference skipped its only
  mount-point hook success test, claiming another file covered it. It did not.
- **Tautological assertions** — asserting a value the test just set, or asserting only that a call did
  not raise.
- **Volume where depth is needed.** A 637-line test file against a 245-line config module is a signal,
  not a virtue.

The four prohibitions on test shape these signatures point at are stated as rules in
[testing](testing.md#prohibitions-on-test-shape).

> Orientation, not behaviour. The specifications win.

## What owns these obligations

This note is orientation. The obligations themselves — that every rule names its enforcing gate and
every gate names its rule, that unenforced preference is quarantined rather than left looking like a
requirement, and that every gate is demonstrated to fail on a deliberately violating input — are
normative in
[`docs/code-standards`](../../openspec/specs/docs/code-standards/spec.md).
Where this note and that specification disagree, the specification wins.
