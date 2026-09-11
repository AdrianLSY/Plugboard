#!/usr/bin/env python3
"""Gate: exactly one decision register, no reused identifier, nothing lost on removal.

Enforces docs/knowledge-base -- "There is exactly one decision register":

  1. ONE REGISTER. An identifier in the installation's unnamespaced `D<n>`
     sequence, introduced anywhere other than the declared register, fails --
     whatever file it appears in, including a change's own design artifact.
     Citing an identifier the register holds is NOT introducing one.
  2. NAMESPACED PER-CHANGE DECISIONS PASS and are not treated as a register.
  3. NO REUSE. Assigning an identifier a superseded register used fails, naming
     the identifier and its former meaning.
  4. NOTHING LOST ON REMOVAL. A superseded register may not be removed while it
     records a decision recorded nowhere else, and the check is an enumeration
     over the declared table rather than an inspection of prose.

## Why the subject is declared rather than inferred

Two scopings were available and both are wrong. Scoped to a literal path, this
gate fails the tree the moment the change's own artifacts are tracked. Scoped to
"any file named design.md", it licenses every future change to open its own
`D1`-`D10` -- which is exactly how the collision being repaired arose: this
change's own design numbered ten decisions `D1`-`D10` against the register's
`D1`-`D10`, so `D1` meant "vault root is the repository root" in one file and
"three primitives, not twelve protocols" in the other.

So the subject is *an unnamespaced identifier outside the declared register*,
and the register is named in ci/vault.json.

## What "introduced" means, precisely

A heading that assigns an identifier -- `## D13 · ...`, `### D13. ...` -- is an
assignment. An identifier in running prose, a table cell, or backticks is a
citation. This distinction is the whole reason the gate can be strict about
assignment without making the collision table (which must name all fifteen old
identifiers) unwritable.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, candidates, classify, load_manifest, main_guard, repo_root

GATE_ID = "decision-register"
RULE_NOTE = "docs/method/rules/decision-register.md"

# An assignment: a markdown heading whose first token is the identifier. The
# prefix comes from ci/vault.json rather than from this line: a gate never
# decides its own scope, and the rule is that an identifier belongs to a
# declared register, not that one letter is special.
def assignment_re(prefix: str) -> re.Pattern[str]:
    return re.compile(
        r"^#{1,6}\s+(?:\**)([A-Z]{0,6}\d*[A-Z]*)?(" + re.escape(prefix) + r"\d+)\b"
    )


ASSIGNMENT = assignment_re("D")
HEADING = re.compile(r"^#{1,6}\s+(.*)$")
# A namespaced identifier: a change prefix immediately followed by a number.
NAMESPACED = re.compile(r"^#{1,6}\s+(?:\**)([A-Z]{2,6})(\d+)\b")


def _keys(section: dict) -> list[str]:
    return [k for k in section if not k.startswith("_")]


def register_assignments(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ASSIGNMENT.match(line)
        if m and not m.group(1):
            found.add(m.group(2))
    return found


def run(scan_root: Path, report_only: bool) -> int:
    global ASSIGNMENT
    manifest = load_manifest(repo_root())
    reg = manifest["decision_register"]
    ASSIGNMENT = assignment_re(reg["prefix"])
    register_rel = reg["register"]
    assigned = set(reg["assigned"])
    retired = {k: v for k, v in reg["retired"].items() if not k.startswith("_")}
    ns_map = reg["per_change_namespaces"]
    namespaces = {ns_map[k] for k in _keys(ns_map)}
    superseded = {k: v for k, v in reg["superseded_registers"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)

    paths, from_index = candidates(scan_root, manifest)
    paths = [p for p in paths if classify(p, manifest)[0] == "governed"]

    citation_paths = tuple(reg.get("citation_scopes", {}).get("paths", []))

    # (1) and (3): assignments outside the register, and reuse inside it.
    for rel in paths:
        f = scan_root / rel
        if not f.is_file():
            continue
        body = f.read_text(encoding="utf-8")
        in_citation_scope = any(
            rel == p or rel.startswith(p + "/") for p in citation_paths
        )
        links_to_register = register_rel.rsplit("/", 1)[-1] in body and "design.md" in body
        for n, line in enumerate(body.splitlines(), 1):
            m = ASSIGNMENT.match(line)
            if not m or m.group(1):
                continue
            ident = m.group(2)
            if rel != register_rel and in_citation_scope:
                # A note ABOUT the register may head a section with an identifier
                # the register already holds, provided it points at the register.
                # It may not introduce a new one, revive a retired one, or omit
                # the link -- each of those is a second register wearing a
                # decision note's clothes.
                if ident in retired:
                    report.fail(
                        f"{rel}:{n}: heads a section with retired identifier "
                        f"'{ident}' -- {retired[ident]}"
                    )
                elif ident not in assigned:
                    report.fail(
                        f"{rel}:{n}: heads a section with '{ident}', which the "
                        f"declared register does not hold -- a note in a citation "
                        f"scope may cite an existing identifier, never introduce one"
                    )
                elif not links_to_register:
                    report.fail(
                        f"{rel}:{n}: cites '{ident}' in a heading but does not link "
                        f"to the register ({register_rel}) -- a note about a decision "
                        f"must point at it, or it is a restatement"
                    )
            elif rel != register_rel:
                report.fail(
                    f"{rel}:{n}: assigns '{ident}' in the installation's unnamespaced "
                    f"sequence outside the declared register ({register_rel}) -- a "
                    f"change's own decisions must carry a namespace; citing an "
                    f"identifier the register holds is not assigning one"
                )
            elif ident in retired:
                report.fail(
                    f"{rel}:{n}: assigns retired identifier '{ident}' -- {retired[ident]}"
                )
            elif ident not in assigned:
                report.fail(
                    f"{rel}:{n}: assigns '{ident}', which the declared register's "
                    f"`assigned` list does not hold -- add it there or renumber"
                )

    # (4): a superseded register may not be removed while it holds a unique decision.
    surviving = register_assignments(scan_root / register_rel)
    for old_rel, table in superseded.items():
        entries = {k: v for k, v in table.items() if not k.startswith("_")}
        old_path = scan_root / old_rel
        lost = []
        for ident, row in entries.items():
            now = row.get("now")
            if not now or not row.get("denoted"):
                report.fail(
                    f"{old_rel} {ident}: collision-table row is incomplete "
                    f"(needs both 'denoted' and 'now')"
                )
                continue
            if now != "retired" and now not in surviving:
                lost.append(f"{ident} ('{row['denoted']}') -> {now}")
        if lost:
            verb = "still records" if old_path.is_file() else "recorded"
            report.fail(
                f"{old_rel}: {verb} {len(lost)} decision(s) whose carried identifier "
                f"is absent from the surviving register, so removing it loses them: "
                + "; ".join(sorted(lost))
            )
        # Every identifier the old register actually uses must appear in the table.
        if old_path.is_file():
            for ident in sorted(register_assignments(old_path) - set(entries)):
                report.fail(
                    f"{old_rel}: assigns '{ident}' but the collision table does not "
                    f"record what it denoted -- a citation against it could not resolve"
                )

    # The collision table note must exist once a register has been superseded.
    table_rel = reg.get("collision_table")
    if superseded and table_rel and not (scan_root / table_rel).is_file():
        report.fail(
            f"{table_rel}: a register has been superseded and no collision table "
            f"note records what its identifiers denoted"
        )

    for _subject in paths:
        report.examine(_subject)
    report.coverage(
        covered=[register_rel, *sorted(superseded)],
        excluded=sorted(namespaces) or ["(no per-change namespace declared)"],
        kind="note",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    print(
        f"  register: {register_rel} | assigned={len(assigned)} "
        f"retired={len(retired)} in-file={len(surviving)} "
        f"| superseded registers={len(superseded)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
