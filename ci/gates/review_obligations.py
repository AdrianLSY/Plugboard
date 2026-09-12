#!/usr/bin/env python3
"""Gate: an enumeration stated once propagates to every artifact required to name it.

Enforces docs/code-standards -- "The review obligations are stated in one
location and enumerated". Three enumerations live in one note: the
change-description questions, the review checklist, and the closed set of
blocking objections. Every other artifact that needs one of them LINKS it; the
one artifact required to enumerate it -- `CONTRIBUTING.md`, which a contributor
reads before they read the spine -- names each item without restating it.

The checkable form of "stated once" is PROPAGATION. "Nobody copied the list" is
not decidable over prose, and a gate that tried would fire on every note that
mentions a checklist. What is decidable is the other direction: adding an item to
a canonical enumeration fails every artifact required to enumerate it, until that
artifact names the new item. A list that cannot silently fall behind has nothing
to drift from.

Three cases, all three failing:

  1. An item of a canonical enumeration that a required enumerator does not name,
     naming the item, the enumerator and the anchor the item is stated at.
  2. A declared enumeration whose heading the source note no longer carries --
     the declaration outlived its subject, or the note was reorganised and the
     check quietly stopped covering it.
  3. A declared enumerator that does not exist.

## What an item's NAME is, and why it is derived rather than declared

The key is taken from the canonical enumeration itself, in this order: the item's
leading bold phrase; failing that, its leading link text; failing that, the text
up to its first em dash or comma. Declaring the keys in ci/vault.json instead
would be a second encoding of the list -- the exact defect this rule exists to
prevent, reappearing in the check that enforces it.

That ordering is not arbitrary. Every item of the two prose enumerations opens
with a bold phrase, and thirteen of the sixteen blocking objections open with a
link to the note stating the rule. The three that do neither are prose whose
identity ends at an em dash or the first clause boundary, which is where the
truncation lands.

## What it does not decide

Whether an enumerator names the items in the right ORDER, whether it names an
item that has since been removed from the canonical list, or whether the sentence
it wraps the name in is true. The first two are a stale-entry check that needs a
notion of "this file's list" the file does not carry as data; the third is
review's. A green run means no item is missing, not that the enumerator is right.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "review-obligations"
RULE_NOTE = "docs/code/rules/review-obligations-single-sourced.md"

HEADING = re.compile(r"^(#+)\s+(.*?)\s*$")
ITEM = re.compile(r"^(\d+)\.\s+(.*)$")
BOLD_LEAD = re.compile(r"^\*\*(.+?)\*\*")
LINK_LEAD = re.compile(r"^\[([^\]]+)\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
EMPHASIS = str.maketrans("", "", "*_`")


def _normalise(text: str) -> str:
    text = LINK.sub(r"\1", text)
    text = text.translate(EMPHASIS)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _section(lines: list[str], heading: str) -> list[str] | None:
    """The lines under `heading`, up to the next heading of the same or higher level."""
    for index, line in enumerate(lines):
        m = HEADING.match(line)
        if not m or m.group(2) != heading:
            continue
        level = len(m.group(1))
        out = []
        for follow in lines[index + 1:]:
            m2 = HEADING.match(follow)
            if m2 and len(m2.group(1)) <= level:
                break
            out.append(follow)
        return out
    return None


def _items(section: list[str]) -> list[tuple[int, str]]:
    """(number, joined raw text) for each top-level ordered item."""
    found: list[tuple[int, list[str]]] = []
    for line in section:
        m = ITEM.match(line)
        if m:
            found.append((int(m.group(1)), [m.group(2)]))
        elif found and line.startswith(("   ", "\t")) and line.strip():
            found[-1][1].append(line.strip())
        elif not line.strip():
            continue
        else:
            # A paragraph at the left margin ends the list.
            if found and not ITEM.match(line):
                pass
    return [(n, " ".join(parts)) for n, parts in found]


def _key(raw: str) -> str:
    """The item's name: leading bold, else leading link text, else the lead clause."""
    m = BOLD_LEAD.match(raw)
    if m:
        return _normalise(m.group(1)).rstrip(".")
    m = LINK_LEAD.match(raw)
    if m:
        return _normalise(m.group(1)).rstrip(".")
    text = _normalise(raw)
    for cut in ("—", ","):
        if cut in text:
            text = text.split(cut, 1)[0]
            break
    return text.strip().rstrip(".")


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["review_obligations"]
    source_rel = cfg["source"]
    declared = [e for e in cfg["enumerations"] if not e.get("heading", "").startswith("_")]
    enumerators = [e for e in cfg["enumerators"] if not e.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)

    source = scan_root / source_rel
    if not source.is_file():
        report.fail(
            f"{source_rel}: the note declared to single-source the review "
            f"obligations is absent -- every enumerator's obligation is keyed on it"
        )
        report.coverage(covered=[], excluded=[], kind="enumerated item",
                        source="manifest", scan_root=scan_root)
        return report.finish(report_only=report_only)

    lines = source.read_text(encoding="utf-8").splitlines()
    bodies = {}
    for rel in enumerators:
        path = scan_root / rel
        # (3) a declared enumerator that is not there.
        if not path.is_file():
            report.fail(
                f"{rel}: declared as an artifact required to enumerate the review "
                f"obligations, and absent -- a propagation check with no "
                f"destination enforces nothing"
            )
            continue
        bodies[rel] = _normalise(path.read_text(encoding="utf-8"))

    total = 0
    for entry in declared:
        heading, anchor = entry["heading"], entry["anchor"]
        section = _section(lines, heading)
        # (2) a declared enumeration the source note no longer carries.
        if section is None:
            report.fail(
                f"{source_rel}: no heading '{heading}' -- ci/vault.json declares it "
                f"a canonical enumeration, so either the note was reorganised and "
                f"this check stopped covering it, or the declaration is stale"
            )
            continue
        for number, raw in _items(section):
            key = _key(raw)
            if not key:
                continue
            total += 1
            subject = f"{heading} item {number}"
            report.examine(subject)
            # (1) the propagation direction.
            for rel, body in bodies.items():
                if key not in body:
                    report.fail(
                        f"{rel}: does not name {heading.lower()} item {number}, "
                        f'"{raw[:70]}" -- link it at {source_rel}#{anchor}; an '
                        f"enumeration that can silently fall behind is a second "
                        f"copy waiting to happen"
                    )

    report.coverage(
        covered=[f"{source_rel}#{e['anchor']}" for e in declared],
        excluded=["order", "a stale entry the canonical list has dropped"],
        kind="enumerated item",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  enumerations: {len(declared)} declared | items: {total} | "
        f"enumerators: {len(bodies)} of {len(enumerators)} present"
    )
    return report.finish(report_only=report_only)


main_guard(run)
