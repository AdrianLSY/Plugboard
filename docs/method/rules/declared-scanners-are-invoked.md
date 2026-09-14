---
type: rule
status: current
authority: rationale
---

# A declared scanner is invoked where the runner executes, not where a reader looks

**Gate:** `ci/gates/security_scan.py`

Every scanner `ci/vault.json` declares appears in a position the runner **executes** — a step's `run:`
body or its `uses:` reference — with the settings that make it refuse rather than report, on every
trigger the declaration names including the weekly one.

## Why the position matters more than the name

An earlier version of this gate matched a scanner's name anywhere in its step, `name:` included. A
workflow whose four steps read `- name: govulncheck ./... (disabled while we triage)` above
`run: echo skipping` satisfied it, and it printed *scanners invoked: 4 of 4*. It was reverted before
it reached `main`. A scanner named in prose is a scanner nobody ran, and a gate that cannot tell the
difference is worse than no gate, because it reports the reassurance without the scan.

## Why the schedule is not optional

A vulnerability is published against code that has not changed. A scan bound only to push and pull
request finds it when somebody next happens to edit a file, which may be never — the dependency that
is most at risk is the one nobody is touching.

## What it does not decide

Whether a scan finds anything, whether `HIGH,CRITICAL` is the right floor, or whether a finding was
triaged. Nor path filters, branch filters or `continue-on-error`, which belong to
[the runner rule](the-gates-actually-run.md) and are checked against
`ci/vault.json`'s `runner.forbidden_clauses` — this workflow is declared there, so it is covered.
