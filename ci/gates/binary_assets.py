#!/usr/bin/env python3
"""Gate: a committed binary states where it came from and on what terms.

Enforces rebuild-plugboard task 3.14. Every tracked file is classified; any that
is binary must appear in ci/vault.json's `binary_assets` manifest with an origin
and the terms it is carried under.

Three cases, all three failing:

  1. A committed binary absent from the manifest, naming the path and its size.
  2. A manifest entry whose file is gone -- the declaration outlived its subject.
  3. An entry missing `origin` or `terms`. A row saying only that a file is
     expected records nothing anybody can act on.

## Why this is not a licensing check

It is a provenance check, and the distinction matters. The prior attempt shipped
85 JPEGs whose origin was established nowhere: not their source, not their terms,
not who put them there. Nothing in that repository was wrong about them, because
nothing in it said anything about them at all. The remedy is not a scanner that
guesses a licence -- it is that adding a binary becomes a deliberate edit to a
tracked declaration, which is a place a reviewer looks.

## Why every tracked file is a subject

Deciding "is this binary" IS the work, so the classified set is the examined set.
A gate reporting only the binaries it found would report zero over a tree it had
never read, and that count is indistinguishable from a clean one.

This gate exists because the case is not hypothetical here either: two compiled
Go commands, 2.4 MB each, reached a commit in this repository before it was
written, left behind by `go build ./...` writing into a module root.

## What it does not decide

Whether the stated origin is true, whether the terms permit what the repository
does with the file, and whether a text file is one somebody should have committed.
The first two are review's; the third is nobody's, deliberately.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from _common import (
    Report,
    load_manifest,
    main_guard,
    on_tracked_tree,
    repo_root,
    scan_excludes,
    subject_source,
    _in_worktree,
)

GATE_ID = "binary-assets"
RULE_NOTE = "docs/code/rules/binary-assets-carry-provenance.md"

#: git's own heuristic, near enough: a NUL byte in the leading block.
SNIFF_BYTES = 8000


def _tracked(root: Path) -> list[str] | None:
    if not _in_worktree(root):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [p for p in out.decode("utf-8").split("\0") if p]


def _walk(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )


def is_binary(path: Path) -> bool:
    try:
        head = path.open("rb").read(SNIFF_BYTES)
    except OSError:
        return False
    if b"\0" in head:
        return True
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    declared = {
        k: v for k, v in manifest.get("binary_assets", {}).items() if not k.startswith("_")
    }
    report = Report(GATE_ID, RULE_NOTE)

    tracked = _tracked(scan_root)
    paths = tracked if tracked is not None else _walk(scan_root)
    # The violating inputs are excluded for the reason ci/vault.json gives: they
    # are deliberately violating and must not be scanned as part of the real
    # tree. This gate's OWN fixture is a committed, unattributed PNG, so without
    # this the gate would fail the repository on the evidence that it works.
    excluded = scan_excludes(manifest)
    paths = [
        p for p in paths if not any(p == e or p.startswith(e + "/") for e in excluded)
    ]

    binaries = []
    for rel in paths:
        report.examine(rel)
        path = scan_root / rel
        if path.is_file() and is_binary(path):
            binaries.append(rel)
            # (1) a committed binary nobody declared.
            if rel not in declared:
                size = path.stat().st_size
                report.fail(
                    f"{rel}: a committed binary ({size:,} bytes) with no entry in "
                    f"ci/vault.json's binary_assets -- record its origin and the "
                    f"terms it is carried under, or remove it. A file nothing in "
                    f"the repository says anything about is one nobody can answer "
                    f"a question about later"
                )

    # (2) and (3) are about the DECLARATION, so they are repository-scoped: a
    # violating input is deliberately partial and its file set has nothing to do
    # with this manifest's.
    if on_tracked_tree(scan_root):
        for rel, entry in sorted(declared.items()):
            if rel not in binaries:
                report.fail(
                    f"ci/vault.json: binary_assets declares '{rel}', which is not a "
                    f"tracked binary -- the declaration outlived its subject"
                )
                continue
            missing = [k for k in ("origin", "terms") if not (entry or {}).get(k)]
            if missing:
                report.fail(
                    f"ci/vault.json: binary_assets entry '{rel}' states no "
                    f"{' and no '.join(missing)} -- a row recording only that a file "
                    f"is expected records nothing anybody can act on"
                )

    report.coverage(
        covered=["every tracked file, classified"],
        excluded=[*excluded, "whether a stated origin is true (review's)"],
        kind="tracked file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  tracked files: {len(paths)} | binaries: {len(binaries)} | declared: "
        f"{len(declared)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
