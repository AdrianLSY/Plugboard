#!/usr/bin/env python3
"""Gate: the gating-test registry is honest about what it records.

Enforces rebuild-plugboard task 4.5. ci/expected-outcomes.py runs the gating
tests and compares each outcome to the recorded one. This gate checks the RECORD
itself, and it runs inside `make check` because it starts no process: a gate that
ran end-to-end tests would put a chain of processes inside the command a
contributor runs on every commit.

Four cases, all four failing:

  1. A RED entry naming no closing task. A red gate is a DEBT, and a debt with no
     named creditor is a permanent exemption wearing a temporary one's clothes.
  2. A closing task that does not exist in the task list it names. The id is
     resolved against THAT list, not against every list in the repository: two
     changes in flight carry overlapping identifiers, and an unscoped read clears
     a marker against the wrong one.
  3. An entry naming a test no source declares. A registry row for a test nobody
     wrote records an outcome that was never measured.
  4. An outcome outside the closed set. `red` and `green` are the two things a
     run can be; anything else is a note somebody left in a field a check reads.

## Why the record needs its own gate

The runner can only compare what it is given. A registry that names a test that
does not exist reports nothing about it and exits zero, which reads exactly like
a clean run -- the same shape as a suite green over an empty subject set. So the
record is checked against the tree, and the tree against the record.

## What it does not decide

Whether a recorded outcome is the RIGHT one; that is ci/expected-outcomes.py's,
and it decides it by running the test. Nor whether the closing task is the task
that will actually close it, which no check can know.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from _common import Report, main_guard

GATE_ID = "expected-outcomes"
RULE_NOTE = "docs/code/rules/a-red-gate-is-a-recorded-debt.md"

REGISTRY = "ci/expected-outcomes.json"
OUTCOMES = {"red", "green"}
CLOSED_BY = re.compile(r"(\S+tasks\.md)\s+task\s+(\d+\.\d+[a-z]?)")


def task_exists(root: Path, rel: str, task_id: str) -> bool:
    path = root / rel
    if not path.is_file():
        return False
    pattern = re.compile(rf"^- \[[ x]\] {re.escape(task_id)}\s")
    return any(pattern.match(line) for line in path.read_text(encoding="utf-8").splitlines())


def test_declared(root: Path, pkg: str, name: str) -> bool:
    directory = root / pkg
    if not directory.is_dir():
        return False
    needle = re.compile(rf"^func {re.escape(name)}\s*\(", re.M)
    return any(
        needle.search(p.read_text(encoding="utf-8", errors="replace"))
        for p in directory.glob("*.go")
    )


def run(scan_root: Path, report_only: bool) -> int:
    report = Report(GATE_ID, RULE_NOTE)
    path = scan_root / REGISTRY

    if not path.is_file():
        report.fail(
            f"{REGISTRY}: absent -- the gating tests then have no recorded "
            f"baseline, so a permanently red one makes every change unmergeable "
            f"and a gate that closes goes unnoticed"
        )
        report.coverage(covered=[], excluded=[], kind="recorded gate",
                        source="manifest", scan_root=scan_root)
        return report.finish(report_only=report_only)

    try:
        entries = json.loads(path.read_text(encoding="utf-8")).get("gates", {})
    except json.JSONDecodeError as exc:
        report.fail(f"{REGISTRY}: not valid JSON ({exc.msg})")
        report.coverage(covered=[], excluded=[], kind="recorded gate",
                        source="manifest", scan_root=scan_root)
        return report.finish(report_only=report_only)

    reds = 0
    for key, entry in sorted(e for e in entries.items() if not e[0].startswith("_")):
        report.examine(key)
        pkg, _, name = key.partition(":")
        outcome = (entry or {}).get("outcome")

        # (4) the closed set.
        if outcome not in OUTCOMES:
            report.fail(
                f"{REGISTRY}: '{key}' records outcome {outcome!r}, and a run is "
                f"one of {sorted(OUTCOMES)} -- anything else is a note left in a "
                f"field a check reads"
            )
        if outcome == "red":
            reds += 1
            closed_by = (entry or {}).get("closed_by", "")
            m = CLOSED_BY.search(closed_by or "")
            # (1) a debt with no named creditor.
            if not m:
                report.fail(
                    f"{REGISTRY}: '{key}' is recorded red and names no closing task "
                    f"-- a red gate is a debt, and one with no creditor is permanent"
                )
            # (2) a creditor that does not exist.
            elif not task_exists(scan_root, m.group(1), m.group(2)):
                report.fail(
                    f"{REGISTRY}: '{key}' is closed by task {m.group(2)} of "
                    f"{m.group(1)}, and that list holds no such task"
                )

        # (3) a row about a test nobody wrote.
        if not test_declared(scan_root, pkg, name):
            report.fail(
                f"{REGISTRY}: '{key}' names a test no source in {pkg}/ declares -- "
                f"the runner then reports nothing about it and exits zero, which "
                f"reads exactly like a clean run"
            )

    report.coverage(
        covered=[REGISTRY],
        excluded=["whether a recorded outcome is the right one (the runner decides that, by running it)"],
        kind="recorded gate",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  recorded gates: {len(entries)} | red (a debt with a named closer): {reds}")
    return report.finish(report_only=report_only)


main_guard(run)
