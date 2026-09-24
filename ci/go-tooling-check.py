#!/usr/bin/env python3
"""Every Go checking command is demonstrated to refuse its own violating input.

Serves rebuild-plugboard tasks 3.2 and 3.3 on the Go side, and commits the
violations task 2.3 verified by hand. The Elixir half is ci/proxy-tooling-check.py.

A gate's subject is a property of the tree and it starts no process. This starts
several, against a copy, so it pairs to a SCRIPT rather than to ci/gates/<name>.py
-- declared in ci/vault.json gate_policy.script_paired_inputs, and run by the lint
job in .github/workflows/test.yml.

Four assertions, and the third is the one the Elixir checker's review found
missing from it:

  1. THE ROSTER. Every checking command in ci/make/go.mk's recipes has a violating
     input naming it. A command nobody planted a violation for is a command nobody
     has seen refuse anything.
  2. THE BEHAVIOUR. Each input is refused by exactly the tools it declares, and the
     declared case substring appears in that tool's own output.
  3. THE BINDING. A tree's declared `tool` is in its declared `fails`. Without this
     the roster is satisfied by a LABEL: swapping two trees' tool names passes
     while neither tool is bound to the input that names it.
  4. REACHABILITY. `golangci-lint` refusing an input is not enough -- the recipe
     in ci/make/go.mk has to refuse it too, or the check is reachable by hand and
     not by `make lint`.

## What this does not decide

Whether the linter set is the right one, or whether a threshold is well chosen.
It decides that each command in the recipe has been seen to refuse something, and
that the something is what the declaration says it is.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "ci" / "broken-inputs" / "go-tooling"
GO_MK = ROOT / "ci" / "make" / "go.mk"

#: The checking commands, and how to run one against a module directory. A
#: rewriter is not a check: `go fmt` edits the file and always succeeds, which is
#: why gofmt is reached through golangci-lint's formatter instead.
COMMANDS = {
    "golangci-lint": lambda d: [
        "golangci-lint",
        "run",
        "--config",
        str(ROOT / ".golangci.yml"),
        "./...",
    ],
    "go-test-race": lambda d: ["go", "test", "-race", "./..."],
}


def recipe_commands() -> set[str]:
    """The checking commands ci/make/go.mk actually invokes."""
    body = GO_MK.read_text(encoding="utf-8")
    found = set()
    if re.search(r"^\t\$\(GOLANGCI\) run\b", body, re.M):
        found.add("golangci-lint")
    if re.search(r"^\t\$\(GO\) test -race\b", body, re.M):
        found.add("go-test-race")
    return found


def run_in(directory: Path, argv: list[str]) -> tuple[int, str]:
    done = subprocess.run(argv, cwd=str(directory), capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def main(argv: list[str]) -> int:
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    decl = json.loads((INPUTS / "expect.json").read_text(encoding="utf-8"))
    trees = {k: v for k, v in decl["trees"].items() if not k.startswith("_")}
    problems: list[str] = []

    # (1) the roster
    declared_tools = {spec["tool"] for spec in trees.values()}
    for cmd in sorted(recipe_commands() - declared_tools):
        problems.append(
            f"`{cmd}` is in ci/make/go.mk's recipes and no violating input under "
            f"ci/broken-inputs/go-tooling/ names it -- a command nobody planted a "
            f"violation for is one nobody has seen refuse anything"
        )
    for name, spec in sorted(trees.items()):
        # (3) the binding
        if spec["tool"] not in spec["fails"]:
            problems.append(
                f"'{name}' names tool '{spec['tool']}' and does not list it in "
                f"`fails` ({', '.join(spec['fails']) or 'none'}) -- the input is "
                f"then bound to no tool at all, and the roster above is satisfied "
                f"by the label alone"
            )
        if not spec["fails"]:
            problems.append(
                f"'{name}' declares an empty `fails`, which no tool can satisfy"
            )

    for name, spec in sorted(trees.items()):
        if only and only not in name:
            continue
        source = INPUTS / name
        if not source.is_dir():
            problems.append(
                f"'{name}' is declared and ci/broken-inputs/go-tooling/{name} is absent"
            )
            continue
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / name
            shutil.copytree(source, work)
            failing, outputs = [], {}
            for cmd, argv_of in sorted(COMMANDS.items()):
                code, out = run_in(work, argv_of(work))
                outputs[cmd] = out
                if code != 0:
                    failing.append(cmd)
            # (2) the behaviour
            if sorted(failing) != sorted(spec["fails"]):
                problems.append(
                    f"'{name}': the tools that fail are "
                    f"{', '.join(failing) or 'none'}, and expect.json declares "
                    f"{', '.join(spec['fails'])}"
                )
            elif spec["case"] not in outputs.get(spec["tool"], ""):
                problems.append(
                    f"'{name}': {spec['tool']} failed and its output does not carry "
                    f"the declared case {spec['case']!r}"
                )
            else:
                print(
                    f"  [ok  ] {name}: refused by {', '.join(failing)} ({spec['case']})"
                )

            # (4) reachability through the recipe, not only by hand
            if "golangci-lint" in spec["fails"]:
                code, _ = run_in(
                    work,
                    [
                        "golangci-lint",
                        "run",
                        "--config",
                        str(ROOT / ".golangci.yml"),
                        "./...",
                    ],
                )
                if code == 0:
                    problems.append(
                        f"'{name}': the configuration ci/make/go.mk passes does not "
                        f"refuse it, so `make lint` would pass over it"
                    )

    covered = sorted(declared_tools)
    print(
        f"\ncoverage: {len(trees)} violating module(s) from ci/broken-inputs/go-tooling "
        f"| covered: {', '.join(covered)} | excluded: "
        f"{'a rewriter (`go fmt` edits and always succeeds, so it checks nothing)'}"
    )
    if problems:
        print(f"[FAIL] go tooling: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        print("  rule: docs/code/rules/language-conventions-keyed-on-source.md")
        return 1
    print("go tooling: every checking command is demonstrated to refuse")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
