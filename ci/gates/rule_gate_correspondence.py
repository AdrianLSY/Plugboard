#!/usr/bin/env python3
"""Gate: every rule names its gate, and every gate names its rule.

Enforces docs/code-standards -- "Every rule names its gate, and every gate names
its rule", plus "Unenforced rules are quarantined".

Five cases, all five failing:

  1. A gate naming no rule note.
  2. A gate naming a rule note that does not exist.
  3. A rule note claiming a gate the repository does not run.
  4. A rule note that neither names a gate nor carries the no-gate marker.
  5. Two gates naming ONE rule note. The correspondence is one-to-one in both
     directions, so a second gate over one obligation is two enforcements that
     can disagree -- and the failure is silent, because each of them passes.
     rebuild-plugboard task 1.4 asks for exactly this assertion in its narrow
     form ("only one link gate exists in the repository"); stating it over the
     whole roster costs one dictionary and answers it for every rule.

And one more, from the quarantine requirement:

  6. An ungated rule sitting among the gated ones. An unenforced rule is not
     banned -- some genuinely are taste -- but it is held separately, marked as
     preference, and barred from being raised as a blocking objection.

## Why both directions

A one-directional check (every rule has a gate) still permits a gate nobody can
find the rule for, which is how a lint rule becomes folklore: it fires, nobody
remembers why, and the next person to trip it deletes it. Checking the other way
round costs one more loop and closes that.

The correspondence is also what makes a gate's failure the teaching surface. The
contributor who trips a check is handed the defect it prevents and the citation
for it, at the one moment they are guaranteed to be reading.

## The proportion of ungated rules is a number, not a feeling

It is printed on every run. A guide drifting toward unenforced opinion shows up
as that number rising rather than as somebody eventually noticing.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, rule_notes

GATE_ID = "rule-gate-correspondence"
RULE_NOTE = "docs/code/rules/rule-gate-correspondence.md"

from _common import RULE_NOTE_DECL  # the one declaration, shared with ci/gen

GATE_LINE = re.compile(r"^\*\*Gate:\*\*\s*(.+)$", re.M)
NO_GATE = re.compile(r"^\*\*Gate:\*\*\s*none\b", re.M | re.I)
# A third state the requirement did not anticipate, and which the banned patterns
# need: a rule that IS an obligation whose gate is not built yet. Calling it
# "none" would file an obligation as taste; claiming a gate would name one that
# does not run. So it declares itself planned and links the work that builds it,
# and the currency rule then refuses it once that gate exists.
PLANNED_GATE = re.compile(r"^\*\*Gate:\*\*\s*planned\b", re.M | re.I)

NOT_A_GATE = {"a module whose name starts with _ (a shared library)"}


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]
    quarantine = cfg["quarantine_dir"]
    report = Report(GATE_ID, RULE_NOTE)

    gates = {
        p.stem: p
        for p in sorted((scan_root / "ci" / "gates").glob("*.py"))
        if not p.stem.startswith("_")
    }
    notes = rule_notes(scan_root, cfg)

    # (1) and (2): a gate must name a rule note, and it must exist.
    claimed: dict[str, str] = {}
    for stem, path in gates.items():
        m = RULE_NOTE_DECL.search(path.read_text(encoding="utf-8"))
        if not m:
            report.fail(
                f"ci/gates/{stem}.py: names no rule note -- a gate whose rule "
                f"nobody can find becomes folklore the next contributor deletes"
            )
            continue
        rel = m.group(1).split("#")[0]
        claimed[stem] = rel
        if rel not in notes:
            report.fail(
                f"ci/gates/{stem}.py: names rule note '{rel}', which does not exist"
            )

    # (5) one rule, one gate -- the direction a per-gate loop cannot see.
    owners: dict[str, list[str]] = {}
    for stem, rel in claimed.items():
        owners.setdefault(rel, []).append(stem)
    for rel, stems in sorted(owners.items()):
        if len(stems) > 1:
            report.fail(
                f"{rel}: named by {len(stems)} gates ("
                + ", ".join(f"ci/gates/{s}.py" for s in sorted(stems))
                + ") -- the correspondence is one-to-one, and two gates over one "
                "obligation is two enforcements that can disagree while both pass"
            )

    # (3), (4) and (6): the note's side of the correspondence.
    gated = ungated = planned = 0
    for rel, path in sorted(notes.items()):
        text = path.read_text(encoding="utf-8")
        m = GATE_LINE.search(text)
        if not m:
            report.fail(
                f"{rel}: names neither a gate nor the no-gate marker -- a rule "
                f"whose enforcement is unstated reads as an obligation either way"
            )
            continue
        if PLANNED_GATE.search(text):
            planned += 1
            if "status: planned" not in text:
                report.fail(
                    f"{rel}: declares a planned gate but is not marked "
                    f"status: planned -- a rule whose enforcement does not exist "
                    f"yet describes a planned artifact"
                )
            if "tasks.md" not in text:
                report.fail(
                    f"{rel}: declares a planned gate and links no work that "
                    f"builds it -- a planned marker names its subject or it is "
                    f"an obligation with no route to enforcement"
                )
            continue
        if NO_GATE.search(text):
            ungated += 1
            if not rel.startswith(quarantine.rstrip("/") + "/"):
                report.fail(
                    f"{rel}: carries no gate but sits among the gated rules -- "
                    f"an unenforced rule belongs under {quarantine} so that a "
                    f"preference is distinguishable from an obligation without "
                    f"reading either note"
                )
            continue
        gated += 1
        named = re.findall(r"`ci/gates/([a-z_]+)\.py`", m.group(1))
        if not named:
            report.fail(
                f"{rel}: its Gate line names no runnable gate path "
                f"(expected `ci/gates/<name>.py` or 'none')"
            )
        for stem in named:
            if stem not in gates:
                report.fail(
                    f"{rel}: claims gate 'ci/gates/{stem}.py', which the "
                    f"repository does not run"
                )
        # A gated rule in the quarantine is the inverse mistake.
        if rel.startswith(quarantine.rstrip("/") + "/"):
            report.fail(
                f"{rel}: names a gate but sits in the quarantine, which is for "
                f"unenforced preference only"
            )

    total = gated + ungated + planned
    pct = (100 * ungated // total) if total else 0
    for _subject in notes:
        report.examine(_subject)
    report.coverage(
        covered=[*cfg["rule_dirs"], "ci/gates"],
        excluded=sorted(NOT_A_GATE),
        kind="rule note",
        source="scan",
        scan_root=scan_root,
    )
    print(
        f"  gates: {len(gates)} | rule notes: {total} "
        f"({gated} gated, {planned} gate planned, {ungated} unenforced = {pct}%)"
    )
    return report.finish(report_only=report_only)


main_guard(run)
