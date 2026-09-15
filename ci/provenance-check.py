#!/usr/bin/env python3
"""Every component reports the provenance it was stamped with. Task 3.13.

One checker rather than one test per component, for a reason the tree enforces:
four near-identical test files across four modules is duplication
ci/gates/code_duplication.py would refuse, and Go cannot share a helper across
module boundaries. So the assertion lives once, here, and runs against each.

## The assertion is derived INDEPENDENTLY of the value under test

This is the finding that sank the first attempt at this task. Its tests built
`want` out of the same stamp they compared against:

    want := buildstamp.Build.Commit
    got  := startupReport()
    assert strings.Contains(got, want)        // passes over a BLANK stamp

That passes when every field is empty and when the component name is wrong. A
test that cannot fail is not a test. Here `commit` and `tree` are derived from
git directly, `component` from the directory being checked, and only `built_at`
is checked structurally -- there is nothing to compare a build time against.

## Three checks

  1. Each component reports a line carrying all four declared fields.
  2. `commit` equals `git rev-parse HEAD` and `tree` matches the working tree's
     own porcelain status, both read here rather than taken from the stamp.
  3. Two stamps of ONE revision, one with a file modified, differ in `tree` --
     the dirty marker is about the working tree and not about the revision, which
     is exactly what `git describe --dirty` gets wrong on a repository with no
     tags.

## What it does not decide

Whether the stamp reaches a RELEASED artifact -- reading provenance out of a
stopped artifact is task 70.7's -- and whether any configuration item collides
with a provenance field, which needs the configuration schema task 5.2 builds.
Both are named in 'unfinished' rather than quietly skipped.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ci"))

FIELD = re.compile(r"(\w+)=(\S+)")
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

#: How to make each component report. One entry per deployable that has a
#: toolchain; `contract` has none and is declared so in ci/vault.json.
COMPONENTS = {
    "sidecar": ["go", "run", "./cmd/telephone"],
    "terminator": ["go", "run", "./cmd/terminator"],
    "conformance": ["go", "run", "./cmd/conformance"],
    "proxy": ["mix", "run", "--no-start", "-e", "IO.puts(Plugboard.provenance_line())"],
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True,
                          text=True, check=False).stdout.strip()


def reported(component: str) -> tuple[str, str]:
    done = subprocess.run(COMPONENTS[component], cwd=str(ROOT / component),
                          capture_output=True, text=True, check=False)
    return done.returncode, (done.stdout + done.stderr)


#: The generated sources, and every linter each component's own `lint` target
#: runs over them -- not only the formatter. The Go side is piped through gofmt by ci/stamp.py; the Elixir side cannot
#: be (mix needs a project context and may be absent), so it is checked here.
#:
#: This exists because a trailing comma in the generated Elixir map failed
#: `mix format --check-formatted` in CI, on a file no human wrote and that
#: `make check` never sees -- it is gitignored, and the formatter runs only in
#: `make -C proxy lint`. A generated file is still a file the linters read.
#:
#: Then a reviewer found the SECOND one the same way: `mix credo --strict`
#: refused the generated module for functions with no @spec, which the formatter
#: had nothing to say about. One linter was never the subject; every linter the
#: component's lint target runs is.
FORMATTED = {
    "proxy/lib/plugboard/build_stamp.ex": (
        ["mix", "format", "--check-formatted", "lib/plugboard/build_stamp.ex"], "proxy", False),
    "proxy/lib/plugboard/build_stamp.ex (credo)": (
        ["mix", "credo", "--strict", "lib/plugboard/build_stamp.ex"], "proxy", False),
    # gofmt -l says nothing when a file is formatted and PRINTS ITS NAME when it
    # is not, exiting 0 either way -- so for it, and only for it, output is the
    # verdict. mix reports through its exit code and prints on every run.
    "sidecar/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"], "sidecar", True),
    "terminator/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"], "terminator", True),
    "conformance/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"], "conformance", True),
}


def check_formatting(root: Path) -> list[str]:
    """Every generated stamp, held to the formatter its component's lint runs."""
    problems = []
    for rel, (cmd, cwd, stdout_is_verdict) in sorted(FORMATTED.items()):
        target = root / rel.split(" (")[0]
        if not target.is_file():
            problems.append(f"{rel}: absent -- run `make stamp`")
            continue
        try:
            done = subprocess.run(cmd, cwd=root / cwd, capture_output=True, text=True)
        except FileNotFoundError:
            print(f"  [skip] {rel}: {cmd[0]} is not on PATH")
            continue
        if done.returncode != 0 or (stdout_is_verdict and done.stdout.strip()):
            # The first line that carries WORDS. gofmt prints a bare filename and
            # mix prints a diff whose last line is a pipe character; quoting
            # either is a diagnosis nobody can act on, which is the shape of a
            # check that discards the evidence for its own verdict.
            said = [l.strip() for l in (done.stdout + done.stderr).splitlines()
                    if any(c.isalpha() for c in l)]
            problems.append(
                f"{rel}: the generator emitted source its own component's linter "
                f"refuses -- {said[0][:140] if said else 'exit ' + str(done.returncode)}. "
                f"Fix ci/stamp.py; the file is generated and editing it is undone "
                f"by the next `make stamp`")
        else:
            print(f"  [ok  ] {rel}: formatter-clean")
    return problems


def main(argv: list[str]) -> int:
    problems: list[str] = []
    want_commit = git("rev-parse", "HEAD")
    want_tree = "dirty" if git("status", "--porcelain") else "clean"

    for component in sorted(COMPONENTS):
        code, out = reported(component)
        if code != 0:
            problems.append(f"{component}: did not start ({out.strip().splitlines()[-1:] or ['no output']})")
            continue
        line = next((l for l in out.splitlines() if l.startswith(component + " ")), "")
        if not line:
            problems.append(
                f"{component}: reports no provenance line at startup -- the "
                f"reference emitted 75 telemetry events and attached zero handlers, "
                f"and five of seven auditors read that as instrumentation"
            )
            continue
        fields = dict(FIELD.findall(line))
        for name in ("version", "commit", "tree", "built"):
            if name not in fields:
                problems.append(f"{component}: reports no `{name}` field")
        if fields.get("commit") != want_commit:
            problems.append(
                f"{component}: reports commit {fields.get('commit')!r} and git says "
                f"{want_commit!r} -- derived here rather than read from the stamp, "
                f"because a test that reads its expectation from the value under "
                f"test passes over a blank one"
            )
        if fields.get("tree") != want_tree:
            problems.append(
                f"{component}: reports tree {fields.get('tree')!r} and the working "
                f"tree is {want_tree!r}"
            )
        if not RFC3339.match(fields.get("built", "")):
            problems.append(f"{component}: `built` is not an RFC 3339 instant: {fields.get('built')!r}")
        if not problems or problems[-1].split(":")[0] != component:
            print(f"  [ok  ] {component}: {line[:96]}")

    # (2a) the generated sources are formatter-clean. Their components' linters
    # read them like any other file, and `make check` never sees them.
    problems.extend(check_formatting(ROOT))

    # (3) one revision, one modified file, two different markers
    import stamp as stamp_mod
    before = stamp_mod.values()
    scratch = ROOT / "ci" / ".provenance-probe"
    scratch.write_text("a modification, removed immediately\n", encoding="utf-8")
    try:
        after = stamp_mod.values()
    finally:
        scratch.unlink(missing_ok=True)
    if before["commit"] != after["commit"]:
        problems.append("the dirty-marker probe changed the revision, so it proves nothing")
    elif before["tree"] == after["tree"] == "dirty":
        print("  [ok  ] dirty marker: the tree was already dirty, so both stamps say dirty "
              "-- the probe is inconclusive here and says so rather than claiming a pass")
    elif before["tree"] == after["tree"]:
        problems.append(
            f"two stamps of one revision, one with a file modified, both report "
            f"tree={before['tree']!r} -- the marker is reading the revision rather "
            f"than the working tree, which is what `git describe --dirty` does on a "
            f"repository with no tags"
        )
    else:
        print(f"  [ok  ] dirty marker: {before['tree']} -> {after['tree']} across one modified file")

    print(f"\ncoverage: {len(COMPONENTS)} component(s) reporting provenance | derived "
          f"independently: commit, tree | excluded: contract (no toolchain, declared), "
          f"a released artifact's stamp (task 70.7), a configuration-name collision "
          f"(needs task 5.2's schema)")
    if problems:
        print(f"[FAIL] provenance: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        print("  rule: docs/code/rules/build-provenance-from-one-place.md")
        return 1
    print("provenance: every component reports the stamp it was built with")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
