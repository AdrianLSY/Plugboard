#!/usr/bin/env python3
"""Gate: every convention reaches BOTH authoring channels, and they agree.

Enforces docs/knowledge-base -- "Authoring guidance is applied at authoring
time": the conventions are supplied where the author reads them rather than left
to review, through two channels, keyed on one enumeration so a convention added
to the gates without reaching both fails, and so that the two cannot state
different conventions.

## What it does not decide

Whether a convention is the right convention, and whether an author read it. It
decides that both channels carry every id and state the same thing for each.

## Why two channels rather than one

RDV10, and it was a correction. The plan originally named a single hook:
`openspec/config.yaml`. But that file's `rules:` block is keyed per *openspec
artifact* -- proposal, specs, design, tasks -- so it cannot express an obligation
on a note at all, and a note author never opens it. The single substitution the
whole change rests on could not reach the author it most needed to reach.

So: the planning-artifact channel is `openspec/config.yaml` (including its
`operations:` block, which governs the apply and archive loops that will touch
this vault once per task across the whole plan), and the note-authoring channel is
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

# The shape the planning-artifact channel states a convention in. Keyed on the id
# so the statement and the gate can be compared against the single source rather
# than merely looked for.
CONVENTION_LINE = re.compile(
    r"note convention \[([^\]]+)\]:\s*(.*?)\s*\(gate: ci/gates/([A-Za-z0-9_]+)\.py\)\s*$"
)


def _openspec(scan_root: Path, *args: str) -> str | None:
    """Run the planning tool in `scan_root`; None when it is not installed.

    Absence is returned rather than raised so the caller can report it as a
    failure naming the tool. A traceback names a Python file; the fact a
    contributor needs is that a binary is missing. It is never a pass: an
    absent tool delivers no conventions, which is indistinguishable from a
    config that delivers none -- the exact state this gate exists to catch.
    """
    try:
        return subprocess.run(
            ["openspec", *args], capture_output=True, text=True, cwd=str(scan_root)
        ).stdout
    except FileNotFoundError:
        return None


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    items = {
        k: v
        for k, v in manifest["conventions"]["items"].items()
        if not k.startswith("_")
    }
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
        listing = _openspec(scan_root, "list", "--json")
        if listing is None:
            report.fail(
                "the planning tool `openspec` is not on PATH -- this gate reads "
                "the conventions back THROUGH the tool, so an absent binary "
                "delivers nothing and is silently identical to a config that "
                "delivers nothing, which is the state this gate exists to catch. "
                "Install it with `npm install -g @fission-ai/openspec` (README.md "
                "names the version CI pins)"
            )
            listing = ""
        change = None
        try:
            change = json.loads(listing[listing.index("{") :])["changes"][0]["name"]
        except Exception:
            change = None
        if change:
            got = (
                _openspec(
                    scan_root, "instructions", "apply", "--change", change, "--json"
                )
                or ""
            )
            try:
                d = json.loads(got[got.index("{") :])
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

    # What each channel actually STATES, not merely which ids it mentions. The
    # generated channel cannot drift -- ci/gates/index_drift.py pins it against a
    # fresh regeneration -- so a disagreement is always the hand-maintained
    # config's, and naming both channels is what lets the author see which.
    stated: dict[str, tuple[str, str]] = {}
    if delivered:
        try:
            guidance = json.loads(delivered)[1]
        except (ValueError, IndexError):
            guidance = []
        for line in guidance:
            m = CONVENTION_LINE.match(str(line).strip())
            if m:
                stated[m.group(1)] = (m.group(2), m.group(3))

    # Every convention reaches both channels, and names a gate that exists.
    gates = {p.stem for p in (scan_root / "ci" / "gates").glob("*.py")}
    missing_note = missing_cfg = 0
    for cid, it in sorted(items.items()):
        if note_text and cid not in note_text:
            missing_note += 1
            report.fail(
                f"convention '{cid}': absent from the note-authoring channel ({note_rel})"
            )
        if cfg_text and cid not in delivered:
            missing_cfg += 1
            report.fail(
                f"convention '{cid}': the planning tool does not deliver it -- "
                f"present in {cfg_rel} is not the same as reaching the author"
            )
        elif cfg_text and cid not in stated:
            report.fail(
                f"convention '{cid}': {cfg_rel} delivers it in a form this gate cannot "
                f"read against the source -- a line the comparison cannot parse is a "
                f"statement nothing holds to {note_rel}; expected "
                f"'note convention [{cid}]: <statement> (gate: ci/gates/<module>.py)'"
            )
        elif cfg_text:
            statement, gate = stated[cid]
            if statement != it["statement"]:
                report.fail(
                    f"convention '{cid}': the two channels state different conventions -- "
                    f"{note_rel} carries {it['statement']!r} and {cfg_rel} delivers "
                    f"{statement!r}; both are keyed on one enumeration, so they cannot disagree"
                )
            if gate != it["gate"]:
                report.fail(
                    f"convention '{cid}': the two channels name different gates -- "
                    f"{note_rel} names 'ci/gates/{it['gate']}.py' and {cfg_rel} delivers "
                    f"'ci/gates/{gate}.py'"
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
