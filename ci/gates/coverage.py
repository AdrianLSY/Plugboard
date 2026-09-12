#!/usr/bin/env python3
"""Gate: a coverage line is an assertion about the run, not narrative.

Enforces docs/code-standards -- "A gate's reported coverage is an assertion
about the run". Every gate prints, on every run including a passing one, how
many subjects it examined, what kind of item it counted, and where the set came
from. Before this gate, nothing read any of it.

Four cases, all four failing:

  1. A gate whose coverage line is absent or unparseable. A passing run that
     says nothing about its reach is the state every gate was in before the
     coverage line existed.
  2. A gate reporting version control as its source on a run whose scan root is
     not a work tree. This is the one half of the source claim decidable without
     an oracle, and five gates were making it.
  3. A gate whose failure messages name more distinct subjects than its reported
     count. A gate that fails about an item its count excludes has examined a
     subject it did not report.
  4. A gate examining no subjects with no declaration recording why -- and a
     declaration whose named work is complete while the set is still empty, so
     an exemption cannot outlive its reason.

## Why the subject is each gate's own output

The alternative is to inspect each module's source for a coverage call, which
proves the call exists and nothing about what it prints. The history here is a
gate that reported "0 citations checked" while exiting zero: the call was
present, correct in shape, and the run examined nothing. So the subject is the
line the run actually emits.

## Scope

The gates declared blocking in ci/vault.json, each invoked against the tree
this gate was pointed at. A gate-shaped module under a declared scan exclusion
is a fixture, not a gate, and is not invoked.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "coverage"
RULE_NOTE = "docs/method/rules/coverage-is-an-assertion.md"

# The kind noun admits a hyphen: "top-level directory" is a kind, and a pattern
# that refused one reported the line as UNPARSEABLE -- a failure naming the wrong
# defect, since the line stated its count, its kind and its source correctly.
COVERAGE = re.compile(
    r"^\s*coverage: (\d+) ([a-z][a-z -]*?)s? from "
    r"(tracked index|a directory scan|a declared key in ci/vault\.json)\b"
)
FAILURE = re.compile(r"^\s*- ([^\s:]+)")
SELF = {"_common", GATE_ID}


def gate_modules(root: Path) -> dict[str, Path]:
    return {
        p.stem: p
        for p in sorted((root / "ci" / "gates").glob("*.py"))
        if p.stem not in SELF
    }


def run_gate(module: Path, tree: Path) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, str(module), "--root", str(tree)],
        capture_output=True,
        text=True,
        cwd=str(tree),
    )
    return done.returncode, done.stdout + done.stderr


def task_complete(root: Path, ends_with: str) -> bool:
    """Whether the work a vacuity declaration names is already done."""
    m = re.match(r"(\S+?tasks\.md)\s+task\s+(\d+\.\d+[a-z]?)", ends_with)
    if not m:
        return False
    path, task_id = root / m.group(1), m.group(2)
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(rf"\s*- \[(.)\] {re.escape(task_id)}\b", line):
            return re.match(rf"\s*- \[(.)\]", line).group(1) == "x"
    return False


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    declared_vacuity = manifest["gate_policy"].get("declared_vacuity", {})
    report = Report(GATE_ID, RULE_NOTE)

    modules = gate_modules(scan_root)
    for name, module in modules.items():
        code, output = run_gate(module, scan_root)
        report.examine(name)

        line = next((l for l in output.splitlines() if l.lstrip().startswith("coverage:")), None)
        if line is None:
            report.fail(
                f"ci/gates/{name}.py: prints no coverage line -- a run that says "
                f"nothing about its reach cannot be told from one that examined nothing"
            )
            continue
        m = COVERAGE.match(line)
        if not m:
            report.fail(
                f"ci/gates/{name}.py: coverage line is unparseable ({line.strip()!r}) "
                f"-- it must state a count, the kind of item counted, and the source"
            )
            continue
        count, _kind, source = int(m.group(1)), m.group(2), m.group(3)

        # (2) a source the run cannot have used.
        if source == "tracked index" and not (scan_root / ".git").exists():
            report.fail(
                f"ci/gates/{name}.py: reports the tracked index as its source on a "
                f"tree that is not a work tree -- the coverage line names a source "
                f"the run did not use"
            )

        # (3) a failure about a subject the count excludes.
        named = {
            mm.group(1).split(":")[0]
            for mm in (FAILURE.match(l) for l in output.splitlines())
            if mm
        }
        if len(named) > count:
            report.fail(
                f"ci/gates/{name}.py: reports {count} subject(s) and its failures name "
                f"{len(named)} distinct one(s) -- it examined a subject it did not "
                f"report ({', '.join(sorted(named)[:4])})"
            )

        # (4) an empty subject set, declared or not.
        gate_id = name.replace("_", "-")
        if count == 0:
            declaration = declared_vacuity.get(gate_id)
            if not declaration:
                report.fail(
                    f"ci/gates/{name}.py: examined no subjects and ci/vault.json's "
                    f"gate_policy.declared_vacuity records no reason -- an undeclared "
                    f"empty subject set is a check that has quietly stopped checking"
                )
            elif not (declaration.get("reason") and declaration.get("ends_with")):
                report.fail(
                    f"ci/gates/{name}.py: declared vacuity needs both 'reason' and "
                    f"'ends_with' -- a declaration with no ending condition is a "
                    f"permanent exemption"
                )
            elif task_complete(scan_root, declaration["ends_with"]):
                report.fail(
                    f"ci/gates/{name}.py: examined no subjects, and the work its "
                    f"declaration names ({declaration['ends_with']}) is complete -- "
                    f"the declaration has outlived its reason"
                )

    report.coverage(
        covered=sorted(modules),
        excluded=sorted(SELF),
        kind="gate",
        source="scan",
        scan_root=scan_root,
    )
    print(f"  gates inspected: {len(modules)} | declared vacuities: "
          f"{len([k for k in declared_vacuity if not k.startswith('_')])}")
    return report.finish(report_only=report_only)


main_guard(run)
