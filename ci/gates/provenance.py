#!/usr/bin/env python3
"""Gate: build provenance is derived in one place, and nowhere else.

Enforces docs/code/rules/build-provenance-from-one-place.md. rebuild-plugboard
task 3.13.

## Why the first attempt at this gate was worthless, and what is different

It matched the git commands as plain substrings against whole files. The exact
spelling `ci/stamp.py` used defeated it -- `_git("rev-parse", "HEAD")` never
contains the string `git rev-parse` -- so it passed over the tree it governed.
Patching its matching back to the form a reviewer had already condemned left
every fixture still green, which is the tell: nothing was pinned to the repair.

The second attempt, in this file's own first draft, repeated it. Declaring
`git rev-parse` and friends as `derives_with` failed the one place immediately,
for the same reason.

So the subject is not a command spelling. It is EXECUTION. A component that
derives its own provenance has to run a subprocess -- there is no other route
from Go, Elixir or make to git -- and that is a property of a handful of
language primitives that do not get respelled. Comments and doc strings are
stripped first, because every subject file in this tree mentions git in prose
while none of them runs it, and a gate that cannot tell those apart is a gate
nobody can leave switched on.

Three directions, which is what pins it:

  1. A subject file that executes anything fails, naming the primitive. Two
     derivations drift apart while each looks self-consistent.
  2. The one place that has STOPPED deriving fails. Move the computation out and
     this gate goes red, so the arrangement cannot be quietly dismantled. The
     previous version could not detect this at all.
  3. A build file that never calls the one place fails. A stamp nothing
     generates is reported empty, which at startup reads exactly like a binary
     that was never stamped.

## What it does not decide

Whether the reported values are RIGHT -- ci/provenance-check.py runs each of the
four components and compares against git read independently. Whether a released
artifact carries the stamp: task 70.7's. Whether a configuration item collides
with a provenance field: needs the schema task 5.2 builds, and is named there
rather than faked here.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "provenance"
RULE_NOTE = "docs/code/rules/build-provenance-from-one-place.md"


def strip_prose(text: str, suffix: str) -> str:
    """Comments and doc strings removed, so only what RUNS is left.

    Every subject file in this tree mentions git in prose and none of them runs
    it. Stripping cannot open a hole: a derivation hidden behind a comment
    marker is a comment, and does not derive anything.
    """
    if suffix == ".go":
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        return re.sub(r"//[^\n]*", "", text)
    if suffix in (".ex", ".exs"):
        text = re.sub(r'"""(?:.|\n)*?"""', "", text)
        return re.sub(r"#[^\n]*", "", text)
    return re.sub(r"#[^\n]*", "", text)


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["provenance"]
    one_place = cfg["one_place"]
    fields = [f for f in cfg["fields"] if not f.startswith("_")]
    derives = [m for m in cfg["one_place_markers"] if not m.startswith("_")]
    forbidden = [m for m in cfg["executes"] if not m.startswith("_")]
    subjects = [s for s in cfg["subject_files"] if not s.startswith("_")]
    calls = {k: v for k, v in cfg["called_as"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)

    # (2) The one place still derives it.
    source = scan_root / one_place
    report.examine(one_place)
    if not source.is_file():
        report.fail(
            f"{one_place}: the one place provenance is derived is absent, so "
            f"every component either carries no stamp or has grown its own"
        )
    else:
        body = strip_prose(source.read_text(encoding="utf-8"), source.suffix)
        gone = [m for m in derives if m not in body] + [f for f in fields if f not in body]
        if gone:
            report.fail(
                f"{one_place}: no longer derives {', '.join(sorted(gone))} -- the "
                f"computation has left the one place, which is the arrangement "
                f"this gate exists to hold. Moving it back is the fix; widening "
                f"this check is not"
            )

    # (1) and (3) Each subject file: derives nothing itself, and calls the one
    # place where it is the thing that must generate a stamp.
    for rel in subjects:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        raw = path.read_text(encoding="utf-8")
        body = strip_prose(raw, path.suffix if path.suffix else ".mk")
        # One finding per FILE, not per primitive: `exec.Command("git", ...)`
        # trips two markers and is one defect.
        hits = [m for m in forbidden
                if re.search(rf"(?<![\w.]){re.escape(m)}(?![\w])", body)]
        if hits:
            report.fail(
                f"{rel}: runs {', '.join(f'`{h}`' for h in hits)} -- provenance "
                f"is derived once, in {one_place}. A second derivation drifts "
                f"from the first while both stay self-consistent, so neither "
                f"looks wrong on its own"
            )
        if rel in calls and calls[rel] not in raw:
            report.fail(
                f"{rel}: never invokes `{calls[rel]}` -- a component whose stamp "
                f"nothing generates reports an empty one, and an empty stamp "
                f"reads at startup exactly like a binary that was never stamped"
            )

    report.coverage(
        covered=[one_place, *subjects],
        excluded=[
            "whether the reported values are right (ci/provenance-check.py runs each component)",
            "whether a released artifact carries the stamp (task 70.7)",
            "a configuration item colliding with a provenance field (needs task 5.2's schema)",
        ],
        kind="provenance subject",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  one place: {one_place} | subjects held to it: {len(subjects)} | "
          f"execution primitives refused: {len(forbidden)}")
    return report.finish(report_only=report_only)


main_guard(run)
