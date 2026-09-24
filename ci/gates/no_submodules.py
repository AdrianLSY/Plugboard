#!/usr/bin/env python3
"""Gate: one repository -- no .gitmodules, and no path recorded as a gitlink.

Enforces [D22](docs/decisions/d22-one-repository.md), which says a CI guard keeps
submodules out "rather than trusting anyone to remember". Until this module
existed that sentence was in the present tense and nothing performed it.

Two cases, both failing:

  1. `.gitmodules` at the root of the tree. Git reads the file only there, so
     that is the only place this looks -- a file of that name deeper in the tree
     configures nothing, and one lives under ci/broken-inputs/ as this gate's own
     violating input.

  2. A tracked path recorded with mode 160000. That is the entry a submodule
     leaves behind, and it is what actually pins a foreign revision: a gitlink
     survives `.gitmodules` being deleted, and a checkout then silently carries a
     commit nobody in this repository reviewed.

Both are needed because either alone is removable without the other. The defect
being prevented is specific: the prior art was two repositories joined by
submodules, with a sync workflow that auto-committed a pointer update onto the
parent's default branch on every push to the sidecar's -- so a protocol change
reached the parent's main with no review at all.

## What it cannot see off a work tree

Mode 160000 is recorded in the version-control index, so a run pointed at a
violating input -- a directory, not a repository -- can decide case 1 and not
case 2. The run says which of the two it decided rather than reporting a clean
result it did not earn. The gitlink half is demonstrated on a scratch branch
instead, which is what rebuild-plugboard task 1.2 asks for.

## What it does not decide

Vendoring by any other means. A copied directory, a package manager's lockfile
pointing at a fork, or a build step that clones at run time are all outside this
check and outside D22's words. The one-repository property this holds is git's,
not the supply chain's -- ci/gates is not where that is owned.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from _common import Report, _in_worktree, main_guard, subject_source

GATE_ID = "no-submodules"
RULE_NOTE = "docs/code/rules/no-submodules.md"

GITLINK_MODE = "160000"
MODULES_FILE = ".gitmodules"


def _index_entries(scan_root: Path) -> list[tuple[str, str]] | None:
    """(mode, path) for every tracked entry, or None when this is not a work tree."""
    if not _in_worktree(scan_root):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(scan_root), "ls-files", "-s", "-z"],
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    entries = []
    for record in out.split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        entries.append((meta.split(" ", 1)[0], path))
    return entries


def _walked(scan_root: Path) -> list[str]:
    """Every file under `scan_root`, relative and sorted. Violating inputs only."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        rel_dir = Path(dirpath).relative_to(scan_root)
        for name in sorted(filenames):
            found.append((rel_dir / name).as_posix())
    return sorted(found)


def run(scan_root: Path, report_only: bool) -> int:
    report = Report(GATE_ID, RULE_NOTE)
    entries = _index_entries(scan_root)
    paths = [p for _mode, p in entries] if entries is not None else _walked(scan_root)

    for path in paths:
        report.examine(path)

    # (1) the declaration file, at the only place git reads it.
    if (scan_root / MODULES_FILE).is_file():
        report.fail(
            f"{MODULES_FILE}: a submodule declaration at the root of the tree -- "
            f"D22 puts every component in one repository, because the two it "
            f"replaces were joined by a sync workflow that auto-committed "
            f"unreviewed pointer updates onto the parent's default branch"
        )

    # (2) the entry that actually pins a foreign revision.
    gitlinks = (
        [p for mode, p in entries if mode == GITLINK_MODE]
        if entries is not None
        else []
    )
    for path in gitlinks:
        report.fail(
            f"{path}: recorded as a gitlink (mode {GITLINK_MODE}) -- this pins a "
            f"commit from another repository and survives {MODULES_FILE} being "
            f"deleted, so removing the declaration alone does not remove the "
            f"submodule"
        )

    decided = (
        "both cases"
        if entries is not None
        else f"case 1 only ({MODULES_FILE}); mode {GITLINK_MODE} is recorded in "
        f"the index and this run has none"
    )
    report.coverage(
        covered=[f"{MODULES_FILE} at the tree root", f"mode {GITLINK_MODE} entries"],
        excluded=["vendoring by any means other than git"],
        kind="tracked path",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  paths: {len(paths)} | gitlinks: {len(gitlinks)} | "
        f"{MODULES_FILE} at root: {'present' if (scan_root / MODULES_FILE).is_file() else 'absent'} "
        f"| decided: {decided}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
