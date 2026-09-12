---
type: rule
status: current
authority: rationale
---

# Every rule names its gate, and every gate names its rule

**Gate:** `ci/gates/rule_gate_correspondence.py`

Each rule is stated in exactly one rule note, and that note names the gate enforcing it or carries
the no-gate marker. Each gate names the rule note it enforces, and its failure output identifies
that note. The correspondence is checked in both directions, and it is **one-to-one**: two gates
naming one rule note fails, because one obligation with two enforcements is two checks that can
disagree while each of them reports a pass. That is also the general form of "only one link gate
exists in the repository", which
[rebuild-plugboard task 1.4](../../../openspec/changes/rebuild-plugboard/tasks.md) asks for.

## Why

A one-directional check — every rule has a gate — still permits a gate nobody can find the rule for.
That is how a lint rule becomes folklore: it fires, nobody remembers why, and the next person to trip
it deletes it. Checking the other way costs one more loop and closes it.

The correspondence is also what makes a failure the teaching surface: the contributor who trips a
check is handed the defect it prevents, at the one moment they are certainly reading.

Ungated rules are not banned — some genuinely are taste. They are held in
[the quarantine](preferences/), marked as preference, barred from being raised as blocking
objections, and counted, so a guide drifting toward unenforced opinion is a number rather than a
feeling.
