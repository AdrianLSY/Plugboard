#!/usr/bin/env python3
"""Gate: every note is reachable from a declared entry point, as a stated path.

Enforces docs/knowledge-base -- "Every note is reachable from an entry point":

  * every note, and every tracked file under a declared planning directory, is
    reachable by following links from a declared entry point;
  * a file reachable from nothing fails, whether it was newly added or newly
    orphaned by the deletion of the only note that linked to it -- these are one
    computation, so one gate covers both;
  * a planning artifact's inbound link comes from a note OUTSIDE the planning
    directories; an inbound edge from another planning artifact does not count,
    so reachability of the normative surface is a property of the vault rather
    than of the planning tool's internal cross-references;
  * reachability is reported as a PATH from an entry point, not as a yes/no, so
    a contributor is told where the note is missing from.

Two shapes of this gate's subject are deliberate rather than incidental:

  * Link SOURCES are governed notes only. A link from an exempt root (`.claude`
    holds twelve tracked markdown files today) does not make a note reachable,
    because an exempt root carries no obligation of this capability and its
    layout is owned by another tool -- letting it feed the graph would make the
    vault's reachability depend on a vendored skill's cross-references.
  * Subjects include tracked NON-markdown files under a planning directory
    (`openspec/config.yaml`, `openspec/changes/*/.openspec.yaml`). The
    requirement says "every note, and every file under a declared planning
    directory"; _common enumerates markdown only, so this gate enumerates the
    planning directories itself rather than narrowing the requirement to the
    extension its helper happens to return.

A declared entry point that does not exist yet is ABSENT, not a failure:
docs/start-here.md arrives in task 3.2 and AGENTS.md in task 8.2. The gate says
so in its output, because a reachability number measured from one entry point
means something different from the same number measured from three. Per the
requirement's own closing paragraph this gate is not blocking until the
obligation that creates the first inbound links is in force (tasks 3.11, 5.6);
until then it runs with --report-only and its violation count is the backlog.
"""

from __future__ import annotations

import posixpath
import re
import subprocess
from collections import deque
from pathlib import Path
from urllib.parse import unquote, urlsplit

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

GATE_ID = "reachability"
RULE_NOTE = "docs/method/rules/reachability.md"

# Markdown link parsing. Written here rather than imported from the links gate:
# the two gates are independent, and a shared parser would make a change made
# for one silently redefine the other's subject.
#
# A fenced block is skipped because CLAUDE.md and the specs quote command lines
# and code that contain bracket-paren pairs; an edge invented from a code sample
# would make a note look reachable when no reader can follow anything to it.
_FENCE = re.compile(r"^\s{0,3}(?P<fence>```+|~~~+)")
# [text](target), [text](<target>), [text](target "title"). The (?<!!) drops
# image embeds: an image is not a relation between notes.
_INLINE = re.compile(
    r"(?<!!)\[(?:[^\]\\]|\\.)*\]\(\s*(?:<(?P<angle>[^>]*)>|(?P<bare>[^)\s]+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
# [label]: target -- a reference definition is a relation too.
_REFDEF = re.compile(r"^\s{0,3}\[(?:[^\]\\]|\\.)+\]:\s*(?:<(?P<angle>[^>]*)>|(?P<bare>\S+))")


def outbound(note_path: Path) -> list[tuple[int, str]]:
    """(line number, raw target) for every markdown link in a file."""
    found: list[tuple[int, str]] = []
    fence: str | None = None
    text = note_path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if match:
            token = match.group("fence")
            if fence is None:
                fence = token[0] * 3
                continue
            if token.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        for pattern in (_INLINE, _REFDEF):
            for hit in pattern.finditer(line):
                raw = hit.group("angle")
                if raw is None:
                    raw = hit.group("bare")
                if raw:
                    found.append((lineno, raw.strip()))
    return found


def resolve(source_rel: str, raw: str) -> str | None:
    """Repository-relative target of a link, or None if it is not one.

    None covers: an external scheme, a protocol-relative URL, a bare fragment
    (a link into the same note is not a relation), an absolute filesystem path
    (the link discipline refuses that form outright, so counting it as a valid
    relation would let a refused link satisfy this gate), and a target that
    normalises outside the repository.
    """
    if raw.startswith("//") or urlsplit(raw).scheme:
        return None
    target = raw.split("#", 1)[0].strip()
    if not target or target.startswith("/"):
        return None
    target = unquote(target)
    # A file:line citation ("docs/02-architecture.md:212") points at the file.
    head, sep, tail = target.rpartition(":")
    if sep and head and tail.isdigit():
        target = head
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(source_rel), target))
    if joined == ".." or joined.startswith("../"):
        return None
    return joined


def _tracked_all(root: Path) -> list[str] | None:
    """Every tracked path under `root`, or None when `root` is not a work tree.

    _common.tracked_markdown answers the same question for markdown only. The
    planning-directory obligation is written about files, not about markdown, so
    the subject set needs the unfiltered index; None keeps the fixture-tree
    fallback identical to the one _common documents.
    """
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if Path(top).resolve() != root.resolve():
        return None
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def _walk_all(root: Path) -> list[str]:
    """Every file on disk under `root`, relative and sorted. Fixture trees only."""
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    )


def planning_files(scan_root: Path, manifest: dict) -> list[str]:
    """Governed, non-excluded tracked PLANNING ARTIFACTS under a planning root.

    A planning artifact is a file an author writes -- a proposal, a
    specification, a design, a task list. Metadata the planning tool manages for
    itself is not a reachability subject: requiring a note to link to
    `.openspec.yaml` would be a gate demanding prose about a tool's bookkeeping.

    The suffix allowlist and the metadata list are DECLARED in
    ci/vault.json (classification.planning_artifacts), not decided here. An
    earlier revision of this gate read the requirement literally -- "every file
    under a declared planning directory" -- and made `openspec/config.yaml` and
    every `.openspec.yaml` a subject. It was right to implement the requirement
    as written rather than narrow it on its own authority; the requirement was
    then narrowed, and the distinction now lives beside the roots.
    """
    planning = manifest["classification"]["planning_directories"]
    spec = manifest["classification"].get("planning_artifacts", {})
    suffixes = tuple(spec.get("suffixes", [".md"]))
    metadata = {m for m in spec.get("tool_metadata", []) if not m.startswith("_")}
    paths = _tracked_all(scan_root)
    if paths is None:
        paths = _walk_all(scan_root)
    out = []
    for rel in paths:
        if not any(rel == d or rel.startswith(d + "/") for d in planning):
            continue
        if not rel.endswith(suffixes):
            continue
        if rel.rsplit("/", 1)[-1] in metadata:
            continue
        if classify(rel, manifest)[0] == "governed":
            out.append(rel)
    return out


def is_planning(rel: str, manifest: dict) -> bool:
    planning = manifest["classification"]["planning_directories"]
    return any(rel == d or rel.startswith(d + "/") for d in planning)


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    directories, root_files = governed_roots(manifest)
    report = Report(GATE_ID, RULE_NOTE)

    md_notes = notes(scan_root, manifest)
    _, from_index = candidates(scan_root, manifest)
    subjects = sorted(set(md_notes) | set(planning_files(scan_root, manifest)))
    subject_set = set(subjects)

    # --- entry points -------------------------------------------------------
    # An entry point that does not exist yet is absent, not a violation; one
    # that exists outside the governed set IS a violation, because a router the
    # vault does not govern cannot be the origin of a governed property.
    declared_entries = list(manifest["entry_points"]["declared"])
    entries, absent, ungoverned = [], [], []
    for entry in declared_entries:
        if entry in subject_set:
            entries.append(entry)
        elif (scan_root / entry).exists():
            ungoverned.append(entry)
        else:
            absent.append(entry)
    for entry in ungoverned:
        report.fail(
            f"{entry}: declared entry point exists but is not a governed note -- "
            f"declare its root governed in ci/vault.json, or drop it from "
            f"entry_points.declared"
        )

    # --- link graph ---------------------------------------------------------
    # Sources are governed markdown notes only (see the module docstring).
    edges: dict[str, list[tuple[str, int]]] = {}   # source -> [(target, line)]
    inbound: dict[str, list[tuple[str, int]]] = {}  # target -> [(source, line)]
    for rel in md_notes:
        disk = scan_root / rel
        if not disk.is_file():
            # Tracked but not on disk (a staged deletion). Not this gate's rule.
            continue
        for lineno, raw in outbound(disk):
            target = resolve(rel, raw)
            if target is None or target not in subject_set or target == rel:
                continue
            edges.setdefault(rel, []).append((target, lineno))
            inbound.setdefault(target, []).append((rel, lineno))

    # --- breadth-first search from every present entry point ----------------
    parent: dict[str, tuple[str, int] | None] = {e: None for e in entries}
    queue = deque(entries)
    while queue:
        node = queue.popleft()
        for target, lineno in sorted(edges.get(node, [])):
            if target not in parent:
                parent[target] = (node, lineno)
                queue.append(target)

    def link_path(rel: str) -> str:
        """The shortest entry-point-to-note path, as the requirement asks.

        Rendered `source:line -> next:line -> note`, where the line is the one
        carrying the link to the next hop -- so the contributor reading a
        failure elsewhere can see exactly which line a path hangs off.
        """
        chain, hops, cursor = [rel], [], rel
        while parent.get(cursor) is not None:
            source, lineno = parent[cursor]
            hops.append(lineno)
            chain.append(source)
            cursor = source
        chain.reverse()
        hops.reverse()
        if not hops:
            return f"{chain[0]} (declared entry point)"
        steps = [f"{node}:{line}" for node, line in zip(chain, hops)]
        return " -> ".join([*steps, chain[-1]])

    reachable = sorted(parent)

    # --- violation 1: unreachable subjects ----------------------------------
    origin = ", ".join(entries) if entries else "none present"
    for rel in subjects:
        if rel in parent:
            continue
        sources = sorted(inbound.get(rel, []))
        if not sources:
            report.fail(
                f"{rel}: unreachable -- no note links to it (newly added, or "
                f"orphaned by the deletion of its only inbound link); no path "
                f"exists from any entry point ({origin})"
            )
        else:
            named = ", ".join(f"{src}:{line}" for src, line in sources)
            report.fail(
                f"{rel}: unreachable -- linked only from note(s) that are "
                f"themselves unreachable ({named}); no path exists from any "
                f"entry point ({origin})"
            )

    # --- violation 2: a planning artifact linked only by planning artifacts --
    for rel in subjects:
        if not is_planning(rel, manifest):
            continue
        sources = sorted(inbound.get(rel, []))
        if not sources:
            continue  # already named by the unreachable check above
        outside = [(src, line) for src, line in sources if not is_planning(src, manifest)]
        if not outside:
            named = ", ".join(f"{src}:{line}" for src, line in sources)
            report.fail(
                f"{rel}: inbound link comes only from planning artifact(s) "
                f"({named}) -- a planning artifact's inbound link must come from "
                f"a note outside the planning directories "
                f"({', '.join(manifest['classification']['planning_directories'])})"
            )

    # --- the report ---------------------------------------------------------
    print(f"  entry points present: {', '.join(entries) or '-'}")
    print(
        f"  entry points absent (not yet created, not a violation): "
        f"{', '.join(absent) or '-'}"
    )
    # The reachability report proper: one stated path per reachable subject, so
    # that "reachable" is a claim a reader can check rather than a boolean.
    print(f"  reachable: {len(reachable)}/{len(subjects)} subject(s); paths:")
    for rel in reachable:
        print(f"    {rel} <- {link_path(rel)}")

        for _subject in subjects:
            report.examine(_subject)
    report.coverage(
        covered=[*directories, *sorted(root_files)],
        excluded=[*exempt_roots(manifest), *scan_excludes(manifest)],
        kind="note",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    return report.finish(report_only=report_only)


main_guard(run)
