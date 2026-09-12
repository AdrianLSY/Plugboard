---
type: procedure
status: planned
authority: rationale
---

# Adding a feature, in the order the artifacts are touched

**Gate:** planned — the absent-artifact check that keeps this procedure honest now runs
([`ci/gates/entry_points.py`](../../ci/gates/entry_points.py) for the entry files,
[entry files route](../method/rules/entry-files-route.md) for the rule), but nothing yet checks that
step 4 is not skipped; that arrives with
[rebuild-plugboard task 1.10](../../openspec/changes/rebuild-plugboard/tasks.md).

Five steps, in one order. The order *is* the procedure: a step taken out of turn — code before its
specification, implementation before the fixture that gates it — is the defect this note prevents,
and the one the previous attempt shipped.

## 1. Specify it, before any code

`openspec new change <name>` scaffolds the directory; `CLAUDE.md` names the skills that drive the
workflow. Then the four artifacts, in this order: `proposal.md` (why, and what breaks without it) →
`specs/<domain>/<capability>/spec.md` (the requirement and its scenarios) → `design.md` (the
decision, and the alternatives refused) → `tasks.md` (ordered, each task carrying its own
verification).

Nothing downstream starts until `openspec validate <change> --strict` exits zero.

## 2. Prove it failing, before the implementation

The conformance fixture is written **before** the code it gates, and adversarially —
[the seeded list](testing.md#conformance-fixtures-seeded-adversarially) is where a new one belongs.
A fixture written afterwards tests the implementation's opinion of the contract, not the contract;
the suite outranks any implementation's own tests. Where fixtures live is planned, below.

## 3. Write the code in the component that owns it

Which component that is comes from its boundary note, [stated
once](../../openspec/specs/docs/code-standards/spec.md#requirement-a-components-boundary-is-stated-once)
so placement is answerable before a file is chosen. The component directories are planned.

## 4. Update what travels with the change

In the same change, not afterwards: the affected specification, the
[capability note](../capabilities/index.md), the [glossary](../glossary.md) if the change introduces
a term used in a defining sense, and a decision note if a decision was taken. Every behavioural
sentence carries a `file:line` or a named test ([the citation rule](../method/rules/citations.md));
prose summarising a requirement links to it rather than copying it
([one copy](../method/rules/one-copy-of-requirement-text.md)). A change touching a documented
behaviour and no note says `docs: n/a` with a reason.

## 5. Describe it, then verify

The change description answers [the change-description questions](reviewing.md#the-change-description-questions),
and the review runs [the review checklist](reviewing.md#the-review-checklist). **This procedure's
own verification** — a contributor followed it when all four hold:

- `openspec validate <change> --strict` exits zero; `openspec show <change>` lists all four artifacts.
- The fixture existed in a commit earlier than the implementation it gates, and failed there.
- `make check` exits zero — every vault gate, including links and citations over the step-4 notes.
- `make check-gates` exits zero, so a gate the change added fails on its own violating input.

## Named here, not yet provided

| named | provided by | what stands in today |
|---|---|---|
| a conformance suite with cases in it | [rebuild-plugboard task 13.1](../../openspec/changes/rebuild-plugboard/tasks.md) | the module builds and cross-compiles (task 2.6) and carries no case: the adversarial corpus is written at section 12 and the runner at 13. Steps 2 and 3 stay ordering claims until then |
| a component toolchain for `make fmt`, `make lint` and `make test` to dispatch to | [rebuild-plugboard task 2.2](../../openspec/changes/rebuild-plugboard/tasks.md) | the targets exist (task 1.7) and refuse by name for a component whose toolchain has not landed, so they report what is missing rather than passing over nothing. `make check`, `make check-gates` and `make check-links` run today |

## Why

A specification with no fixture ahead of it is a wish. The previous attempt's hooks subsystem had a
37 KB specification whose central feature — enriching the request body — was never wired up:
`executor.ex:406` names the extension that would have read the enriched body, and nothing read it.
The one test named for payload passing, `proxy_controller_test.exs:835`, uses `GET` and asserts only
on the method, so no fixture contradicted the document. [The audit](../history/reference-audit.md)
holds both; [the finding table](../method/harness.md#the-finding-to-constraint-table) carries the
constraint.

> Orientation, not behaviour. The specifications win.
