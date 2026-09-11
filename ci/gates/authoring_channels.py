#!/usr/bin/env python3
"""Gate: every convention reaches BOTH authoring channels, keyed on one enumeration.

Enforces docs/knowledge-base -- "Authoring guidance is applied at authoring
time": the conventions are supplied where the author reads them rather than left
to review, through two channels, keyed on one enumeration so a convention added
to the gates without reaching both fails.

## Why two channels rather than one

RDV10, and it was a correction. The plan originally named a single hook:
`openspec/config.yaml`. But that file's `rules:` block is keyed per *openspec
artifact* -- proposal, specs, design, tasks -- so it cannot express an obligation
on a note at all, and a note author never opens it. The single substitution the
whole change rests on could not reach the author it most needed to reach.

So: the planning-artifact channel is `openspec/config.yaml` (including its
`operations:` block, which governs the apply and archive loops that will touch
this vault hundreds of times across 709 tasks), and the note-authoring channel is
a generated note the entry files link as their first hop.

## The failure this gate actually caught

Writing the config by hand produced a YAML indentation error, and openspec
responded by printing a warning and **ignoring the entire file**. An unparsed
config is indistinguishable from an empty one to anyone who does not read stderr,
so this gate asserts the config parses and that every convention id is present in
it -- not merely that the file exists.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "authoring-channels"
RULE_NOTE = "docs/method/rules/authoring-channels.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    items = {k: v for k, v in manifest["conventions"]["items"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)

    note_rel = "docs/method/conventions.md"
    cfg_rel = "openspec/config.yaml"
    note_path, cfg_path = scan_root / note_rel, scan_root / cfg_rel

    note_text = note_path.read_text(encoding="utf-8") if note_path.is_file() else ""
    cfg_text = cfg_path.read_text(encoding="utf-8") if cfg_path.is_file() else ""
    if not note_text:
        report.fail(f"{note_rel}: the note-authoring channel does not exist")
    if not cfg_text:
        report.fail(f"{cfg_rel}: the planning-artifact channel does not exist")

    # Read the conventions back THROUGH THE TOOL rather than out of the file.
    # This is the requirement's actual wording -- "the conventions are present in
    # the context it reads" -- and it subsumes a parse check: an unparseable
    # config makes the tool print a warning and ignore the whole file, so the
    # guidance comes back empty and every convention is reported missing. Reading
    # the file's text instead would have passed on exactly that state, because
    # the ids are still in the bytes.
    #
    # No third-party YAML library: the Python conventions this change wrote say
    # standard library only, and the tool is a better authority on its own format
    # than a second parser would be.
    delivered = ""
    if cfg_text:
        listing = subprocess.run(
            ["openspec", "list", "--json"], capture_output=True, text=True, cwd=str(scan_root)
        ).stdout
        change = None
        try:
            change = json.loads(listing[listing.index("{"):])["changes"][0]["name"]
        except Exception:
            change = None
        if change:
            got = subprocess.run(
                ["openspec", "instructions", "apply", "--change", change, "--json"],
                capture_output=True, text=True, cwd=str(scan_root),
            ).stdout
            try:
                d = json.loads(got[got.index("{"):])
                delivered = json.dumps(
                    [d.get("context") or "", d.get("operationGuidance") or []]
                )
            except Exception:
                delivered = ""
            if not delivered.strip('[]"\n ,'):
                report.fail(
                    f"{cfg_rel}: the planning tool delivers no context and no "
                    f"guidance -- either it is empty or it could not be parsed, and "
                    f"the tool warns and IGNORES an unparseable file, which is "
                    f"silently identical to no configuration at all"
                )

    # Every convention reaches both channels, and names a gate that exists.
    gates = {p.stem for p in (scan_root / "ci" / "gates").glob("*.py")}
    missing_note = missing_cfg = 0
    for cid, it in sorted(items.items()):
        if note_text and cid not in note_text:
            missing_note += 1
            report.fail(f"convention '{cid}': absent from the note-authoring channel ({note_rel})")
        if cfg_text and cid not in delivered:
            missing_cfg += 1
            report.fail(
                f"convention '{cid}': the planning tool does not deliver it -- "
                f"present in {cfg_rel} is not the same as reaching the author"
            )
        if it.get("gate") not in gates:
            report.fail(
                f"convention '{cid}': names gate 'ci/gates/{it.get('gate')}.py', "
                f"which the repository does not run"
            )

    # The entry files must link the note-authoring channel, or nobody reaches it.
    for entry in [f for f in manifest["entry_files"]["files"] if not f.startswith("_")]:
        p = scan_root / entry
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if "conventions.md" not in text and "rule-index.md" not in text:
            report.fail(
                f"{entry}: links neither the conventions note nor the rule index -- "
                f"a channel no entry file points at is a channel nobody reads"
            )

        for _subject in items:
            report.examine(_subject)
    report.coverage(
        covered=[note_rel, cfg_rel],
        excluded=["review (which is what these channels exist to replace)"],
        kind="convention",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  conventions: {len(items)} | missing from note: {missing_note} | "
        f"missing from config: {missing_cfg} | gates named: "
        f"{len({i['gate'] for i in items.values()})}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
