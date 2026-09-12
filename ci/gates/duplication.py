#!/usr/bin/env python3
"""Gate: requirement text has one copy -- the spine links to it, never copies it.

Enforces docs/knowledge-base -- "The repository is one vault with one spine",
scenario "Content is not duplicated between the spine and the specifications":
when a note in the spine and a specification both contain the same requirement
text the gate fails, and the failure names BOTH locations, so the copy can be
deleted and replaced by a link to the artifact that owns it.

The concrete defect that motivated it: `docs/05-decision-log.md` restates
decisions that `openspec/changes/rebuild-plugboard/design.md` owns, and the
restatement went stale -- its "Open questions" table still lists four questions
that D16-D20 resolved. `CLAUDE.md` now carries a prose warning telling readers
which copy wins. Two copies of one decision plus a note about which to believe
is the failure mode; one copy and a link is the fix.

WHAT THIS GATE DECIDES, exactly
-------------------------------
  * It compares paragraph- and blockquote-sized blocks ACROSS three sides --
    the spine, the specifications, and the per-component roots -- and fails on
    an EXACT match of the normalised form:
    blockquote markers and list bullets dropped, inline links reduced to their
    link text, markdown emphasis characters stripped, whitespace collapsed,
    case folded. So it catches a copy that was re-wrapped, re-emphasised,
    re-cased, indented into a quote, or relinked at a different relative path.
  * It considers only blocks of at least MIN_CHARS characters and MIN_WORDS
    words. Below that, a shared line is incidental -- a specification and a
    note about it inevitably share "THEN the gate fails" -- and a gate that
    fired on those would be turned off rather than obeyed. The price is stated
    rather than hidden: a copied fragment shorter than the floor is not caught.
  * Fenced code is not requirement text, and is excluded. A command line or a
    manifest excerpt appearing in both a note and a specification is duplicated
    code, which the code-standards duplication threshold owns (task 6.11), not
    a duplicated requirement.
  * Duplication that is wholly inside the spine, wholly inside the
    specifications, or wholly among the component roots is not this gate's
    subject. The requirement is about the boundaries BETWEEN them.

WHY THE COMPONENT ROOTS ARE A SIDE
----------------------------------
A component README is where the second copy of a boundary appears -- reliably
enough that ci/gates/component_boundaries.py checks the heading form of it
separately. That check catches a README that restates its boundary under its own
"What it owns" heading; it cannot catch one that pastes the boundary note's
paragraphs under any other heading, or one that pastes a requirement straight out
of a specification. This side closes that, and the two gates stay apart because
they hand over different remedies: add the link, versus delete the copy.

Entry files at the repository root (README.md, CLAUDE.md, AGENTS.md,
CONTRIBUTING.md) are NOT a side here. They are held to a size ceiling and to the
absent-artifact rule by ci/gates/entry_points.py, and a router short enough to
pass that ceiling has little room to carry a copied requirement paragraph. Said
rather than left implicit: a copy pasted into an entry file is not caught here.

WHAT IT CANNOT DECIDE, and what owns that instead
-------------------------------------------------
It catches copy-paste, and only copy-paste. It CANNOT catch a paraphrase: a
note that restates a requirement in its own words is invisible here, and so is
a paraphrase that later drifts out of agreement with the specification it
restates -- which is exactly the decision-log defect above, in the form this
gate cannot see. That is deliberate, not an unfinished edge: a deterministic
check has no access to "means the same thing", and widening this one with
fuzzy similarity would trade a decidable property for a tunable one.

The property this gate holds is ONE COPY, not currency. Currency of a
restatement is owned elsewhere:

  * docs/knowledge-base -- "Authority precedence is stated and enforced": a
    spine note stating behaviour a specification owns must mark the statement
    non-normative and link to the owning specification, so a drifted
    restatement is readable as non-authoritative rather than as a rival claim.
  * docs/knowledge-base -- "The documentation reflects the current state", and
    human review, for whether the restatement still says something true.

So a passing run of this gate means "no copied block crosses the boundary". It
does not mean "the spine and the specifications agree", and neither this
module's output nor its comments may be read as claiming that.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import (
    Report,
    candidates,
    exempt_roots,
    load_manifest,
    main_guard,
    notes,
    repo_root,
    scan_excludes,
)

GATE_ID = "duplication"
RULE_NOTE = "docs/method/rules/one-copy-of-requirement-text.md"

# The floor below which a shared block is incidental rather than copied. Both
# conditions must hold: characters alone would admit a long path or a table
# row, words alone would admit a wrapped heading. A requirement paragraph in
# openspec/changes/**/specs/**/spec.md runs well past both.
MIN_CHARS = 120
MIN_WORDS = 18

_FENCE = re.compile(r"^(`{3,}|~{3,})")
# A leading run of blockquote markers, then at most one list bullet. Applied
# per line so an indented quote of a bulleted requirement normalises to the
# same text as the requirement itself.
_LEADING = re.compile(r"^\s*(?:>\s*)*(?:[-*+]\s+|\d+[.)]\s+)?")
_INLINE_LINK = re.compile(r"\[([^\]\n]*)\]\([^)\n]*\)")
_WHITESPACE = re.compile(r"\s+")
# Emphasis, code-span and strikethrough markers carry no meaning for identity.
# Deleting them can only make two texts more likely to match, never less, so
# the direction of the error is toward reporting a pair for a human to dismiss.
_EMPHASIS = str.maketrans("", "", "*_`~")


def _is_spec(rel: str) -> bool:
    """True for openspec/**/specs/**/*.md -- the specification side of the pair."""
    parts = rel.split("/")
    if len(parts) < 3 or parts[0] != "openspec" or not rel.endswith(".md"):
        return False
    return "specs" in parts[1:-1]


def _blocks(text: str) -> list[tuple[int, str]]:
    """(1-based start line, raw block) for each paragraph/blockquote-sized block.

    Frontmatter is skipped (it is classification, not requirement text), each
    heading is its own block, and fenced regions are dropped entirely per the
    boundary stated in the module docstring.
    """
    lines = text.splitlines()
    index = 0
    if lines and lines[0].strip() == "---":
        for offset in range(1, len(lines)):
            if lines[offset].strip() in ("---", "..."):
                index = offset + 1
                break

    found: list[tuple[int, str]] = []
    buffer: list[str] = []
    start = 0
    fence: str | None = None

    def flush() -> None:
        nonlocal buffer
        if buffer:
            found.append((start, "\n".join(buffer)))
            buffer = []

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            index += 1
            continue
        opener = _FENCE.match(stripped)
        if opener:
            flush()
            fence = opener.group(1)[:3]
        elif not stripped:
            flush()
        elif stripped.startswith("#"):
            flush()
            found.append((index + 1, raw))
        else:
            if not buffer:
                start = index + 1
            buffer.append(raw)
        index += 1
    flush()
    return found


def _normalise(block: str) -> str:
    text = " ".join(_LEADING.sub("", line) for line in block.splitlines())
    text = _INLINE_LINK.sub(r"\1", text)
    text = text.translate(_EMPHASIS)
    return _WHITESPACE.sub(" ", text).strip().casefold()


def _index_blocks(
    scan_root: Path, rels: list[str]
) -> tuple[dict[str, list[tuple[str, int]]], list[str]]:
    """(normalised block -> every (path, line) carrying it, unreadable paths).

    Unreadable files are returned rather than skipped: a gate that passed over
    a file it could not decode would let a copy hide behind an encoding error,
    and would then report coverage it did not have.
    """
    table: dict[str, list[tuple[str, int]]] = {}
    unreadable: list[str] = []
    for rel in rels:
        try:
            text = (scan_root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            unreadable.append(f"{rel}: unreadable, so it cannot be checked ({exc})")
            continue
        for line, block in _blocks(text):
            key = _normalise(block)
            if len(key) < MIN_CHARS or len(key.split()) < MIN_WORDS:
                continue
            table.setdefault(key, []).append((rel, line))
    return table, unreadable


def _excerpt(key: str, width: int = 90) -> str:
    return key if len(key) <= width else key[:width].rstrip() + "..."


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    spine = manifest["spine"]
    report = Report(GATE_ID, RULE_NOTE)

    _all, from_index = candidates(scan_root, manifest)
    spine_notes = notes(scan_root, manifest, scopes=("spine",))
    spec_files = [
        rel for rel in notes(scan_root, manifest, scopes=("planning",)) if _is_spec(rel)
    ]
    comp_notes = notes(scan_root, manifest, scopes=("components",))

    spine_blocks, spine_unreadable = _index_blocks(scan_root, spine_notes)
    spec_blocks, spec_unreadable = _index_blocks(scan_root, spec_files)
    comp_blocks, comp_unreadable = _index_blocks(scan_root, comp_notes)

    for message in sorted({*spine_unreadable, *spec_unreadable, *comp_unreadable}):
        report.fail(message)

    # Every crossing pair is reported, in one run: a contributor removing a copy
    # needs both ends of each pair, not the first one the walk happened to find.
    for key in sorted(set(spine_blocks) & set(spec_blocks)):
        for note_path, note_line in spine_blocks[key]:
            for spec_path, spec_line in spec_blocks[key]:
                report.fail(
                    f"{note_path}:{note_line}: block is a copy of "
                    f"{spec_path}:{spec_line} -- delete the copy and link to the "
                    f'specification that owns it: "{_excerpt(key)}"'
                )

    # A component note copying either of the other two sides. The remedy differs
    # per owner, so it is named per owner rather than generically.
    for other_blocks, remedy in (
        (spine_blocks, "link the note that owns it"),
        (spec_blocks, "link the specification that owns it"),
    ):
        for key in sorted(set(comp_blocks) & set(other_blocks)):
            for comp_path, comp_line in comp_blocks[key]:
                for owner_path, owner_line in other_blocks[key]:
                    report.fail(
                        f"{comp_path}:{comp_line}: block is a copy of "
                        f"{owner_path}:{owner_line} -- delete the copy and "
                        f'{remedy}: "{_excerpt(key)}"'
                    )

    for _subject in [*spine_notes, *spec_files, *comp_notes]:
        report.examine(_subject)
    report.coverage(
        covered=[spine, "openspec/**/specs/**/*.md", "per-component roots"],
        excluded=[*exempt_roots(manifest), *scan_excludes(manifest)],
        kind="note",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    print(
        f"  subjects: {len(spine_notes)} spine note(s), {len(spec_files)} "
        f"specification file(s), {len(comp_notes)} component note(s); blocks "
        f"compared across the three boundaries at >= {MIN_CHARS} chars and "
        f">= {MIN_WORDS} words"
    )
    # Stated on every run, passing included, so the result is not over-read:
    # see the module docstring for who owns the case this cannot decide.
    print(
        "  decides: exact normalised block match (copy-paste). does NOT decide: "
        "paraphrase, or a restatement drifting from its owner -- owned by "
        "authority precedence and by review."
    )
    return report.finish(report_only=report_only)


main_guard(run)
