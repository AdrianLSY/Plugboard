#!/usr/bin/env python3
"""Gate: the three tiers are wired, in one copy, and the fast one has its budget.

Enforces docs/code/rules/test-tiers.md and docs/code/rules/fast-tier-latency-budget.md,
in the half that is decidable over the tree.

What this gate does NOT do is time anything. The ten seconds are enforced where
they can be -- `make test-fast`, which routes through ci/fast-tier.py and prints
the elapsed time on every run, passing included. What is checkable here is the
WIRING, and the wiring is what silently disappears: a component grows its own
`test` target, a tier target is dropped from one include and not the other, or
the budget wrapper is removed from the top-level target because it was in the way
one afternoon. Each of those leaves a suite that still runs and no longer means
what the rules say it means.

Four cases, all four failing:

  1. A declared tier target absent from a shared include that exists.
  2. The top-level fast-tier target not routed through the declared budget tool.
     A budget nobody passes through is a number in a JSON file.
  3. A declared shared include that does not exist.
  4. A present component whose build file includes none of the declared shared
     includes. It then has its own copy of the tier targets, which is the
     duplication the includes exist to prevent -- and the copy is where a tier
     quietly becomes `go test ./...` with no `-race` and no tag.

## Why the tiers are a rule rather than a habit

The prior attempt's split was not by subsystem but by whether the subject was
synchronous: 27 of 43 files ran `async: false`, and tests of pure functions
required Postgres. Its 947 lines of notifier tests sat in the tier that cannot
observe a commit, so the mechanism they were written for never ran under test at
all. Full evidence in docs/history/reference-audit.md.

## What it does not decide

Whether a given test is in the right tier. No check over source decides that a
test's subject "requires" a database -- and a fast-tier test that reaches for one
fails on its own, in a job with no service to reach, which is the enforcement
that matters and is not this gate's.
"""

from __future__ import annotations

from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "test-tiers"
RULE_NOTE = "docs/code/rules/test-tiers.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["test_tiers"]
    targets = [t for t in cfg["targets"] if not t.startswith("_")]
    includes = [i for i in cfg["includes"] if not i.startswith("_")]
    budget_tool = cfg["budget_tool"]
    components = [
        c
        for c in manifest["code_standards"]["components"]["candidates"]
        if not c.startswith("_")
    ]
    report = Report(GATE_ID, RULE_NOTE)

    present_includes = []
    for rel in includes:
        report.examine(rel)
        path = scan_root / rel
        # (3) a declared include that is not there.
        if not path.is_file():
            report.fail(
                f"{rel}: declared as a shared include for the tier targets and "
                f"absent -- every component it serves has no tiers, or has its own "
                f"copy of them"
            )
            continue
        present_includes.append(rel)
        text = path.read_text(encoding="utf-8")
        # (1) a tier target dropped from one include and not the other.
        for target in targets:
            if f"\n{target}:" not in text:
                report.fail(
                    f"{rel}: declares no `{target}` target -- the tiers are "
                    f"separately invocable in every component, and one missing "
                    f"from one include is a tier that silently does not run there"
                )

    # (2) the budget wrapper on the top-level fast tier.
    top = scan_root / "Makefile"
    report.examine("Makefile")
    if not top.is_file():
        report.fail("Makefile: absent, so there is no top-level tier dispatch at all")
    else:
        text = top.read_text(encoding="utf-8")
        if "test-fast:" not in text:
            report.fail(
                "Makefile: declares no `test-fast` target -- the fast tier is what "
                "runs on save, and it has to be invocable on its own to be that"
            )
        elif budget_tool not in text:
            report.fail(
                f"Makefile: names no path matching ci/vault.json's declared budget "
                f"tool {budget_tool} -- the ceiling is then a number in a JSON file "
                f"that nothing passes through, and suite latency is a correctness "
                f"control here rather than a target"
            )
        elif not (scan_root / budget_tool).is_file():
            report.fail(
                f"{budget_tool}: declared as the fast tier's budget tool and named "
                f"by the Makefile, and absent -- the wrapper resolves to nothing, "
                f"which runs the suite and enforces no ceiling"
            )

    # (4) a component with its own copy of the tier targets.
    for comp in components:
        build = scan_root / comp / "Makefile"
        if not build.is_file():
            continue
        report.examine(comp)
        text = build.read_text(encoding="utf-8")
        if not any(inc in text for inc in includes):
            report.fail(
                f"{comp}/Makefile: includes none of {', '.join(includes)}, so it "
                f"carries its own copy of the tier targets -- which is where a "
                f"tier quietly becomes a bare `test` with no tag and no -race"
            )

    report.coverage(
        covered=[*includes, "Makefile"],
        excluded=["whether a given test is in the right tier (no check decides that)"],
        kind="tier declaration",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  tiers: {', '.join(cfg['tiers'])} | targets: {len(targets)} | shared "
        f"includes present: {len(present_includes)} of {len(includes)} | budget: "
        f"{cfg['fast_budget_seconds']}s via {budget_tool}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
