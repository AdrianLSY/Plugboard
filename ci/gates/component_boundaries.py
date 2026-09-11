#!/usr/bin/env python3
"""Gate: every component that EXISTS states its boundary, once.

Enforces docs/code-standards -- "A component's boundary is stated once":

  1. A component directory with no boundary note fails, naming the component.
  2. A boundary note for a component that does not exist fails -- its subject
     is gone, or never arrived.
  3. A component README that states its own boundary rather than linking the
     canonical note fails. Two statements of one boundary is the drift this
     whole change exists to remove, and a README is where the second copy
     always appears.

## Why this passes vacuously today, and where that is recorded

The set is keyed on the components that EXIST, and none does: `contract/`,
`proxy/`, `sidecar/`, `terminator/` and `conformance/` are created by
rebuild-plugboard task 1.1. So the keyed set is empty and every case above is
vacuously satisfied.

The reason is DECLARED, in ci/vault.json's gate_policy.declared_vacuity, not
asserted here -- and this module reads it. It used to live in this docstring
alone, which meant a gate reporting zero subjects and exiting zero was doing so
on nothing but its own good manners: no check could read the reason, and nobody
reading a green run would see it. Now an undeclared empty subject set fails, and
a declaration that has outlived its reason fails too.

What this gate buys today is that the moment a component directory appears
without its boundary note, the build fails. The alternative -- writing the check
later, alongside the components -- is how you get five components and no
boundaries.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, on_tracked_tree

GATE_ID = "component-boundaries"
RULE_NOTE = "docs/code/rules/component-boundary-stated-once.md"

OWNS_HEADING = re.compile(r"^#+\s+What it (owns|does not own)", re.M | re.I)


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["components"]
    candidates = [c for c in cfg["candidates"] if not c.startswith("_")]
    bdir = cfg["boundary_dir"]
    report = Report(GATE_ID, RULE_NOTE)

    existing = [c for c in candidates if (scan_root / c).is_dir()]
    notes = {
        p.stem: p
        for p in sorted((scan_root / bdir).glob("*.md"))
        if p.stem != "index"
    } if (scan_root / bdir).is_dir() else {}

    for comp in existing:
        if comp not in notes:
            report.fail(
                f"{comp}/: component directory exists with no boundary note at "
                f"{bdir}/{comp}.md -- placement has to be answerable before a "
                f"contributor picks a file"
            )
    for name in sorted(notes):
        if name not in existing:
            report.fail(
                f"{bdir}/{name}.md: boundary note for a component that does not "
                f"exist ({name}/ is absent)"
            )

    # (3) a README may point at the boundary, never restate it.
    for comp in existing:
        readme = scan_root / comp / "README.md"
        if not readme.is_file():
            continue
        text = readme.read_text(encoding="utf-8")
        if OWNS_HEADING.search(text):
            report.fail(
                f"{comp}/README.md: states the component's boundary itself -- link "
                f"{bdir}/{comp}.md instead; one boundary, one statement"
            )

    # An empty subject set is a DECLARATION, not a docstring claim. Until
    # harden-vault-harness moved it, the reason this gate governs nothing today
    # sat in the module docstring, where no check could read it and no reader
    # of a green run would see it.
    # Scoped to the run against the tracked tree -- the run the aggregating
    # target makes with no tree argument. A fixture tree is deliberately partial
    # and its component set has nothing to do with the repository's, so applying
    # this against one produces a failure that is not a defect. Writing the check
    # without this guard made the fixture emit four violations where it states
    # three, which is how the omission surfaced.
    on_tracked = on_tracked_tree(scan_root)
    vacuity = manifest["gate_policy"].get("declared_vacuity", {}).get(GATE_ID)
    if not on_tracked:
        vacuity = None
    if not existing and on_tracked:
        if not vacuity:
            report.fail(
                f"{GATE_ID}: examined no subjects and no declaration in "
                f"ci/vault.json gate_policy.declared_vacuity records why -- an "
                f"undeclared empty subject set is indistinguishable from a gate "
                f"whose logic stopped matching"
            )
        elif not (vacuity.get("reason") and vacuity.get("ends_with")):
            report.fail(
                f"{GATE_ID}: declared vacuity is incomplete (needs both 'reason' "
                f"and 'ends_with') -- a declaration with no ending condition is a "
                f"permanent exemption wearing a temporary one's clothes"
            )
    elif vacuity:
        report.fail(
            f"{GATE_ID}: {len(existing)} subject(s) exist but ci/vault.json still "
            f"declares this gate vacuous ({vacuity.get('ends_with')}) -- the "
            f"declaration has outlived its reason and must be removed"
        )

        for _subject in existing:
            report.examine(_subject)
    report.coverage(
        covered=existing or ["(no component exists yet)"],
        excluded=[c for c in candidates if c not in existing],
        kind="component",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  components declared: {len(candidates)} | existing: {len(existing)} | "
        f"boundary notes: {len(notes)}"
    )
    if not existing and vacuity:
        print(
            f"  subject set empty by declaration: {vacuity['reason'][:78]}"
            f"\n  ends with: {vacuity['ends_with']}"
        )
    return report.finish(report_only=report_only)


main_guard(run)
