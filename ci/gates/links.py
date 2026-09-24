#!/usr/bin/env python3
"""Gate: every link from a note into the repository resolves -- file and anchor.

Enforces docs/knowledge-base -- "Every link resolves":

  * a link to a repository path that does not exist fails, naming the source
    note, the line, and the unresolved target;
  * a link carrying a fragment that no anchor in the target provides fails, and
    the failure DISTINGUISHES a missing anchor from a missing file -- the two
    have different fixes, and a report that conflates them sends a contributor
    to create a file that is already there;
  * every unresolved link is reported in one run rather than the first only;
  * the run states the roots it covered and the roots it excluded.

Subject: governed notes (`notes()`) plus any declared entry file present in the
tree, which is what "every tracked note, every component README and the
contributor entry files" comes to once the roots are declared. The entry set is
unioned in explicitly because an entry file may exist before it is tracked, and
an unresolvable link in the first file an agent reads is the worst case this
gate exists to catch.

The distinction between the two causes is the concrete defect behind this gate.
The reference attempt's docs cited `lib/plugboard/...` paths that had been
renamed; a checker that reported them all as "broken link" gave no way to tell a
renamed file from a renamed heading, so the whole list was re-verified by hand
every time. Naming the cause makes the fix mechanical.

Deliberately NOT this gate's business, so that a failure here means one thing:
whether a link is *relative* rather than absolute or reader-specific (the
wikilink/relative-link gate owns that), and whether a note is reachable at all
(the reachability gate owns that). A root-absolute `/docs/x.md` is resolved
here against the repository root rather than failed twice.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from _common import (
    Report,
    candidates,
    classify,
    exempt_roots,
    governed_roots,
    load_manifest,
    main_guard,
    notes,
    repo_root,
    scan_excludes,
)

GATE_ID = "links"
RULE_NOTE = "docs/method/rules/link-resolution.md"

# Causes. Kept as constants because the requirement is that the report
# distinguishes them, so they are part of the gate's contract, not phrasing.
MISSING_FILE = "missing-file"
MISSING_ANCHOR = "missing-anchor"

# Schemes that leave the repository. Note the deliberate narrowness: anything
# with an authority component (`scheme://`) plus the two mail/phone forms. A
# broad "looks like scheme:" test would swallow `proxy/lib/router.ex:47`, which
# is a line-numbered citation this gate must resolve, not skip.
_EXTERNAL_PREFIXES = ("mailto:", "tel:")

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*(\S*)")
_REF_DEF = re.compile(r"^ {0,3}\[([^\]^]+)\]:\s*(\S+)")
_ATX = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*$")
_CUSTOM_ID = re.compile(r"\{#([A-Za-z0-9_\-:.]+)\}\s*$")
_HTML_ANCHOR = re.compile(r"<a\s[^>]*?(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.I)
_HEADING_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_TITLE_TAIL = re.compile(r"""\s+(?:"[^"]*"|'[^']*'|\([^()]*\))\s*$""")
_LINE_SUFFIX = re.compile(r":(\d+)(?:[-:](\d+))?$")
_LINE_FRAGMENT = re.compile(r"^L\d+(?:[-C]\d+)*$", re.I)
_SLUG_STRIP = re.compile(r"[^\w\- ]+", re.UNICODE)

# Fragments into a non-markdown file cannot be checked against headings; the
# forge's own line-fragment form is the one that legitimately appears.
_MARKDOWN_SUFFIXES = {".md", ".markdown"}


def _mask_code_spans(line: str) -> str:
    """Blank out inline-code spans, preserving length so columns still line up.

    A `[x](y)` inside backticks renders literally and is not a link; failing on
    it would push authors to stop writing examples of the syntax the vault's own
    convention notes have to show.
    """
    out = list(line)
    i = 0
    n = len(line)
    while i < n:
        if line[i] != "`":
            i += 1
            continue
        run = 1
        while i + run < n and line[i + run] == "`":
            run += 1
        close = line.find("`" * run, i + run)
        # A closing run must be exactly `run` ticks long, not part of a longer one.
        while close != -1:
            after = close + run
            if after >= n or line[after] != "`":
                break
            close = line.find("`" * run, after)
        if close == -1:
            i += run
            continue
        for k in range(i, close + run):
            out[k] = " "
        i = close + run
    return "".join(out)


def _content_lines(text: str) -> list[tuple[int, str]]:
    """(1-based line number, code-masked text) for every non-fenced body line.

    Fenced blocks and YAML frontmatter are dropped: neither renders as markdown,
    so a path inside them is a sample, not a relation.
    """
    raw = text.splitlines()
    start = 0
    if raw and raw[0].strip() == "---":
        for idx in range(1, len(raw)):
            if raw[idx].strip() in ("---", "..."):
                start = idx + 1
                break
    kept: list[tuple[int, str]] = []
    fence: str | None = None
    for idx in range(start, len(raw)):
        line = raw[idx]
        match = _FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)[0] * len(match.group(1))
                continue
        else:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = None
            continue
        kept.append((idx + 1, _mask_code_spans(line)))
    return kept


def _inline_destinations(line: str) -> list[str]:
    """Every `](dest)` destination on one line, brackets and parens balanced.

    Hand-scanned rather than regexed: destinations legitimately contain
    parentheses, and link text legitimately contains brackets.
    """
    found: list[str] = []
    i = 0
    while True:
        mid = line.find("](", i)
        if mid < 0:
            return found
        back = mid
        depth = 0
        while back >= 0:
            if line[back] == "]":
                depth += 1
            elif line[back] == "[":
                depth -= 1
                if depth == 0:
                    break
            back -= 1
        if back < 0:  # a stray `](` with no opening bracket is not a link
            i = mid + 2
            continue
        pos = mid + 2
        depth = 1
        while pos < len(line):
            if line[pos] == "(":
                depth += 1
            elif line[pos] == ")":
                depth -= 1
                if depth == 0:
                    break
            pos += 1
        if pos >= len(line):  # unterminated; a link split across lines
            i = mid + 2
            continue
        found.append(line[mid + 2 : pos])
        i = pos + 1


def _normalise_destination(dest: str) -> str:
    """Strip the optional title and the `<...>` wrapper from a destination."""
    dest = dest.strip()
    dest = _TITLE_TAIL.sub("", dest).strip()
    if dest.startswith("<") and dest.endswith(">") and len(dest) >= 2:
        return dest[1:-1].strip()
    if " " in dest or "\t" in dest:  # untitled but whitespace-bearing: take the path
        dest = dest.split()[0]
    return dest


def _is_external(target: str) -> bool:
    lowered = target.lower()
    if "://" in lowered:
        return True
    if lowered.startswith(_EXTERNAL_PREFIXES):
        return True
    return False


def _slug(heading: str) -> str:
    """GitHub-style anchor slug for a heading's rendered text."""
    text = _HEADING_LINK.sub(r"\1", heading)
    text = text.replace("`", "").replace("*", "")
    text = _SLUG_STRIP.sub("", text)
    return text.strip().lower().replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    """Anchors the target file provides: heading slugs, `{#id}`, `<a id=...>`.

    Duplicate headings get the forge's `-1`, `-2` disambiguators, so a second
    "## Notes" is still linkable.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    found: set[str] = set()
    for name in _HTML_ANCHOR.findall(text):
        found.add(name)
    seen: dict[str, int] = {}
    for _lineno, line in _content_lines(text):
        match = _ATX.match(line)
        if not match:
            continue
        heading = match.group(2).rstrip("#").strip()
        custom = _CUSTOM_ID.search(heading)
        if custom:
            found.add(custom.group(1))
            heading = _CUSTOM_ID.sub("", heading).strip()
        slug = _slug(heading)
        if not slug:
            continue
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def _resolve_path(scan_root: Path, source_rel: str, path_part: str) -> Path:
    """Repository path a link's path component names, from its source note."""
    decoded = unquote(path_part)
    if decoded.startswith("/"):
        return (scan_root / decoded.lstrip("/")).resolve()
    return (scan_root / source_rel).parent.joinpath(decoded).resolve()


def _targets_in(text: str) -> list[tuple[int, str]]:
    """(line, raw destination) for inline links, images, and reference defs."""
    out: list[tuple[int, str]] = []
    for lineno, line in _content_lines(text):
        ref = _REF_DEF.match(line)
        if ref:
            out.append((lineno, ref.group(2)))
            continue
        for dest in _inline_destinations(line):
            out.append((lineno, dest))
    return out


def _subjects(scan_root: Path, manifest: dict) -> tuple[list[str], bool]:
    """Governed notes plus every declared entry file that exists in the tree."""
    subjects = list(notes(scan_root, manifest))
    _paths, from_index = candidates(scan_root, manifest)
    entry = manifest.get("entry_points", {}).get("declared", [])
    for rel in entry:
        if rel in subjects:
            continue
        verdict, _root = classify(rel, manifest)
        if verdict != "governed":
            continue
        if (scan_root / rel).is_file():
            subjects.append(rel)
    return sorted(set(subjects)), from_index


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    directories, root_files = governed_roots(manifest)
    report = Report(GATE_ID, RULE_NOTE)

    subjects, from_index = _subjects(scan_root, manifest)
    anchor_cache: dict[Path, set[str]] = {}
    counts = {
        "links": 0,
        "external": 0,
        "resolved": 0,
        MISSING_FILE: 0,
        MISSING_ANCHOR: 0,
    }

    for rel in subjects:
        source = scan_root / rel
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            report.fail(f"{rel}: unreadable ({exc})")
            continue

        for lineno, raw in _targets_in(text):
            target = _normalise_destination(raw)
            if not target:
                continue
            counts["links"] += 1
            if _is_external(target):
                counts["external"] += 1
                continue

            path_part, _, fragment = target.partition("#")
            fragment = unquote(fragment).strip()

            if not path_part:
                # A bare `#anchor` is an anchor claim about this very file, and
                # is in scope: it breaks when the heading is renamed.
                resolved = source.resolve()
            else:
                # `proxy/lib/router.ex:47` is a citation: resolve the file, drop
                # the line. Only strip when the stripped path is the one that
                # exists, so a real filename ending in digits survives.
                candidate = _resolve_path(scan_root, rel, path_part)
                if not candidate.exists():
                    stripped = _LINE_SUFFIX.sub("", path_part)
                    if stripped != path_part:
                        candidate = _resolve_path(scan_root, rel, stripped)
                resolved = candidate

            root = scan_root.resolve()
            escapes = root != resolved and root not in resolved.parents

            if escapes:
                report.fail(
                    f"{rel}:{lineno}: {MISSING_FILE} -- target '{target}' resolves to "
                    f"'{resolved}', outside the repository root; a link must name a "
                    f"path inside the repository"
                )
                counts[MISSING_FILE] += 1
                continue

            if not resolved.exists():
                report.fail(
                    f"{rel}:{lineno}: {MISSING_FILE} -- target '{target}' names no "
                    f"existing file (looked for '{resolved.relative_to(root)}'); the "
                    f"file is absent, not the anchor"
                )
                counts[MISSING_FILE] += 1
                continue

            if not fragment:
                counts["resolved"] += 1
                continue

            shown = resolved.relative_to(root).as_posix()
            if resolved.is_dir():
                report.fail(
                    f"{rel}:{lineno}: {MISSING_ANCHOR} -- '#{fragment}' has no anchor "
                    f"to resolve against: '{shown}' exists but is a directory"
                )
                counts[MISSING_ANCHOR] += 1
                continue

            if resolved.suffix.lower() not in _MARKDOWN_SUFFIXES:
                # Non-markdown target: the only fragment form that resolves is
                # the forge's line fragment, or an explicit HTML anchor.
                if _LINE_FRAGMENT.match(fragment):
                    counts["resolved"] += 1
                    continue
                anchors = anchor_cache.setdefault(resolved, _anchors(resolved))
                if fragment in anchors:
                    counts["resolved"] += 1
                    continue
                report.fail(
                    f"{rel}:{lineno}: {MISSING_ANCHOR} -- '#{fragment}' is not an "
                    f"anchor in '{shown}'; the file exists but is not markdown, so "
                    f"only a line fragment (#L12) or an explicit <a id> resolves"
                )
                counts[MISSING_ANCHOR] += 1
                continue

            anchors = anchor_cache.setdefault(resolved, _anchors(resolved))
            if fragment in anchors:
                counts["resolved"] += 1
                continue
            report.fail(
                f"{rel}:{lineno}: {MISSING_ANCHOR} -- '{shown}' exists but provides "
                f"no anchor '#{fragment}'; available: "
                f"{', '.join('#' + a for a in sorted(anchors)) or '(none)'}"
            )
            counts[MISSING_ANCHOR] += 1

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
        f"  accounting: links={counts['links']} resolved={counts['resolved']} "
        f"external-skipped={counts['external']} "
        f"{MISSING_FILE}={counts[MISSING_FILE]} "
        f"{MISSING_ANCHOR}={counts[MISSING_ANCHOR]}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
