#!/usr/bin/env python3
"""Gate: every language with tracked source has stated conventions, and no others.

Enforces docs/code-standards -- "Every language with tracked source has stated
conventions": introducing a language without its conventions fails, and
conventions for a language no longer present fail too.

## The consequence today, which is worth knowing before reading the guide

Python is the only language with tracked source: the gate modules, the index
generator and the aggregating runner. So the guide covers Python and nothing
else. Elixir and Go conventions cannot be written yet -- this gate would refuse
them as conventions for an absent language, which is exactly its second case
doing its job.

That collides with the proposal's promise of "per-language conventions for
Elixir and Go", and the collision is the gate's finding rather than its bug: the
promise is scoped to when their source lands. A guide that described conventions
for two languages the repository does not contain would be describing a system
that does not exist -- the failure mode the whole vault is built to refuse.

Fixture files are not source. A `.ex` file under ci/broken-inputs is a test input
for the link gate, and counting it would have produced Elixir conventions on the
strength of one deliberately-broken example.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root


GATE_ID = "language-coverage"
RULE_NOTE = "docs/code/rules/language-conventions-keyed-on-source.md"


def tracked(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
        ).stdout
        return [p for p in out.decode("utf-8").split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["languages"]
    globs = {k: v for k, v in cfg["source_globs"].items() if not k.startswith("_")}
    excl = tuple(cfg.get("exclude", []))
    ndir = cfg["note_dir"]
    report = Report(GATE_ID, RULE_NOTE)

    files = [f for f in tracked(scan_root) if not any(f.startswith(e) for e in excl)]
    present = {}
    for lang, patterns in globs.items():
        hits = [
            f for f in files
            if any(Path(f).match(pat) for pat in patterns)
        ]
        if hits:
            present[lang] = len(hits)

    notes = {
        p.stem: p for p in sorted((scan_root / ndir).glob("*.md")) if p.stem != "index"
    } if (scan_root / ndir).is_dir() else {}

    for lang, n in sorted(present.items()):
        if lang not in notes:
            report.fail(
                f"{lang}: {n} tracked source file(s) and no conventions note at "
                f"{ndir}/{lang}.md"
            )
    for name in sorted(notes):
        if name not in present:
            report.fail(
                f"{ndir}/{name}.md: conventions for a language with no tracked "
                f"source -- describing a language the repository does not contain"
            )

        for _subject in present:
            report.examine(_subject)
    report.coverage(
        covered=sorted(present) or ["(no tracked source)"],
        excluded=[*excl, *sorted(set(globs) - set(present))],
        kind="language",
        source="scan",
        scan_root=scan_root,
    )
    print(
        "  languages present: "
        + (", ".join(f"{k} ({v} files)" for k, v in sorted(present.items())) or "none")
        + f" | conventions notes: {len(notes)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
