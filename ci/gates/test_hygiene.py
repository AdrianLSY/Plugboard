#!/usr/bin/env python3
"""Gate: a test says what it asserts, and a skip says why and until when.

Enforces docs/code/rules/no-uncertainty-marker-or-skip.md. rebuild-plugboard task
3.9: rejects an uncertainty marker in a test body, a skip with no linked issue,
and a new `async: false` with no stated reason.

Three cases, all three failing:

  1. AN UNCERTAINTY MARKER. Abandoned reasoning committed as a comment --
     "actually this shouldn't...", "let me think again", "for now we just...".
     The audit found these are the signature of a test written around a defect
     rather than at it, and the prior attempt carried them: hooks_test.exs:425 is
     abandoned reasoning left in the file.
  2. A SKIP WITH NO LINKED ISSUE. A skip is a deferred assertion, and one with no
     creditor is a deleted assertion wearing a temporary marker. The prior
     attempt skipped its only mount-point hook success test claiming another file
     covered it; it did not (executor_test.exs:465).
  3. `async: false` WITH NO STATED REASON. 27 of 43 files ran serial, which is
     what made the suite slow enough that assertions got chosen for being cheap
     to satisfy. Serial is sometimes right; unexplained serial is how it spreads.

## What it does not decide

Whether a stated reason is a good one, or whether a linked issue is real. Both
are review's. It decides that the question was answered somewhere a reader can
find it, which is the same property ci/gates/binary_assets.py decides about a
committed binary.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, subject_source
from _source import config, sources

GATE_ID = "test-hygiene"
RULE_NOTE = "docs/code/rules/no-uncertainty-marker-or-skip.md"

SKIP = re.compile(r"@tag\s+:skip|\bt\.Skip\w*\s*\(|\bt\.SkipNow\s*\(")
ASYNC_FALSE = re.compile(r"async:\s*false")
ISSUE = re.compile(r"https?://\S+|#\d+|[A-Z]{2,}-\d+|tasks\.md")


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = config(manifest)
    markers = [m for m in manifest["code_standards"]["test_hygiene"]["uncertainty_markers"]
               if not m.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)
    marker_re = re.compile("|".join(re.escape(m) for m in markers), re.I)

    files = [rel for rel in sources(scan_root, cfg, manifest) if "_test." in rel]
    for rel in files:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for n, line in enumerate(lines, 1):
            near = " ".join(lines[max(0, n - 3):n + 2])

            if marker_re.search(line):
                report.fail(
                    f"{rel}:{n}: an uncertainty marker in a test -- abandoned "
                    f"reasoning committed as a comment is the signature of a test "
                    f"written around a defect rather than at it"
                )
            if SKIP.search(line) and not ISSUE.search(near):
                report.fail(
                    f"{rel}:{n}: a skip with no linked issue -- a skip is a deferred "
                    f"assertion, and one with no creditor is a deleted assertion "
                    f"wearing a temporary marker"
                )
            if ASYNC_FALSE.search(line) and not _explained(lines, n):
                report.fail(
                    f"{rel}:{n}: `async: false` with no stated reason -- serial is "
                    f"sometimes right, and unexplained serial is how 27 of 43 files "
                    f"came to be serial"
                )

    report.coverage(
        covered=["tests in the declared source languages"],
        excluded=["whether a stated reason is a good one (review's)"],
        kind="test file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  test files: {len(files)} | uncertainty markers declared: {len(markers)}"
    )
    return report.finish(report_only=report_only)


def _explained(lines: list[str], n: int) -> bool:
    """A comment on the same line or the one above counts as the stated reason."""
    same = lines[n - 1]
    above = lines[n - 2] if n >= 2 else ""
    return "#" in same.split("async:")[0] + same.split("async:")[-1] or \
        above.strip().startswith("#")


main_guard(run)
