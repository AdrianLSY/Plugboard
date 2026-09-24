#!/usr/bin/env python3
"""Gate: a relation is a relative markdown link -- never a wikilink or a transclusion.

Enforces docs/knowledge-base -- "Relations are relative markdown links":

  * wiki-style link syntax (`[[target]]`, with or without a pipe alias) fails;
  * transclusion syntax (the same form prefixed by an exclamation mark) fails,
    and is reported as its own kind rather than folded into the wikilink count;
  * a link whose target starts at a filesystem or vault root -- a leading
    slash, a Windows drive letter, a UNC path, a `file://` URI -- fails;
  * a form that resolves only inside the vault reader (an `obsidian://` URI)
    fails;
  * every failure names the note, the line and column, the offending text, and
    the equivalent relative markdown form -- the real relative path when the
    target can be located in the tree, the shape with a placeholder when it
    cannot;
  * every violation in the tree is reported in one run, and a passing run
    states the roots it covered and excluded.

Why the prohibition: a wikilink resolves against a reader's own index, so the
same relation that a person following the rendered file or an agent resolving a
path can traverse becomes reader-only state. The spec's remedy is a link a
`relpath` can follow.

Why the gate masks code rather than grepping: the note that documents this rule
has to be able to show the syntax it forbids, and a specimen already exists in
the tree -- docs/04-protocol-fidelity.md:221 carries the WebIDL internal slot
`[[Reliability]]` inside an inline code span, quoting the W3C definition. A
line-grep gate flags that sentence, and the pressure is then to delete the
citation or to weaken the rule; a gate that cannot tell a specimen from a
violation makes its own rule undocumentable. So fenced blocks and inline code
spans are masked to spaces before matching -- masked, not dropped, so the
column a failure names is still the column in the file.

Deliberately NOT this gate's subject: a markdown link to a path that does not
exist, or to a missing heading anchor. That is the link resolution gate
(ci/gates/links.py, task 1.4). This gate refuses a *form*, not a target.
"""

from __future__ import annotations

import os
import posixpath
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from _common import (
    Report,
    candidates,
    exempt_roots,
    governed_roots,
    load_manifest,
    main_guard,
    notes,
    repo_root,
    scan_excludes,
)

GATE_ID = "wikilinks"
RULE_NOTE = "docs/method/rules/relative-markdown-links.md"

# `![[target]]` and `![[target|alias]]`; the leading `!` makes it a transclusion.
TRANSCLUSION_RE = re.compile(r"!\[\[([^\[\]\n]*)\]\]")
# The same form without the `!`. The lookbehind is what keeps the two kinds
# distinct, so the report can say which one a contributor wrote.
WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\[\]\n]*)\]\]")
# `[text](target ...)` -- target only, up to whitespace, `)` or a closing `>`.
MD_LINK_RE = re.compile(r"\[([^\]\n]*)\]\(\s*<?([^)>\s]*)")
# A reader-only URI anywhere in prose, not only inside a markdown link.
OBSIDIAN_URI_RE = re.compile(r"obsidian://\S+")

WINDOWS_ROOT_RE = re.compile(r"^[A-Za-z]:[\\/]")
ANCHOR_SAFE_RE = re.compile(r"[^a-z0-9\-_]+")


# --------------------------------------------------------------------------
# Masking: a specimen is not a violation.
# --------------------------------------------------------------------------


def _mask_inline(line: str) -> str:
    """Blank every inline code span, preserving length so columns stay true.

    CommonMark: a span opens with a run of N backticks and closes with a run of
    exactly N. An unclosed run is literal text and is left alone -- masking it
    would blank the rest of the line and hide whatever follows.
    """
    out = list(line)
    i = 0
    width = len(line)
    while i < width:
        if line[i] != "`":
            i += 1
            continue
        run = 0
        while i + run < width and line[i + run] == "`":
            run += 1
        j = i + run
        closed = False
        while j < width:
            if line[j] != "`":
                j += 1
                continue
            close = 0
            while j + close < width and line[j + close] == "`":
                close += 1
            if close == run:
                for k in range(i, j + close):
                    out[k] = " "
                i = j + close
                closed = True
                break
            j += close
        if not closed:
            i += run
    return "".join(out)


def _fence_run(line: str) -> tuple[str, int, str]:
    """(fence char, run length, info string) for a candidate fence line."""
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:  # 4+ spaces is not a fence opener
        return "", 0, ""
    char = stripped[:1]
    if char not in ("`", "~"):
        return "", 0, ""
    run = 0
    while run < len(stripped) and stripped[run] == char:
        run += 1
    return char, run, stripped[run:].strip()


def mask_code(lines: list[str]) -> tuple[list[str], int | None]:
    """Mask fenced blocks and inline code. Returns (masked lines, open fence line).

    The open-fence line number is reported as its own violation: an
    unterminated fence would otherwise mask every line after it, turning a
    typo into a way to smuggle wiki syntax past this gate.
    """
    masked: list[str] = []
    fence: tuple[str, int] | None = None
    opened_at: int | None = None
    for lineno, raw in enumerate(lines, start=1):
        char, run, info = _fence_run(raw)
        if fence is None:
            if run >= 3:
                fence, opened_at = (char, run), lineno
                masked.append(" " * len(raw))
                continue
            masked.append(_mask_inline(raw))
            continue
        # Inside a fence: a closer is the same char, at least as long, no info.
        if char == fence[0] and run >= fence[1] and not info:
            fence, opened_at = None, None
        masked.append(" " * len(raw))
    return masked, opened_at


# --------------------------------------------------------------------------
# Suggestion: the concrete relative markdown link that replaces the form.
# --------------------------------------------------------------------------


def tree_files(scan_root: Path) -> list[str]:
    """Every file under the scan root, relative and posix, for target lookup."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = sorted(d for d in dirnames if d not in (".git", "__pycache__"))
        rel_dir = Path(dirpath).relative_to(scan_root)
        for name in sorted(filenames):
            found.append((rel_dir / name).as_posix())
    return sorted(found)


def locate(target: str, files: list[str]) -> str | None:
    """Best match in the tree for a wiki-style or root-anchored target.

    Preference order -- exact path, path suffix, then basename -- so a target
    that names a real path is never answered with a same-named file elsewhere.
    Ambiguity resolves to the shortest path so the suggestion is deterministic.
    """
    name = target.strip().strip("/")
    if not name:
        return None
    forms = [name] if name.endswith(".md") else [name, name + ".md"]
    for form in forms:
        exact = [f for f in files if f == form]
        if exact:
            return exact[0]
    for form in forms:
        suffix = sorted((f for f in files if f.endswith("/" + form)), key=len)
        if suffix:
            return suffix[0]
    stem = posixpath.basename(name)
    base = sorted(
        (
            f
            for f in files
            if posixpath.basename(f) == stem or posixpath.basename(f) == stem + ".md"
        ),
        key=len,
    )
    return base[0] if base else None


def slug(anchor: str) -> str:
    """A heading fragment in the form a rendered file resolves."""
    return ANCHOR_SAFE_RE.sub("-", anchor.strip().lower().replace(" ", "-")).strip("-")


def markdown_form(
    source: str, target: str, text: str, files: list[str]
) -> tuple[str, str]:
    """(suggested markdown link, note). The note is empty when nothing is odd."""
    raw, _, fragment = target.partition("#")
    label = (text or posixpath.basename(raw.strip("/")) or "the note").strip()
    note = ""
    if fragment.startswith("^"):
        # A block reference has no rendered anchor; only a heading does.
        note = "a block reference has no markdown equivalent -- give the target a heading and link its anchor"
        fragment = ""
    suffix = f"#{slug(fragment)}" if fragment else ""

    found = locate(raw, files)
    if found is None:
        placeholder = (raw.strip("/") or "target") + (
            "" if raw.endswith(".md") else ".md"
        )
        return (
            f"[{label}](<relative-path-to>/{posixpath.basename(placeholder)}{suffix})",
            (
                note
                or "target not found in the tree; the shape is shown with a placeholder"
            ),
        )
    rel = posixpath.relpath(found, posixpath.dirname(source) or ".")
    return f"[{label}]({rel}{suffix})", note


def obsidian_target(uri: str) -> str:
    """The vault-relative path an `obsidian://open?...` URI names, if any."""
    parts = urlsplit(uri)
    query = parse_qs(parts.query)
    for key in ("file", "filepath", "path"):
        if query.get(key):
            return query[key][0]
    return parts.path.lstrip("/")


def is_root_anchored(target: str) -> bool:
    """A target that starts at a filesystem or vault root, not at this note."""
    return (
        target.startswith("/")
        or target.startswith("\\\\")
        or target.startswith("file://")
        or bool(WINDOWS_ROOT_RE.match(target))
    )


# --------------------------------------------------------------------------
# The gate.
# --------------------------------------------------------------------------


def scan_note(rel: str, scan_root: Path, files: list[str], report: Report) -> dict:
    """Report every violation in one note. Returns per-kind counts."""
    counts = {"wikilink": 0, "transclusion": 0, "root-anchored": 0, "reader-only": 0}
    text = (scan_root / rel).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    masked, open_fence = mask_code(lines)

    if open_fence is not None:
        report.fail(
            f"{rel}:{open_fence}: unterminated fenced code block -- the gate cannot "
            f"tell a specimen from a violation below it; close the fence"
        )

    for lineno, line in enumerate(masked, start=1):
        spans: list[tuple[int, int]] = []

        for match in TRANSCLUSION_RE.finditer(line):
            counts["transclusion"] += 1
            spans.append(match.span())
            inner = match.group(1)
            target, _, alias = inner.partition("|")
            form, note = markdown_form(rel, target, alias, files)
            report.fail(
                f"{rel}:{lineno}:{match.start() + 1}: transclusion `{match.group(0)}` "
                f"-- transclusion has no markdown form; link the note instead: {form} "
                f"(the embedded body is not reproduced)"
                + (f" [{note}]" if note else "")
            )

        for match in WIKILINK_RE.finditer(line):
            if any(start <= match.start() < end for start, end in spans):
                continue
            counts["wikilink"] += 1
            spans.append(match.span())
            inner = match.group(1)
            target, _, alias = inner.partition("|")
            form, note = markdown_form(rel, target, alias, files)
            report.fail(
                f"{rel}:{lineno}:{match.start() + 1}: wiki-style link "
                f"`{match.group(0)}` -- use a relative markdown link: {form}"
                + (f" [{note}]" if note else "")
            )

        for match in MD_LINK_RE.finditer(line):
            label, target = match.group(1), match.group(2)
            if not target:
                continue
            if target.startswith("obsidian://"):
                counts["reader-only"] += 1
                spans.append(match.span())
                form, note = markdown_form(rel, obsidian_target(target), label, files)
                report.fail(
                    f"{rel}:{lineno}:{match.start() + 1}: reader-only link `{target}` "
                    f"-- an obsidian:// URI resolves only inside the vault reader; "
                    f"use a relative markdown link: {form}"
                    + (f" [{note}]" if note else "")
                )
            elif is_root_anchored(target):
                counts["root-anchored"] += 1
                spans.append(match.span())
                probe = (
                    target[len("file://") :] if target.startswith("file://") else target
                )
                form, note = markdown_form(rel, probe, label, files)
                report.fail(
                    f"{rel}:{lineno}:{match.start() + 1}: root-anchored link `{target}` "
                    f"-- a link is relative to the note that carries it; "
                    f"use a relative markdown link: {form}"
                    + (f" [{note}]" if note else "")
                )

        for match in OBSIDIAN_URI_RE.finditer(line):
            # A bare URI in prose or an autolink, outside any link already named.
            if any(start <= match.start() < end for start, end in spans):
                continue
            counts["reader-only"] += 1
            uri = match.group(0).rstrip(">).,;")
            form, note = markdown_form(rel, obsidian_target(uri), "", files)
            report.fail(
                f"{rel}:{lineno}:{match.start() + 1}: reader-only URI `{uri}` "
                f"-- it resolves only inside the vault reader; use a relative "
                f"markdown link: {form}" + (f" [{note}]" if note else "")
            )

    return counts


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    directories, root_files = governed_roots(manifest)
    report = Report(GATE_ID, RULE_NOTE)

    subjects = notes(scan_root, manifest)
    _, from_index = candidates(scan_root, manifest)
    files = tree_files(scan_root)

    totals = {"wikilink": 0, "transclusion": 0, "root-anchored": 0, "reader-only": 0}
    for rel in subjects:
        for kind, count in scan_note(rel, scan_root, files, report).items():
            totals[kind] += count

        for _subject in subjects:
            report.examine(_subject)
    report.coverage(
        covered=[*directories, *sorted(root_files)],
        excluded=[*exempt_roots(manifest), *scan_excludes(manifest)],
        kind="note",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    print(
        f"  forms: wikilink={totals['wikilink']} "
        f"transclusion={totals['transclusion']} "
        f"root-anchored={totals['root-anchored']} "
        f"reader-only={totals['reader-only']}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
