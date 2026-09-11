---
type: rule
status: current
authority: rationale
---

# A violating input states the failure it produces

**Gate:** `ci/gates/fixture_declarations.py`

Each violating tree carries a machine-readable declaration beside it: the violation count, and one
expectation per case its note claims, each required to match a failure the gate emits. Prose in the
note is not read as that declaration. A count that disagrees, or a case that matches nothing, fails.
An input may additionally declare invocations of its own gate with the exit status each expects, and
every declared invocation is performed; a flag the note demonstrates and the declaration omits fails.

## Why

[`ci/gates/meta.py`](../../../ci/gates/meta.py) proves each gate fails on its own violating input, and
never reads what the fixture claims that failure is. Of the eleven notes stating a count in prose,
four were wrong — and two of the four were not wrong numbers but defects the numbers were hiding.
[`currency`](../../../ci/broken-inputs/currency/GATE.md) exercises four properties and only three
fired: the fourth, a note still marked planned whose linked task is complete, had stopped matching
because the fixture wrote the task id in prose where the gate reads it from the link label. The
property that gate exists for was undemonstrated while the fixture kept failing on the other three,
so nothing noticed.

The unit is the tree rather than the directory, because one gate may need more than one scenario and
a declaration keyed on the directory cannot say what each emits. An invocation declares an exit status
and never a count: a self-test builds its own scenario in a temporary repository, so how it exited is
the only thing an outside observer can assert about it.

The gate's failure output names this note, so tripping it hands you the rule rather than a verdict.

> Orientation, not behaviour. Where this note and a specification disagree, the specification wins.
