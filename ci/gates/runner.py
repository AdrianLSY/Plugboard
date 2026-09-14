#!/usr/bin/env python3
"""Gate: every blocking gate runs without a person's initiative.

Enforces docs/code-standards -- "Every blocking gate runs without a person's
initiative".

Before the configuration this gate checks existed, twenty-five gates were
declared blocking in ci/vault.json and nothing blocked. They ran when somebody
chose to type a command, which is the condition every one of them was written to
replace, and `CLAUDE.md` described `make check` as "the one command CI runs"
while no runner configuration was tracked at all. That is not hypothetical: a
rename sat half-staged in the index for hours with one gate crashing on a path
`git ls-files` reported as tracked, and it survived a completion report and a
session boundary.

Four cases, all four failing:

  1. No configuration at the declared path.
  2. A configuration carrying a path filter, a branch filter, or a clause letting
     a non-zero exit pass -- each named, because each defeats refusal in a
     different way.
  3. A configuration that does not invoke the declared aggregating target, or
     does not carry both declared triggers.
  4. An aggregating target that swallows a failure: a `-` prefix or a `|| true`
     on the recipe makes every gate advisory again in one character.

## Keys, not substrings

The first version of this check grepped for the forbidden clause names and
failed on the workflow file that DOCUMENTS them in a comment -- the file it was
written to approve. So comment lines are stripped and the remainder is matched
as `key:` at the start of a line. A structural read of a small, known-shape file
rather than a YAML dependency, because ci/ is standard library only.

## What this gate does not decide

Whether the hosting service refuses a merge. That is a branch-protection setting
held server-side: no tracked artifact states it and nothing here can read it. The
requirement puts it out of scope explicitly rather than leaving a scenario
nothing could distinguish a pass from a fail on.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "runner"
RULE_NOTE = "docs/method/rules/the-gates-actually-run.md"


def uncommented(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def triggers(body: str) -> set[str]:
    """Every event name under `on:`, in all three spellings GitHub accepts.

    A mapping:            on:\n  push:\n  pull_request:
    A bare scalar:        on: pull_request_target
    An inline sequence:   on: [push, pull_request]

    All three are valid and this gate met the second one the day a fourth
    workflow was declared -- it recognised only the mapping, so a workflow that
    DID carry its declared trigger was reported as missing it. A gate that
    refuses a correct spelling is one that gets argued with and then switched
    off, which is the failure this whole harness is arranged against.

    Parsed by regex rather than by a YAML library because ci/gates is standard
    library only: a gate with a dependency can stop running without failing.
    """
    m = re.search(r"^on:\s*$(.*?)(?=^\S)", body, re.M | re.S)
    if m:
        return set(re.findall(r"^\s+([a-z_]+)\s*:", m.group(1), re.M))
    m = re.search(r"^on:\s*(.+?)\s*$", body, re.M)
    if not m:
        return set()
    rest = m.group(1)
    if rest.startswith("["):
        return {t.strip().strip("'\"") for t in rest.strip("[]").split(",") if t.strip()}
    return {rest.strip()}


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["runner"]
    target = cfg["aggregating_target"]
    workflows = {k: v for k, v in cfg["workflows"].items() if not k.startswith("_")}
    forbidden = {k: v for k, v in cfg["forbidden_clauses"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)

    # Every declared workflow, not just the aggregating one. A second blocking
    # workflow outside this gate's scope is the condition the rule refuses: the
    # properties its own header claims would be prose, checked by nothing.
    for rel, spec in sorted(workflows.items()):
        report.examine(rel)
        path = scan_root / rel
        if not path.is_file():
            report.fail(
                f"{rel}: no runner configuration at a path ci/vault.json declares -- "
                f"until one exists, what it was declared to run runs only when "
                f"somebody chooses to"
            )
            continue

        body = uncommented(path.read_text(encoding="utf-8"))

        # (2) a clause that defeats refusal.
        for key, why in sorted(forbidden.items()):
            if re.search(rf"^\s*{re.escape(key)}\s*:", body, re.M):
                report.fail(f"{rel}: carries `{key}:` -- {why}")

        # (3) the triggers this workflow declares for itself, and -- for the one
        # that runs the gates -- the aggregating target.
        declared_on = triggers(body)
        for want in spec["required_triggers"]:
            if want not in declared_on:
                report.fail(
                    f"{rel}: does not trigger on `{want}` -- a runner that misses one "
                    f"of the events it declares leaves that event unchecked"
                )
        if spec.get("invokes_aggregating_target") and target not in body:
            report.fail(
                f"{rel}: does not invoke the declared aggregating target "
                f"('{target}') -- a runner that runs something else is not this "
                f"declaration's runner"
            )

    # (4) the aggregating target must not swallow a failure.
    makefile = scan_root / "Makefile"
    if not makefile.is_file():
        report.fail("Makefile: absent, so the declared aggregating target does not exist")
    else:
        name = target.split()[-1]
        report.examine(f"Makefile:{name}")
        m = re.search(rf"^{re.escape(name)}:.*?\n((?:\t.*\n)+)", makefile.read_text(encoding="utf-8"), re.M)
        if not m:
            report.fail(f"Makefile: declares no `{name}` target")
        else:
            for line in m.group(1).splitlines():
                recipe = line.lstrip("\t")
                if recipe.lstrip().startswith("-"):
                    report.fail(
                        f"Makefile `{name}`: a recipe line begins with `-`, so make "
                        f"ignores its exit status -- every gate becomes advisory in "
                        f"one character"
                    )
                if "|| true" in recipe or "|| :" in recipe:
                    report.fail(
                        f"Makefile `{name}`: a recipe line swallows failure with "
                        f"`{recipe.strip()[:40]}` -- the target cannot then report a "
                        f"blocking gate"
                    )

    report.coverage(
        covered=[*sorted(workflows), f"Makefile:{target.split()[-1]}"],
        excluded=["whether the hosting service refuses a merge (server-side, unreadable here)"],
        kind="runner declaration",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        "  runners: "
        + " | ".join(
            f"{rel} ({', '.join(spec['required_triggers'])})"
            for rel, spec in sorted(workflows.items())
        )
        + f" | target: {target} | forbidden clauses checked: {len(forbidden)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
