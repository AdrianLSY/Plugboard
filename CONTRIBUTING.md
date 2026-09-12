# Contributing to Plugboard

**There is no product code yet.** This repository is the plan — the specifications, the decision
register, the documentation vault and the gate harness that refuses prose which drifts from the tree.
Read [start here](docs/start-here.md) before anything else; it carries the five governing facts and
the routing table.

Contributions are accepted under [Apache-2.0](LICENSE) by §5 of that licence, and every commit needs
a [sign-off](#sign-off). There is **no contributor licence agreement** — nothing to sign, no rights
assigned beyond the licence. → [D28](docs/decisions/d28-licensing.md)

---

## The one command

```bash
make check
```

Every vault gate in one command, and CI runs it on every push and pull request. It must be green
before a pull request, and it enumerates every gate it ran, so the inventory is a build output rather
than a prose count. Changes under `openspec/` also need `openspec validate rebuild-plugboard --strict`.

It is not the *only* thing CI runs: the [sign-off](#sign-off) check reads the commits in a pull
request, which no local target can do. Those two workflows are the whole of CI.

---

## Where to start

**The conformance suite is the on-ramp** — *"write a sidecar in your language; here is the suite that
tells you when you are done."* It is the best-scoped, highest-status contribution an outside
contributor can make, and it exists as a side effect of
[D23](docs/decisions/d23-contract-first.md). → [contributor experience](docs/code/contributing.md)

Good first issues are the reserved-but-unimplemented frame types — trailers, 1xx interim responses,
Range — each a bounded piece of work against an existing primitive with a fixture already written.

None of that exists yet either. Until it does, the work is the plan: the vault, the gates, and the
specifications.

---

## Before you write a note

The [conventions](docs/method/conventions.md), each with the gate that enforces it. A first draft
that violates one fails the build rather than a review. The short version: every claim carries a
citation or an explicit `Unverified` marker, relations are relative markdown links, and a note never
states behaviour a specification owns —
[precedence](docs/method/authority-precedence.md) decides who wins.

---

## Tests

Three tiers, and the first one is a correctness control: [every test runs in one of three declared
tiers](docs/code/rules/test-tiers.md), and [the fast tier stays inside ten
seconds](docs/code/rules/fast-tier-latency-budget.md). That budget is not a convenience — when
feedback is slow, an author writes assertions that are cheap to satisfy rather than assertions that
are expensive to satisfy. → [testing](docs/code/testing.md)

The prior attempt had more test code than production code, zero `TODO` markers, and did not catch
that `POST` bodies arrive empty — [the audit](docs/history/reference-audit.md) records each.
**Test volume is not evidence.**

---

## Describing a change

Stated once and [cited by number](docs/code/reviewing.md#the-change-description-questions).
Every pull request answers all four:

| # | answers |
|---|---|
| change-description question 1 | what *breaks* if this is wrong — not what it does |
| change-description question 2 | the wire-contract impact: none, additive, or **BREAKING** |
| change-description question 3 | what was tested, and what the test would catch |
| change-description question 4 | which pre-submit checks were run, item by item |

A `BREAKING` answer cannot merge without a version bump and a capability flag.

---

## The review checklist

Stated once and [cited by number](docs/code/reviewing.md#the-review-checklist). A
reviewer says "checklist item 4" and you find item 4 — there is no second list to disagree with the
first, which is why this table carries numbers and links rather than a copy of the text
([the rule](docs/code/rules/review-obligations-single-sourced.md)).

| # | subject |
|---|---|
| checklist item 1 | the body surviving the round trip |
| checklist item 2 | headers still an ordered list of pairs |
| checklist item 3 | the method passing through unmodified |
| checklist item 4 | streaming rather than aggregating |
| checklist item 5 | the test proving the thing |
| checklist item 6 | the mutation authorized in its signature |
| checklist item 7 | the queue bounded |
| checklist item 8 | the error typed |
| checklist item 9 | how a gate finds its subjects |

The first four are the ones that would have caught actual shipped defects.
**Reviewers reject, not fix.**

---

## Blocking objections

Stated once and [cited by number](docs/code/reviewing.md#blocking-objections) — the closed
set. An objection outside it is a comment rather than a refusal, and a rule in
[the quarantine](docs/code/rules/preferences/) is never one of these: raising a preference as a
refusal is itself a review defect.

| # | construct refused | # | construct refused |
|---|---|---|---|
| blocking objection 1 | headers as a map | blocking objection 9 | a mutation not taking the acting principal |
| blocking objection 2 | a body as a string | blocking objection 10 | a helper performing the transition it waits for |
| blocking objection 3 | a proxied body accumulated | blocking objection 11 | a test accommodating a defect |
| blocking objection 4 | a method allowlisted or rewritten | blocking objection 12 | a property weakened in test config |
| blocking objection 5 | relayed framing headers | blocking objection 13 | an uncertainty marker or a skip |
| blocking objection 6 | middleware on proxied traffic | blocking objection 14 | past a size or duplication ceiling |
| blocking objection 7 | a term rendering on the wire | blocking objection 15 | a description leaving a question unanswered |
| blocking objection 8 | an unbounded accumulator | blocking objection 16 | a fix with no case that failed before it |

The canary is **headers as a map**, with `Set-Cookie` as the case that proves it —
[the eight banned patterns](docs/code/banned-patterns/index.md).

---

## Sign-off

Every commit carries a `Signed-off-by` line certifying the [Developer Certificate of
Origin](DCO) — that you wrote the change, or have the right to submit it under Apache-2.0:

```bash
git commit -s
```

which appends `Signed-off-by: Your Name <your@email>` using your `git config` identity. Use a real
name and a reachable address. `git rebase --signoff` fixes a branch that missed it.

The DCO is an attestation about *provenance*, not a transfer of rights. It exists because this
repository states [what it cannot check](docs/history/obtaining-the-reference.md) rather than
assuming it — and the provenance of contributed code is exactly that kind of claim.

---

## Pull requests

No direct pushes, no force pushes, squash merge so `main` reads as one commit per change. **If a PR
cannot be reviewed in one sitting, split it** — a hard constraint for a solo-maintainer project,
because unreviewable PRs are either merged unread or abandoned, and
[the audit](docs/history/reference-audit.md) records both happening.
→ [reviewing](docs/code/reviewing.md)

Assume a fraction of contributions are model-written, because they will be. If yours is, the
[signatures a reviewer looks for](docs/code/reviewing.md#ai-generated-pr-review) are worth reading
first — tests named for one thing asserting another, tautological assertions, volume where depth is
needed.
