#!/usr/bin/env python3
"""Gate: a top-level directory says what it is, or is declared as not needing to.

Enforces docs/code-standards -- "A component's boundary is stated once", in the
half that is about ARRIVAL rather than about drift: a directory at the root of
the repository is the first thing a contributor or an agent sees, and one with
no README is a directory nobody can place without reading its contents.

Two cases, both failing:

  1. A top-level directory holding tracked files, not declared exempt, with no
     README.md. The README is a router: it names the component and links the one
     note stating its boundary. What it must NOT do is restate that boundary --
     that half is ci/gates/component_boundaries.py's, and the two are kept apart
     deliberately so "there is a README" and "the README is not a second copy"
     fail separately and name different remedies.

  2. A declared exemption for a directory that holds no tracked files. A
     declaration cannot outlive its subject; an exemption for a directory nobody
     deleted it with is the same stale-declaration shape ci/vault.json's
     declared_vacuity exists to prevent.

## Why an exemption list rather than a rule about which directories count

Four top-level directories legitimately carry no README, and each for a
different reason that a heuristic would have to guess: `docs/` is entered
through a generated index, `openspec/` has its layout owned by an external tool,
`ci/` is described once in the spine and a second description beside the gates is
the copy that drifts, and `.github/` and `.obsidian/` are read by a service and
an editor rather than by a person. Guessing any of those wrong produces either a
gate that fires on four directories forever or one that fires on none. So the set
is declared, in ci/vault.json, with the reason beside each entry -- and case 2
holds the declaration to its subject.

## Why case 2 is scoped to the tracked tree

The exemption set is a fact about THIS repository, and it is read from the real
ci/vault.json on every run including one pointed at a violating input. A fixture
tree is deliberately partial, so nearly every exempt directory is absent from it
and case 2 would fire ten times over a tree that demonstrates nothing about the
declaration. `on_tracked_tree` is the same guard component_boundaries, index_drift
and out_of_scope each arrived at separately.

## What this does not decide

Whether the README is any good. A file containing its own heading and nothing
else satisfies this gate. The link gate holds its links, the frontmatter gate its
classification, the reachability gate its inbound route, and the boundary gate
its one-copy obligation. This one decides only that the file is there, which is
the property that was false for five directories the moment they were created.
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
    on_tracked_tree,
    repo_root,
    subject_source,
)

GATE_ID = "top-level-readmes"
RULE_NOTE = "docs/code/rules/top-level-directory-carries-a-readme.md"


def _tracked_top_level(scan_root: Path) -> set[str] | None:
    """Top-level directories holding tracked files, or None off a work tree."""
    if not on_tracked_tree(scan_root):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(scan_root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return {p.split("/", 1)[0] for p in out.decode("utf-8").split("\0") if "/" in p}


def _walked_top_level(scan_root: Path) -> set[str]:
    """Top-level directories holding any file at all. Fixture trees only."""
    found = set()
    for entry in sorted(scan_root.iterdir()):
        if not entry.is_dir() or entry.name == ".git":
            continue
        for _dirpath, _dirnames, filenames in os.walk(entry):
            if filenames:
                found.add(entry.name)
                break
    return found


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["top_level_readmes"]
    readme = cfg["readme_name"]
    stated = {k: v for k, v in cfg["exempt"].items() if not k.startswith("_")}
    # Roots already declared exempt from the vault's obligations are exempt from
    # this one too, and are NOT restated here: two lists of the same directories
    # is the second encoding ci/gates/correspondences.py exists to catch.
    exempt = set(stated) | set(exempt_roots(manifest))
    report = Report(GATE_ID, RULE_NOTE)

    tracked = _tracked_top_level(scan_root)
    present = tracked if tracked is not None else _walked_top_level(scan_root)
    subjects = sorted(d for d in present if d not in exempt)

    for name in subjects:
        report.examine(name)
        if not (scan_root / name / readme).is_file():
            report.fail(
                f"{name}/: top-level directory with no {readme} -- a directory at "
                f"the root of the repository is the first thing a reader sees, and "
                f"one that does not say what it is has to be opened to be placed. "
                f"Add {name}/{readme} routing to its boundary note, or declare "
                f"{name} in ci/vault.json code_standards.top_level_readmes.exempt "
                f"with the reason"
            )

    # (2) an exemption whose subject is gone. Repository-scoped: see the docstring.
    if on_tracked_tree(scan_root):
        for name in sorted(stated):
            if name not in present:
                report.fail(
                    f"ci/vault.json: code_standards.top_level_readmes.exempt "
                    f"declares '{name}', which holds no tracked file -- a "
                    f"declaration cannot outlive its subject"
                )

    report.coverage(
        covered=subjects or ["(no top-level directory is in scope)"],
        excluded=sorted(exempt),
        kind="top-level directory",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  top-level directories: {len(present)} | in scope: {len(subjects)} | "
        f"exempt by declaration: {len(stated)} | exempt as a declared vault root: "
        f"{len(exempt) - len(stated)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
