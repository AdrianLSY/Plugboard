#!/usr/bin/env python3
"""Gate: one linter configuration for every Go module, and exactly one copy.

Enforces rebuild-plugboard task 2.4 -- the terminator shares a single linter
configuration with the sidecar, and a second copy anywhere in the tree fails.

Three cases, all three failing:

  1. More than one recognised configuration file. Named individually, because
     "there are two" sends nobody to either of them.
  2. No configuration at all while a Go module exists. A module with no linter
     configuration is not lightly configured; it is unlinted, and reports the
     same green as a module with forty checks.
  3. A Go module whose build file reaches neither the shared include nor the
     declared configuration by name. One file on disk is not sharing if a module
     never points at it -- that is a copy with extra steps, and it is how the
     check would pass over exactly the state it exists to prevent.

## Why one copy rather than one per module

The prior art was two repositories. The sidecar carried thirty linters; the
component terminating untrusted traffic had no format check, no Dialyzer, and no
dependency audit at all. Nobody decided that -- it is what two configurations
become, because each drifts toward whatever its own module found inconvenient,
and neither drift is visible from the other side.

## What it does not decide

Whether the configuration is any good, whether a module's build file runs the
linter it points at, and whether the linter is installed. The first is review's,
the second is `ci/make/go.mk`'s single copy of the recipe, and the third fails
loudly at `make lint` rather than silently: a lint target that skips when its
tool is absent is the defect this repository keeps finding under other names.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from _common import (
    Report,
    exempt_roots,
    load_manifest,
    main_guard,
    repo_root,
    scan_excludes,
    subject_source,
    _in_worktree,
)

GATE_ID = "linter-config"
RULE_NOTE = "docs/code/rules/one-linter-config.md"


def _tracked(scan_root: Path) -> list[str] | None:
    """Every tracked path, or None off a work tree.

    The subject is the TRACKED set, for the reason ci/gates/_common.py gives: the
    rules are written about tracked files, and an untracked `.golangci.yaml` in
    somebody's working copy is not a defect in this repository. A violating input
    is not a work tree, so it falls through to the walk below -- and the coverage
    line says which of the two the run used.
    """
    if not _in_worktree(scan_root):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(scan_root), "ls-files", "-z"],
            capture_output=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [p for p in out.decode("utf-8").split("\0") if p]


def _walk(scan_root: Path, skip: set[str]):
    for dirpath, dirnames, filenames in os.walk(scan_root):
        rel_dir = Path(dirpath).relative_to(scan_root).as_posix()
        if rel_dir == ".":
            rel_dir = ""
        dirnames[:] = sorted(
            d
            for d in dirnames
            if d not in {".git"}
            and (f"{rel_dir}/{d}" if rel_dir else d) not in skip
        )
        for name in sorted(filenames):
            yield (f"{rel_dir}/{name}" if rel_dir else name)


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["linter_config"]
    declared = cfg["path"]
    names = set(cfg["recognised_names"])
    shared = cfg["shared_include"]
    report = Report(GATE_ID, RULE_NOTE)

    skip = {*exempt_roots(manifest), *scan_excludes(manifest)}
    tracked = _tracked(scan_root)
    paths = (
        [p for p in tracked if not any(p == s or p.startswith(s + "/") for s in skip)]
        if tracked is not None
        else list(_walk(scan_root, skip))
    )
    found, modules = [], []
    for rel in paths:
        base = rel.rsplit("/", 1)[-1]
        if base in names:
            found.append(rel)
        elif base == "go.mod":
            modules.append(rel.rsplit("/", 1)[0] if "/" in rel else ".")

    for rel in sorted({*found, *modules}):
        report.examine(rel)

    # (1) a second copy.
    extras = sorted(set(found) - {declared})
    for rel in extras:
        report.fail(
            f"{rel}: a second Go linter configuration -- {declared} is the one "
            f"copy, and two configurations become one strict module and one "
            f"unlinted one without anybody deciding that"
        )

    # (2) none at all, with modules present.
    if declared not in found and modules:
        report.fail(
            f"{declared}: absent, with {len(modules)} Go module(s) in the tree "
            f"({', '.join(sorted(modules)[:4])}) -- an unconfigured module reports "
            f"the same green as a configured one"
        )

    # (3) a module that reaches neither the shared include nor the config.
    for mod in sorted(modules):
        build = scan_root / (f"{mod}/Makefile" if mod != "." else "Makefile")
        if not build.is_file():
            report.fail(
                f"{mod}/: a Go module with no Makefile, so no target reaches "
                f"{declared} -- the top-level dispatch cannot lint it either"
            )
            continue
        text = build.read_text(encoding="utf-8")
        if shared not in text and declared not in text:
            report.fail(
                f"{mod}/Makefile: names neither {shared} nor {declared}, so this "
                f"module does not share the one configuration -- a single file on "
                f"disk that a module never points at is a copy with extra steps"
            )

    report.coverage(
        covered=[declared, shared],
        excluded=sorted(skip),
        kind="module or configuration file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  configurations found: {len(found)} ({', '.join(found) or 'none'}) | "
        f"Go modules: {len(modules)} ({', '.join(sorted(modules)) or 'none'})"
    )
    return report.finish(report_only=report_only)


main_guard(run)
