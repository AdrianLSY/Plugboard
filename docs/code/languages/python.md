---
type: guide
status: current
authority: rationale
---

# Python conventions

Python is the only language holding tracked source today: the gate modules under `ci/gates/`, the
generators under `ci/gen/`, and the aggregating runner `ci/run-gates.py`. Which languages appear here
is [keyed on that set](../rules/language-conventions-keyed-on-source.md), so Elixir and Go conventions
arrive with their source and not before — the tree's single `.ex` file is a link-gate fixture under
`ci/broken-inputs/`, a test input rather than source.

**Formatter and linters: none is pinned, and that is a gap rather than a position.** So nothing below
is layout, quoting or import order — a formatter's business. These are the project's own obligations,
each stating what holds it up; the two that are not decidable over English are quarantined as
preference rather than written here as requirements.

## Standard library only

A module under `ci/` imports from the standard library and from its siblings `_common` and `indexes`,
and from nothing else. Every import in the tree today is one of those.

**Why.** A gate with a dependency can stop running without failing, and a declared tool nobody runs
is indistinguishable from no tool. The prior art had `credo` declared and never invoked, and no
format check, Dialyzer or dependency audit on the component terminating untrusted traffic, while the
sidecar carried thirty linters ([audit](../../history/reference-audit.md), `docs/history/reference-audit.md:253`).

## Every violation in one run

A gate accumulates findings and reports all of them rather than exiting at the first: `Report.fail`
appends, `Report.finish` prints the whole list. A gate never repairs the state it inspects — write
mode belongs to the generator, whose check mode never invokes it.

**Why.** Feedback arriving one item at a time is slow, and slow feedback changes what gets written:
the prior art's own critic concluded that when feedback is slow, assertions get chosen for being
cheap to satisfy. Its suite required a live Postgres for every file, including the named test
`validate_path_test.exs`, whose subject touches no database
([reference audit](../../history/reference-audit.md), `docs/history/reference-audit.md:243`).

## Coverage stated on a passing run

A gate calls `Report.coverage` with the roots it covered and excluded, its subject count, and whether
that list came from the tracked index; `Report.finish` prints it on a passing run as on a failing one,
so a green result states its own scope rather than implying it.

**Why.** A suite green over nothing reads exactly like a suite green over everything. `reconnect.go`
— 250 lines, the sidecar's most fragile subsystem — had zero coverage, and the only test named for it
was an unconditional skip
([reference audit](../../history/reference-audit.md), `docs/history/reference-audit.md:147`).

## What a module docstring carries — preference, not obligation

Every module in the tree opens with the requirement it serves and the defect behind it, and the
narrower checks add what they do not decide. Neither is enforceable over English, so both are
quarantined as taste and neither is a blocking objection:
[the docstring habit](../rules/preferences/gate-docstring-names-requirement-and-defect.md) and
[saying what a gate does not decide](../rules/preferences/gate-states-what-it-does-not-decide.md).

## `--root` and `--report-only` on every gate

Both flags come from `_common.parse_args`, wired by `main_guard`, so no gate has its own argument
handling. `--root` runs a gate against a miniature tree under `ci/broken-inputs/`; `--report-only`
prints findings and returns zero. This one is enforced: `ci/gates/meta.py:75` invokes every gate with
`--root`, so a gate without it fails
[the demonstrated-to-fail rule](../../method/rules/gates-are-demonstrated-to-fail.md).

**Why.** A gate that cannot be pointed at a deliberately broken tree is a gate nobody has checked.
The prior art's local guardrail ran `compile --warning-as-errors` — singular, therefore inert — while
CI ran the plural at `unit_test.yml:69` ([reference audit](../../history/reference-audit.md)).

## Ceilings and the gate-naming rule

Stated once as rules, not restated here — a second copy here would be the copy that drifts: the
[module ceiling](../rules/module-size-ceiling.md), the
[function ceiling](../rules/function-size-ceiling.md), the
[duplication threshold](../rules/duplication-threshold.md), and
[the correspondence](../rules/rule-gate-correspondence.md) each gate keeps with its rule note.
