# Violating input: rule-gate-correspondence

- **Gate:** `ci/gates/rule_gate_correspondence.py` (`rule_gate_correspondence`)
- **Rule note:** `docs/code/rules/rule-gate-correspondence.md`
- **Requirement:** `docs/code-standards` — "Every rule names its gate, and every gate names its
  rule", plus "Unenforced rules are quarantined".

## Violations, one per enumerated case

1. `ci/gates/nameless.py` names no rule note.
2. `ci/gates/dangling.py` names a rule note that does not exist.
3. `docs/method/rules/claims-absent-gate.md` claims a gate the repository does not run.
4. `docs/method/rules/no-marker.md` names neither a gate nor a marker.
5. `docs/method/rules/ungated-outside-quarantine.md` carries no gate but sits among the gated rules.
6. `docs/code/rules/preferences/gated-in-quarantine.md` names a gate but sits in the quarantine —
   the inverse mistake.
7. `docs/code/banned-patterns/planned-without-status.md` declares a planned gate without
   `status: planned`, i.e. an obligation with no route to enforcement and no marker saying so.

## Expected

Exit 1 with **eight violations across seven cases**, each naming the file and what it should have
said.

Stated as seven until `harden-vault-harness` task 2.2 remeasured it, and the discrepancy is not
drift — it is cases counted as lines. `docs/code/banned-patterns/planned-without-status.md` trips two
checks from one defect: it declares a planned gate without the `status: planned` marker *and* without
linking the work that builds it. Seven cases, eight failure lines. The distinction matters because a
count is what a run emits while a case is what this note claims, and a declaration that conflates
them cannot be checked against either.
