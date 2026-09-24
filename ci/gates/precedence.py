#!/usr/bin/env python3
"""Gate: the authority precedence is stated in exactly one location.

Enforces docs/knowledge-base -- "Authority precedence is stated and enforced":
a single ordered precedence is stated in ONE location, and the gate fails when it
appears elsewhere with differing content.

## What "stated" means here, and why it is an exact marker

A first version of this gate looked for three or more ordered layer names. That
is unusable: "contract", "specifications", "decisions" and "notes" are ordinary
words in this vocabulary, so almost every capability note enumerates three of
them incidentally and would have been reported as restating the precedence. A
gate with that false-positive rate gets disabled within a week, and then the
requirement has no enforcement at all.

So the canonical statement carries an exact marker line inside a fenced block,
and the gate looks for THAT. Restating the order means reproducing the marker;
mentioning a layer in prose does not. The check is then exact in both directions.

Note what remains permitted, deliberately: a note saying "the specification wins
where this note and it disagree" is *deferring* to the order, not restating it,
and every spine note describing behaviour is required to say exactly that.

## What it does not decide

Whether a restatement AGREES with the canonical one. Two orderings that differ
are both caught, because any second enumeration fails regardless of content --
which is stricter than the requirement's "with differing content" and cheaper
than deciding agreement over prose. Stated so the strictness is a choice rather
than a bug.
"""

from __future__ import annotations

from pathlib import Path

from _common import Report, load_manifest, main_guard, notes, repo_root

GATE_ID = "precedence"
RULE_NOTE = "docs/method/authority-precedence.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["precedence"]
    canonical = cfg["canonical_note"]
    layers = [l for l in cfg["layers"] if not l.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)

    marker = cfg["marker"]
    canon_path = scan_root / canonical
    if not canon_path.is_file():
        report.fail(
            f"{canonical}: the declared canonical precedence note does not exist"
        )
    else:
        text = canon_path.read_text(encoding="utf-8")
        if marker not in text:
            report.fail(
                f"{canonical}: the canonical note does not carry the precedence "
                f"marker '{marker}'"
            )
        missing = [l for l in layers if l.lower() not in text.lower()]
        if missing:
            report.fail(
                f"{canonical}: the canonical statement omits layer(s): "
                f"{', '.join(missing)}"
            )

    restated = 0
    for rel in notes(scan_root, manifest):
        if rel == canonical:
            continue
        path = scan_root / rel
        if not path.is_file():
            continue
        if marker in path.read_text(encoding="utf-8"):
            restated += 1
            report.fail(
                f"{rel}: carries the authority-precedence marker '{marker}' -- the "
                f"order is stated in {canonical}; link it rather than restating it"
            )

        for _subject in layers:
            report.examine(_subject)
    report.coverage(
        covered=[canonical, "every other note"],
        excluded=["a note deferring to its owner without enumerating the order"],
        kind="layer",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  layers: {len(layers)} | canonical: {canonical} | restatements: {restated}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
