#!/usr/bin/env python3
"""Gate: every capability has a concept note, and its dependency links are complete.

Enforces docs/knowledge-base -- "Each capability has a concept note":

  1. **Bijection.** A specification whose capability has no concept note fails,
     naming the capability. A concept note for a capability with no
     specification fails too -- a note describing a capability nobody specified
     is a note whose subject does not exist.

  2. **Dependency correspondence.** Every capability a specification names in
     backticks is a dependency, and the concept note must link to that
     capability's own note. There are eighty such references across ten
     specifications, and each one is a real edge in the dependency graph.

## Why the graph lives here and not in the specifications

The obvious move is to turn those eighty backticked strings into links inside
the specifications, putting the graph in the authoritative files. RDV5 defers
that: the specifications are the one artifact whose format an external tool
validates, and the whole plan depends on them (RDV5, written when it held 709 tasks). Building the graph one layer out gets
the whole navigational payoff -- "what depends on `tunnel/listener`" is answered
by that note's inbound links -- at no risk to those sixteen files.

The correspondence is therefore gated in the direction that can drift. A
specification gaining a reference to a capability its concept note does not link
fails; the specification itself is never edited to satisfy this gate.

## What it does not decide

Whether a *link* in a concept note is a real dependency. A note may link a
capability its specification never names -- an editorially useful pointer -- and
that is not a failure. The check is one-directional by design: every reference
in the spec must appear in the note, not the reverse.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "capability-notes"
RULE_NOTE = "docs/method/rules/capability-notes.md"

CAP_REF = re.compile(r"`([a-z]+/[a-z][a-z-]*)`")
LINK = re.compile(r"\]\(([^)]+)\)")


def note_name(cap_id: str) -> str:
    return cap_id.replace("/", "-") + ".md"


def discover_specs(root: Path, manifest: dict) -> dict[str, Path]:
    glob = manifest["capability_notes"]["spec_glob"]
    found = {}
    for p in sorted(root.glob(glob)):
        cap = f"{p.parent.parent.name}/{p.parent.name}"
        found[cap] = p
    return found


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["capability_notes"]
    notes_dir = scan_root / cfg["dir"]
    report = Report(GATE_ID, RULE_NOTE)

    specs = discover_specs(scan_root, manifest)
    have_notes = {
        p.name: p for p in sorted(notes_dir.glob("*.md")) if p.name != "index.md"
    }

    # (1) bijection, both directions
    for cap in sorted(specs):
        if note_name(cap) not in have_notes:
            report.fail(
                f"{cap}: specification exists at {specs[cap].relative_to(scan_root)} "
                f"with no concept note at {cfg['dir']}/{note_name(cap)}"
            )
    expected = {note_name(c) for c in specs}
    for name in sorted(have_notes):
        if name not in expected:
            report.fail(
                f"{cfg['dir']}/{name}: concept note for a capability with no "
                f"specification -- its subject does not exist"
            )

    # (2) dependency correspondence, spec -> note
    refs_total = refs_linked = 0
    for cap, spec_path in sorted(specs.items()):
        name = note_name(cap)
        note_path = have_notes.get(name)
        if note_path is None:
            continue
        spec_text = spec_path.read_text(encoding="utf-8")
        note_text = note_path.read_text(encoding="utf-8")
        linked = {t.split("/")[-1] for t in (m.group(1) for m in LINK.finditer(note_text))}
        named = sorted(
            {m.group(1) for m in CAP_REF.finditer(spec_text)} & set(specs) - {cap}
        )
        for dep in named:
            refs_total += 1
            if note_name(dep) in linked:
                refs_linked += 1
            else:
                report.fail(
                    f"{cfg['dir']}/{name}: its specification names dependency "
                    f"`{dep}` but the note does not link "
                    f"{cfg['dir']}/{note_name(dep)}"
                )

    # (3) the declared ceiling -- a concept note must be readable whole before its
    # specification is opened, which is the only reason the layer earns its cost.
    ceiling = cfg.get("ceiling_lines")
    over = 0
    if ceiling:
        for name, note_path in sorted(have_notes.items()):
            n_lines = len(note_path.read_text(encoding="utf-8").splitlines())
            if n_lines > ceiling:
                over += 1
                report.fail(
                    f"{cfg['dir']}/{name}: {n_lines} lines, over the declared "
                    f"ceiling of {ceiling} -- a note that cannot be read whole "
                    f"before its specification is not a middle layer"
                )

        for _subject in specs:
            report.examine(_subject)
    report.coverage(
        covered=[cfg["dir"], "openspec/**/specs"],
        excluded=["the specifications themselves (never edited to satisfy this gate)"],
        kind="specification",
        source="scan",
        scan_root=scan_root,
    )
    print(
        f"  capabilities: {len(specs)} | concept notes: {len(have_notes)} | "
        f"distinct dependency edges: {refs_linked}/{refs_total} linked | "
        f"ceiling {cfg.get('ceiling_lines')} lines, {over} over"
    )
    return report.finish(report_only=report_only)


main_guard(run)
