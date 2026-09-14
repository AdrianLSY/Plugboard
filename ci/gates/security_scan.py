#!/usr/bin/env python3
"""Gate: every declared scanner is actually invoked, in a position that executes.

Enforces docs/method/rules/declared-scanners-are-invoked.md. rebuild-plugboard
task 3.4.

## The defect this shape exists to prevent, because it already happened here

An earlier version of this gate matched a scanner's name as a substring of the
whole step block -- `name:` included. A workflow whose four steps read
`- name: govulncheck ./... (disabled while we triage)` / `run: echo skipping`
satisfied it, and it reported `scanners invoked: 4 of 4`. That version was
reverted. This one reads ONLY the positions that execute: a step's `run:` body and
its `uses:` reference. A scanner named in prose is a scanner nobody ran.

Three cases, all three failing:

  1. A declared scanner absent from every executable position in the workflow.
  2. A required setting absent from the step that invokes its scanner -- the
     severity floor and the non-zero exit are the whole of what makes a scan a
     refusal rather than a report.
  3. A declared trigger the workflow does not carry. The weekly one is the point:
     a vulnerability is published against code that has not changed, so a scan
     that runs only on change finds it only when somebody happens to edit a file.

## What this gate does NOT decide

Whether the workflow carries a path or branch filter, or `continue-on-error`.
That is ci/gates/runner.py's, against ci/vault.json's runner.forbidden_clauses,
and this file is declared in runner.workflows so it is covered there. Saying so
matters: the reverted version's own header claimed it checked filters and it did
not, which is the exact shape of a comment standing in for enforcement.

Nor whether a scan FINDS anything, whether HIGH,CRITICAL is the right floor, or
whether a finding was triaged. Those are the operator's.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "security-scan"
RULE_NOTE = "docs/method/rules/declared-scanners-are-invoked.md"

STEP = re.compile(r"^\s*-\s", re.M)


def executable_text(body: str) -> str:
    """Only what a runner executes: `run:` bodies and `uses:` references.

    A step's `name:` is prose. Reading it is how the reverted version of this gate
    came to report four scanners invoked by a workflow that ran `echo skipping`
    four times.
    """
    out: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)(?:-\s+)?(run|uses|with)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        indent, key, rest = len(m.group(1)), m.group(2), m.group(3)
        out.append(rest)
        if key in ("run", "with") and rest.strip() in ("|", ">", "", "|-", ">-"):
            i += 1
            while i < len(lines) and (not lines[i].strip() or
                                      len(lines[i]) - len(lines[i].lstrip()) > indent):
                out.append(lines[i])
                i += 1
            continue
        i += 1
    return "\n".join(out)


def triggers(body: str) -> set[str]:
    m = re.search(r"^on:\s*$(.*?)(?=^\S)", body, re.M | re.S)
    if m:
        return set(re.findall(r"^\s+([a-z_]+)\s*:", m.group(1), re.M))
    m = re.search(r"^on:\s*(.+?)\s*$", body, re.M)
    if not m:
        return set()
    rest = m.group(1)
    if rest.startswith("["):
        return {t.strip().strip("'\"") for t in rest.strip("[]").split(",") if t.strip()}
    return {rest.strip()}


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["security_scan"]
    rel = cfg["workflow"]
    scanners = {k: v for k, v in cfg["scanners"].items() if not k.startswith("_")}
    required_triggers = [t for t in cfg["required_triggers"] if not t.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)

    path = scan_root / rel
    if not path.is_file():
        report.fail(
            f"{rel}: the security workflow ci/vault.json declares is absent, so "
            f"nothing scans either side on any trigger"
        )
        report.coverage(covered=[], excluded=[], kind="declared scanner",
                        source="manifest", scan_root=scan_root)
        return report.finish(report_only=report_only)

    body = path.read_text(encoding="utf-8")
    runs = executable_text(body)
    invoked = 0

    for name, spec in sorted(scanners.items()):
        report.examine(name)
        if spec["invocation"] not in runs:
            report.fail(
                f"{rel}: declares the {spec['side']} scanner `{name}` and no step "
                f"EXECUTES `{spec['invocation']}` -- a scanner named in a step's "
                f"`name:` is a scanner nobody ran, which is how an earlier version "
                f"of this gate reported four of four against `echo skipping`"
            )
            continue
        invoked += 1
        for setting in spec.get("required_settings", []):
            if setting not in runs:
                report.fail(
                    f"{rel}: `{name}` is invoked without `{setting}` -- the severity "
                    f"floor and the non-zero exit are what make a scan a refusal "
                    f"rather than a report"
                )

    present = triggers(body)
    for want in required_triggers:
        if want not in present:
            report.fail(
                f"{rel}: does not trigger on `{want}` -- a vulnerability is "
                f"published against code that has not changed, so a scan that runs "
                f"only on change finds it only when somebody edits a file"
            )

    report.coverage(
        covered=sorted(scanners),
        excluded=[
            "path, branch and continue-on-error clauses (ci/gates/runner.py, "
            "against runner.forbidden_clauses -- this workflow is declared there)",
            "whether a scan finds anything, and whether the severity floor is right",
        ],
        kind="declared scanner",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  scanners invoked: {invoked} of {len(scanners)} | triggers required: "
          f"{', '.join(required_triggers)}")
    return report.finish(report_only=report_only)


main_guard(run)
