#!/usr/bin/env python3
"""Gate: an artifact obliged to enumerate a review obligation names every item.

Enforces docs/code-standards -- "The review obligations are stated in one
location and enumerated":

  * every item of every canonical enumeration is cited by each artifact declared
    to carry that obligation;
  * an item present in the canonical note and absent from an obliged artifact
    fails, naming the artifact, the enumeration and the item;
  * a canonical enumeration that yields no items fails, because a heading that
    stopped matching would otherwise silently discharge the whole obligation.

## Why propagation rather than wording

A checklist is the kind of text that gets pasted into whatever artifact needs it
next -- a CONTRIBUTING.md, a PR template, an agent context file -- and the copies
then diverge silently, because nothing fails when one is left behind. The prior
art shows both halves: `ws_check` appears nowhere in the 457 lines documenting
its own protocol, and where both ends WERE documented they had already drifted,
the Go side hardcoding a three-second check timeout against a configurable five
on the Elixir side (`websocket.go:339`).

So the checkable form is propagation, not equality. An obliged artifact cites an
item BY NUMBER and links to the anchor that owns it; it never carries the item's
text, because a second copy of the wording is what ci/gates/duplication.py
already refuses. Adding item 10 to a canonical enumeration fails every obliged
artifact until each one cites item 10 -- and the failure lists each artifact
still missing it, so the fix is a list rather than a search.

## What it does not decide

Whether the label an artifact puts beside a number is a good summary of the item.
That is wording, and wording is deliberately not this rule's subject: one copy
and a link has no drift to detect, which is the whole reason the enumerations are
single-sourced. A label that misleads is a review comment, not a build failure.

## Why the items are read rather than declared

ci/vault.json names the canonical note, the obliged artifacts and the citation
form. It does NOT name how many items an enumeration holds. A cardinal there
would be a second encoding of what the canonical note already states, and the two
would drift -- which is the defect this repository has already spent three
commits removing from its own prose.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "review-obligations"
RULE_NOTE = "docs/code/rules/review-obligations-single-sourced.md"

# A top-level ordered-list item: "1. ", "12. " at the start of a line.
ITEM = re.compile(r"^(\d+)\.\s", re.M)


def section(body: str, heading: str) -> str:
    """The text under `heading`, up to the next heading of the same or higher level.

    Matched on the heading TEXT rather than on a declared level, so promoting or
    demoting the section does not silently empty it -- the empty-section case
    below is what catches a heading that stopped matching altogether.
    """
    m = re.search(rf"^(#{{1,6}})\s+{re.escape(heading)}\s*$", body, re.M)
    if not m:
        return ""
    level = len(m.group(1))
    rest = body[m.end() :]
    nxt = re.search(rf"^#{{1,{level}}}\s+\S", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["review_obligations"]
    canonical_rel = cfg["canonical"]
    obliged = list(cfg["required_in"])
    enums = {k: v for k, v in cfg["enumerations"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)
    report.examine(canonical_rel)

    canonical = scan_root / canonical_rel
    if not canonical.is_file():
        report.fail(
            f"{canonical_rel}: the note ci/vault.json declares canonical is absent, "
            f"so every enumeration it owns is unstated and nothing can be checked "
            f"against it"
        )
        return report.finish(report_only=report_only)

    body = canonical.read_text(encoding="utf-8")

    # Read each obliged artifact once; an absent one fails against every
    # enumeration at once rather than once per item.
    texts: dict[str, str | None] = {}
    for rel in obliged:
        report.examine(rel)
        path = scan_root / rel
        texts[rel] = path.read_text(encoding="utf-8") if path.is_file() else None
        if texts[rel] is None:
            report.fail(
                f"{rel}: declared to carry the review obligations and absent -- "
                f"an obligation with no artifact under it is not enforced by this "
                f"gate passing"
            )

    for key, spec in sorted(enums.items()):
        heading = spec["heading"]
        form = spec["citation"]
        items = [int(n) for n in ITEM.findall(section(body, heading))]

        if not items:
            report.fail(
                f"{canonical_rel}: the '{heading}' enumeration yields no numbered "
                f"items -- a heading that stopped matching discharges the whole "
                f"obligation silently, so an empty enumeration is a failure rather "
                f"than a vacuous pass"
            )
            continue

        for rel, text in sorted(texts.items()):
            if text is None:
                continue
            missing = [
                n for n in items if form.format(n=n).lower() not in text.lower()
            ]
            for n in missing:
                report.fail(
                    f"{rel}: does not cite '{form.format(n=n)}' -- "
                    f"{canonical_rel} '{heading}' states it and this artifact is "
                    f"declared to enumerate that set, so the copy here is behind "
                    f"the canonical one"
                )

    report.coverage(
        covered=[canonical_rel, *sorted(obliged)],
        excluded=[
            "the wording an obliged artifact puts beside an item number "
            "(single-sourced, so there is no second copy to diverge)"
        ],
        kind="artifact",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  canonical: {canonical_rel} | obliged: {', '.join(sorted(obliged))} | "
        f"enumerations: {', '.join(sorted(enums))}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
