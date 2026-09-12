"""Shared source reading for the code-shape gates. Standard library only.

Three gates measure source rather than notes -- size ceilings, duplication and
the no-repair guard -- and each needs the same two things: the tracked set of
source files in the declared languages, and a line count that is not fooled by
comments. One copy, for the reason ci/make/go.mk gives about recipes: three
copies of a predicate is how two of them come to disagree, and here they would
disagree about what a LINE is.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from _common import load_manifest, repo_root, scan_excludes, _in_worktree

#: Per extension: the line-comment marker, and whether the language nests blocks
#: by indentation (Elixir's `do`/`end`) or by braces (Go).
COMMENT = {".go": "//", ".ex": "#", ".exs": "#", ".py": "#"}


def config(manifest: dict | None = None) -> dict:
    return (manifest or load_manifest(repo_root()))["code_standards"]["code_size"]


def languages(cfg: dict) -> dict[str, str]:
    return {k: v for k, v in cfg["languages"].items() if not k.startswith("_")}


def sources(scan_root: Path, cfg: dict, manifest: dict) -> list[str]:
    """Tracked source files in the declared languages, or a walk off a work tree."""
    exts = tuple(languages(cfg))
    excluded = scan_excludes(manifest)
    if _in_worktree(scan_root):
        try:
            out = subprocess.run(
                ["git", "-C", str(scan_root), "ls-files", "-z"],
                capture_output=True, check=True,
            ).stdout
            paths = [p for p in out.decode("utf-8").split("\0") if p]
        except (subprocess.CalledProcessError, FileNotFoundError):
            paths = _walk(scan_root)
    else:
        paths = _walk(scan_root)
    return sorted(
        p for p in paths
        if p.endswith(exts)
        and not any(p == e or p.startswith(e + "/") for e in excluded)
    )


def _walk(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )


def code_lines(text: str, comment: str) -> list[tuple[int, str]]:
    """(1-based line number, stripped text) for every non-blank, non-comment line.

    A comment does not count toward a ceiling, which is the half that matters:
    otherwise a file crossing one is padded with comments to move the count, and
    the rule asks for the file to be split along what made it long.
    """
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(comment):
            continue
        out.append((n, stripped))
    return out


GO_FUNC = re.compile(r"^func\b")
EX_FUNC = re.compile(r"^(\s*)defp?\s+\S")


def clauses(rel: str, text: str) -> list[tuple[str, int, int]]:
    """(name, first line, non-comment body lines) for each function clause.

    Per CLAUSE rather than per name, which docs/code/rules/function-size-ceiling.md
    asks for: a function with many clauses is measured clause by clause, and a
    template rendered inline is measured with the function it sits in.
    """
    if rel.endswith(".go"):
        return _go_clauses(text)
    if rel.endswith((".ex", ".exs")):
        return _elixir_clauses(text)
    return []


def _go_clauses(text: str) -> list[tuple[str, int, int]]:
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines):
        if not GO_FUNC.match(line):
            continue
        name = line.strip()[:70]
        body = []
        for j in range(i + 1, len(lines)):
            if lines[j] == "}":
                break
            body.append(lines[j])
        found.append((name, i + 1, len(code_lines("\n".join(body), "//"))))
    return found


def _elixir_clauses(text: str) -> list[tuple[str, int, int]]:
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines):
        m = EX_FUNC.match(line)
        if not m or line.rstrip().endswith(", do:") or ", do:" in line:
            continue
        if not line.rstrip().endswith("do"):
            continue
        indent = m.group(1)
        body = []
        for j in range(i + 1, len(lines)):
            if lines[j] == indent + "end":
                break
            body.append(lines[j])
        found.append((line.strip()[:70], i + 1, len(code_lines("\n".join(body), "#"))))
    return found
