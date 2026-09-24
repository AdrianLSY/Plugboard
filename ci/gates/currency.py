#!/usr/bin/env python3
r"""Gate: the documentation reflects the current state, in BOTH directions.

Enforces docs/knowledge-base -- "The documentation reflects the current state",
which states four checkable properties rather than an intention:

  1. A note whose subject was removed is deleted or marked superseded.
  2. A note marked superseded names what replaced it.
  3. A note describing something not yet built is marked planned and links the
     work that builds it, naming its subject as a path the gate can test.
  4. A planned marker is RETIRED once its subject exists.

## Why the fourth property is the one that matters

An adversarial review of the plan found the requirement ran one way only. This
change lands *before* the task that creates `contract/`, `proxy/`, `sidecar/`,
`terminator/` and `conformance/`, so nearly the whole spine is stamped planned
against directories that appear almost immediately afterwards -- and nothing
would ever un-stamp them. `status: planned` would become the default value across
the vault at the exact moment CI started passing, which is the value an agent
reads to decide whether a note can be trusted.

A currency guarantee enforced only in the direction that is empty today would
have reported green over a vault that had gone stale everywhere.

## What makes the marker decidable, and why it is not a required subject path

The requirement offers two hooks: a planned note fails once "its named subject is
present in the tree, OR its linked task is complete". A first version of this gate
demanded the subject path from every planned note, which is wrong for the
capability notes: a capability's subject is not one file, and forcing each note to
nominate one would have produced eighteen arbitrary paths chosen to satisfy a
check.

So the mandatory part is the LINK to the work that builds it -- every planned note
has one, and it is what a reader needs anyway. On top of that:

  * a `Planned subject: \`path\`` line is optional, and checked for existence when
    present, which is the right hook for a note about one artifact;
  * a note naming a task identifier has that task's checkbox read in the linked
    task list, which is the right hook for a note about a body of work.

Both directions therefore fire without anyone nominating a fictional path.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, notes, repo_root, subject_source

GATE_ID = "currency"
RULE_NOTE = "docs/method/rules/currency-both-directions.md"

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
# `status: planned` notes declare their subject with this marker.
SUBJECT = re.compile(r"^\s*(?:\*\*)?Planned subject(?:\*\*)?:\s*`([^`]+)`", re.M)
SUPERSEDED_BY = re.compile(
    r"^\s*(?:\*\*)?Superseded by(?:\*\*)?:\s*\[[^\]]+\]\(([^)]+)\)", re.M
)
LINK = re.compile(r"\]\(([^)]+)\)")


def field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(\S+)\s*$", fm, re.M)
    return m.group(1) if m else None


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    spine = manifest["spine"]
    report = Report(GATE_ID, RULE_NOTE)

    planned = superseded = current = 0
    for rel in notes(scan_root, manifest, scopes=("spine", "components")):
        path = scan_root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        m = FM.match(text)
        status = field(m.group(1), "status") if m else None

        if status == "superseded":
            superseded += 1
            report.examine(rel)
            if not SUPERSEDED_BY.search(text):
                report.fail(
                    f"{rel}: marked superseded and names no replacement -- add a "
                    f"`Superseded by: [name](path)` line, or a reader has a dead end"
                )
            continue

        if status != "planned":
            current += 1
            report.examine(rel)
            continue

        planned += 1
        report.examine(rel)
        links = [m2.group(1) for m2 in LINK.finditer(text)]
        # (3) mandatory: a link to the work that builds it.
        task_links = [l for l in links if "tasks.md" in l or "changes/" in l]
        if not task_links:
            report.fail(
                f"{rel}: marked planned and links no work that builds it -- a "
                f"planned marker with no route to enforcement is a permanent one"
            )
        # (4a) an optional named subject is checked for existence.
        subj = SUBJECT.search(text)
        if subj and (scan_root / subj.group(1)).exists():
            report.fail(
                f"{rel}: still marked planned, but its subject "
                f"'{subj.group(1)}' now exists -- retire the marker; a stale "
                f"planned marker is the value an agent reads to decide whether a "
                f"note can be trusted"
            )
        # (4b) a named task identifier has its checkbox read -- resolved against
        # the task list THAT reference links, not against every list the note
        # links. Two changes are in flight with overlapping identifiers, so an
        # unscoped read reported "rebuild-plugboard task 1.1" as complete because
        # a *different* change's 1.1 was done. A task id means nothing without
        # the list it belongs to.
        for label, target in re.findall(
            r"\[([^\]]*task \d+\.\d+[a-z]?[^\]]*)\]\(([^)]+)\)", text
        ):
            m3 = re.search(r"task (\d+\.\d+[a-z]?)", label)
            if not m3:
                continue
            tid = m3.group(1)
            tp = (path.parent / target.split("#")[0]).resolve()
            if not tp.is_file() or tp.name != "tasks.md":
                continue
            for line in tp.read_text(encoding="utf-8").splitlines():
                if line.startswith(f"- [x] {tid} "):
                    report.fail(
                        f"{rel}: still marked planned and names {label!r}, which is "
                        f"complete in {tp.parent.name} -- retire the marker or "
                        f"update the sentence"
                    )
                    break

    report.coverage(
        covered=[spine, "per-component roots"],
        excluded=["planning directories (format owned by an external tool)"],
        kind="note",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(f"  notes: {current} current, {planned} planned, {superseded} superseded")
    return report.finish(report_only=report_only)


main_guard(run)
