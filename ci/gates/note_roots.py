#!/usr/bin/env python3
"""Gate: the declared root set is closed, and nothing decides its own scope.

Enforces docs/knowledge-base -- "The repository is one vault with one spine":

  * a tracked markdown file under neither a governed nor an exempt root fails,
    naming the path and the declared set;
  * a directory omitted from a traversal without being declared exempt fails,
    naming the directory and requiring it be declared;
  * every run, including a passing one, reports the roots it covered and
    excluded, so green states its own coverage rather than implying totality;
  * the declared set accounts for every tracked markdown file exactly once.

The last two exist because the first version of this gate resolved the
specification's contradiction in its own configuration: `.claude` was dropped
from the walk with no declaration and no reason, and the gate reported the tree
clean over twelve tracked files the requirement forbade. A gate mechanism with
no rule behind it is the inverse of "a rule with no gate is a wish".
"""

from __future__ import annotations

from pathlib import Path

from _common import (
    Report,
    candidates,
    classify,
    exempt_roots,
    governed_roots,
    load_manifest,
    main_guard,
    repo_root,
    scan_excludes,
)

GATE_ID = "note-roots"
RULE_NOTE = "docs/method/rules/note-roots.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    directories, root_files = governed_roots(manifest)
    exempt = exempt_roots(manifest)
    excluded = scan_excludes(manifest)
    report = Report(GATE_ID, RULE_NOTE)

    declared = (
        f"governed dirs: {', '.join(directories)}"
        f" | governed root files: {', '.join(sorted(root_files))}"
        f" | exempt: {', '.join(exempt)}"
    )

    paths, from_index = candidates(scan_root, manifest)
    seen_governed: set[str] = set()
    counts = {"governed": 0, "exempt": 0, "excluded": 0, "undeclared": 0}

    for rel in paths:
        verdict, root = classify(rel, manifest)
        counts[verdict] += 1
        if verdict == "undeclared":
            if "/" in rel:
                report.fail(
                    f"{rel}: outside every declared root -- declare "
                    f"'{root}' governed or exempt in ci/vault.json ({declared})"
                )
            else:
                report.fail(
                    f"{rel}: root-level note is not a declared entry file "
                    f"({declared})"
                )
        elif verdict == "governed":
            seen_governed.add(rel)

    # Each exempt root must carry a reason naming what owns the files instead.
    for root, reason in sorted(manifest.get("exempt_roots", {}).items()):
        if root.startswith("_"):
            continue
        if not isinstance(reason, str) or len(reason.strip()) < 20:
            report.fail(
                f"exempt root '{root}': no recorded reason stating what owns its "
                f"files instead -- exemption is a declaration, not a convenience"
            )

    # A scan exclusion is not root exemption; it must be justified separately.
    for root, reason in sorted(manifest.get("scan_excludes", {}).items()):
        if root.startswith("_"):
            continue
        if not isinstance(reason, str) or len(reason.strip()) < 20:
            report.fail(
                f"scan exclusion '{root}': undeclared -- record why it is excluded "
                f"for a reason other than root exemption, or declare it exempt"
            )

        for _subject in paths:
            report.examine(_subject)
    report.coverage(
        covered=[*directories, *sorted(root_files)],
        excluded=[*exempt, *excluded],
        kind="file",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    print(
        f"  accounting: governed={counts['governed']} exempt={counts['exempt']} "
        f"excluded={counts['excluded']} undeclared={counts['undeclared']}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
