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


def trigger_block(body: str) -> str:
    """The `on:` mapping, up to the next top-level key."""
    m = re.search(r"^on:\s*$(.*?)(?=^\S)", body, re.M | re.S)
    return m.group(1) if m else ""


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["runner"]
    rel = cfg["path"]
    target = cfg["aggregating_target"]
    forbidden = {k: v for k, v in cfg["forbidden_clauses"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)
    report.examine(rel)

    path = scan_root / rel
    if not path.is_file():
        report.fail(
            f"{rel}: no runner configuration at the path ci/vault.json declares -- "
            f"until one exists, every gate declared blocking blocks nothing and runs "
            f"only when somebody chooses to"
        )
    else:
        body = uncommented(path.read_text(encoding="utf-8"))

        # (2) a clause that defeats refusal.
        for key, why in sorted(forbidden.items()):
            if re.search(rf"^\s*{re.escape(key)}\s*:", body, re.M):
                report.fail(f"{rel}: carries `{key}:` -- {why}")

        # (3) both declared triggers, and the declared target.
        triggers = trigger_block(body)
        for want in cfg["required_triggers"]:
            if not re.search(rf"^\s+{re.escape(want)}\s*:", triggers, re.M):
                report.fail(
                    f"{rel}: does not trigger on `{want}` -- a runner that misses one "
                    f"of the declared events leaves that event unchecked"
                )
        if target not in body:
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
        covered=[rel, f"Makefile:{target.split()[-1]}"],
        excluded=["whether the hosting service refuses a merge (server-side, unreadable here)"],
        kind="runner declaration",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  runner: {rel} | target: {target} | triggers: "
          f"{', '.join(cfg['required_triggers'])} | forbidden clauses checked: {len(forbidden)}")
    return report.finish(report_only=report_only)


main_guard(run)
