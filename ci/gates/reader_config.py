#!/usr/bin/env python3
"""Gate: reader settings that change resolution are tracked; per-person state is not.

Enforces docs/knowledge-base -- "The repository is one vault with one spine":

    Vault reader configuration SHALL be tracked for the settings that change how
    links resolve and how notes are classified, and SHALL NOT be tracked for
    per-person workspace state or caches.

Two directions, both checked:

  * a declared-tracked setting file that is absent or untracked fails, because
    the link-resolution mode is what makes RDV2 true for everyone who opens the
    vault rather than for whoever configured it first;
  * a declared-untracked path that has become tracked fails, because pane
    layout, per-person hotkeys and the reader's caches are not repository state
    and would otherwise produce a modified file on every session.

It also checks the two settings the change actually depends on, rather than only
the presence of the file that holds them: wiki-style links off and relative link
format on. A tracked app.json that had wikilinks enabled would satisfy a
file-presence check and silently invert RDV2 for every reader.

Scope note: this gate is about *repository* state, so its subject is what
version control tracks. Against a fixture tree there is no index, so presence on
disk stands in for tracked -- the same convention _common.py documents, and the
reason a fixture can exercise the "has become tracked" case at all.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "reader-config"
RULE_NOTE = "docs/method/rules/reader-configuration.md"

# The settings that carry RDV2. A file present but configured the other way is
# worse than a missing file: it looks configured and behaves inverted.
REQUIRED_SETTINGS = {
    "useMarkdownLinks": True,
    "newLinkFormat": "relative",
}


def tracked_paths(root: Path) -> tuple[set[str], bool]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        ).stdout
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
        ).stdout.decode().strip()
        if Path(top).resolve() == root.resolve():
            return {p for p in out.decode("utf-8").split("\0") if p}, True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    found = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    return found, False


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["reader_config"]
    want_tracked = [p for p in cfg["tracked"] if not p.startswith("_")]
    want_untracked = [p for p in cfg["untracked"] if not p.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)

    present, from_index = tracked_paths(scan_root)

    for rel in want_tracked:
        if rel not in present:
            report.fail(
                f"{rel}: declared as tracked reader configuration but is not "
                f"tracked -- the link-resolution mode must apply to every reader, "
                f"not to whoever configured the vault first"
            )

    for rel in want_untracked:
        if rel in present:
            report.fail(
                f"{rel}: per-person workspace state or cache is tracked -- it is "
                f"not repository state and will show as a modified file on every "
                f"session; add it to .gitignore"
            )
        # A cache declared as a directory: anything beneath it counts too.
        for got in sorted(p for p in present if p.startswith(rel.rstrip("/") + "/")):
            report.fail(
                f"{got}: lives under declared-untracked reader path '{rel}' and is tracked"
            )

    app = scan_root / ".obsidian" / "app.json"
    if app.is_file():
        try:
            settings = json.loads(app.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.fail(f".obsidian/app.json: not valid JSON ({exc.msg} at line {exc.lineno})")
        else:
            for key, expected in REQUIRED_SETTINGS.items():
                actual = settings.get(key)
                if actual != expected:
                    report.fail(
                        f".obsidian/app.json: {key} is {actual!r}, must be "
                        f"{expected!r} -- relations are relative markdown links, "
                        f"and a reader configured otherwise writes the prohibited form"
                    )
    elif ".obsidian/app.json" in want_tracked:
        pass  # already reported above as untracked/absent

    for _subject in [*want_tracked, *want_untracked]:
        report.examine(_subject)
    report.coverage(
        covered=[*want_tracked, ".obsidian/app.json settings"],
        excluded=want_untracked,
        kind="setting",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    return report.finish(report_only=report_only)


main_guard(run)
