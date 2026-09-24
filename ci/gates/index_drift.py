#!/usr/bin/env python3
"""Gate: a generated index is tracked, declares its tool, and cannot drift.

Enforces docs/knowledge-base -- "Generated indexes are checked in and cannot
drift":

  * an index derived from other notes must be tracked, so a reader who never
    runs the generator still sees it;
  * it must be byte-identical to a fresh regeneration, so a note changed without
    a regeneration fails rather than leaving the index quietly wrong;
  * it must declare that it is generated and name the tool that produces it, so
    the failure hands over a command instead of a verdict;
  * a hand edit is detected as drift rather than silently overwritten -- this
    gate never writes, and the generator writes only when invoked in write mode.

The concrete defect this shape exists to prevent: a check that regenerates over
the working tree and then compares finds nothing, because the comparison is
against what it just wrote. So the regeneration here happens in memory, the
subject is the tracked bytes, and the two are never the same object. The related
defect is a gate that keeps its own copy of the expected output; this one calls
ci/gen/indexes.py's `check`, so the expectation the gate enforces is by
construction the one the generator a contributor is told to run produces.

Every index is reported in one run. A missing index and a hand-edited index are
both findings of the same pass, and a passing run states which roots it covered.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _common import Report, load_manifest, main_guard, on_tracked_tree, repo_root

# ci/gen is the generator's home and is not a package; the gate invokes the
# generator rather than duplicating its renderer, so it reproduces the one
# sys.path entry a direct `python3 ci/gen/indexes.py` run would already have.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gen"))

import indexes  # noqa: E402

GATE_ID = "index-drift"
RULE_NOTE = "docs/method/rules/index-drift.md"

#: One line per finding kind, so the message a contributor reads names the
#: obligation rather than the mechanism that noticed it.
EXPLANATION = {
    "missing": "not tracked",
    "drift": "drifted from its source notes",
    "undeclared": "missing its generated-by declaration",
    "unowned": "generated index with no subject directory",
}

#: Every failure names the tool, because the requirement is that a generated
#: index name the tool that produces it and a failure that withholds it leaves
#: the contributor to guess. The remedy is per-kind: regenerating fixes three of
#: the four, and telling someone to regenerate a path the tool does not produce
#: sends them in a circle.
_REGENERATE = (
    f"regenerate with `python3 {indexes.GENERATOR} --write` and commit the result"
)
REMEDY = {
    "missing": _REGENERATE,
    "drift": _REGENERATE,
    "undeclared": _REGENERATE,
    "unowned": f"{indexes.GENERATOR} does not produce this path -- delete it, "
    f"or restore the notes it was generated from",
}


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    report = Report(GATE_ID, RULE_NOTE)

    # Read-only by contract: `check` regenerates into memory and compares. The
    # gate must never leave a regenerated index behind in the tree it inspects.
    findings, expected, from_index = indexes.check(scan_root, manifest)

    for finding in findings:
        where = f":{finding.line}" if finding.line else ""
        report.fail(
            f"{finding.path}{where}: {EXPLANATION[finding.kind]} -- {finding.detail}; "
            f"{REMEDY[finding.kind]}"
        )

    print(
        f"  generator: {indexes.GENERATOR} | spine: {manifest['spine']} | "
        f"indexes expected: {len(expected)}"
    )
    # Generated files outside the per-directory scheme, each verified by running
    # its own declared tool in check mode. Declared rather than discovered so a
    # new generator cannot become the one nothing checks.
    # Scoped to the run against the tracked tree. A fixture tree carries only the
    # notes its own case needs and no ci/ directory at all, so checking a
    # declared generator's existence against one reports two failures that are
    # artifacts of the fixture being partial rather than of the rule -- which is
    # what made this fixture emit six violations against the four it states.
    on_tracked = on_tracked_tree(scan_root)
    import subprocess as _sp

    extra = (
        {
            k: v
            for k, v in manifest.get("generated_files", {}).items()
            if not k.startswith("_")
        }
        if on_tracked
        else {}
    )
    for rel, tool in sorted(extra.items()):
        tool_path = scan_root / tool
        if not tool_path.is_file():
            report.fail(f"{rel}: declares generator {tool}, which does not exist")
            continue
        proc = _sp.run(
            ["python3", str(tool_path)],
            capture_output=True,
            text=True,
            cwd=str(scan_root),
        )
        if proc.returncode != 0:
            report.fail(
                f"{rel}: differs from a fresh regeneration -- regenerate with "
                f"`python3 {tool} --write` and commit the result"
            )

    # The count is what this run actually compared: the per-directory indexes
    # PLUS every declared generated artifact. It reported only the former, so a
    # passing run named thirteen subjects while checking fifteen -- a coverage
    # line understating its own reach is the same defect as one overstating it.
    for _subject in [*expected, *extra]:
        report.examine(_subject)
    report.coverage(
        covered=[*sorted(expected), *sorted(extra)],
        excluded=[
            *(r for r in manifest.get("exempt_roots", {}) if not r.startswith("_")),
            *(r for r in manifest.get("scan_excludes", {}) if not r.startswith("_")),
        ],
        kind="index file",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )

    return report.finish(report_only=report_only)


main_guard(run)
