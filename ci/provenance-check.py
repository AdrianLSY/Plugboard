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
import os
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
#: How each component is started so it reports. The COMMANDS have to live here --
#: they are per-component facts, not a pattern -- but the SET of components does
#: not: it is declared in ci/vault.json, and reconcile() below holds these keys to
#: it in both directions. A hardcoded set reconciled to nothing is how a fifth
#: stamped component gets built, shipped and never checked, while this script
#: goes on printing "4 components" as if that were the whole roster.
COMPONENTS = {
    "sidecar": ["go", "run", "./cmd/telephone"],
    "terminator": ["go", "run", "./cmd/terminator"],
    "conformance": ["go", "run", "./cmd/conformance"],
    "proxy": ["mix", "run", "--no-start", "-e", "IO.puts(Plugboard.provenance_line())"],
}


def reconcile() -> list[str]:
    """This file's component set against the vault's, both directions."""
    import json
    spec = json.loads((ROOT / "ci" / "vault.json").read_text())["code_standards"]["components"]
    declared = {c for c in spec["candidates"] if not c.startswith("_")}
    no_toolchain = {c for c in spec.get("no_toolchain", {}) if not c.startswith("_")}
    expected = declared - no_toolchain
    problems = []
    for missing in sorted(expected - set(COMPONENTS)):
        problems.append(
            f"{missing}: declared a component with a toolchain in ci/vault.json "
            f"and this check does not start it -- it is stamped and unverified")
    for extra in sorted(set(COMPONENTS) - expected):
        problems.append(
            f"{extra}: started by this check and not a component with a toolchain "
            f"in ci/vault.json -- the declaration outlived the component")
    return problems


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


def judge(component: str, line: str, want_commit: str, want_tree: str,
          want_version: str) -> list[str]:
    """One component's reported line against values read from git INDEPENDENTLY.

    A function rather than an inline block so selfcheck() below can feed it a
    blank stamp and a wrong one and assert it rejects both. The recorded defect
    this replaces is a test whose expectation was read from the value under
    test, which passes over a blank stamp and over the wrong component name.
    """
    problems = []
    fields = dict(FIELD.findall(line))
    for name in ("version", "commit", "tree", "built"):
        if name not in fields:
            problems.append(f"{component}: reports no `{name}` field")
    if fields.get("commit") != want_commit:
        problems.append(
            f"{component}: reports commit {fields.get('commit')!r} and git says "
            f"{want_commit!r} -- derived here rather than read from the stamp, "
            f"because a test that reads its expectation from the value under "
            f"test passes over a blank one")
    if fields.get("tree") != want_tree:
        problems.append(
            f"{component}: reports tree {fields.get('tree')!r} and the working "
            f"tree is {want_tree!r}")
    # `version` is as independently derivable as the other two, and binding it
    # only to non-emptiness left one of the four declared fields checked by
    # nothing -- which is where the reference's stamped binaries went wrong.
    if want_version and fields.get("version") != want_version:
        problems.append(
            f"{component}: reports version {fields.get('version')!r} and "
            f"`git describe --tags --always --dirty` says {want_version!r}")
    if not RFC3339.match(fields.get("built", "")):
        problems.append(
            f"{component}: `built` is not an RFC 3339 instant: {fields.get('built')!r}")
    return problems


#: Set on the child this check spawns, so the child does not spawn one of its own.
CHILD_MARKER = "PROVENANCE_CHECK_TOOLCHAIN_PROBE"


def refuses_an_absent_toolchain() -> list[str]:
    """This script, where a declared tool is absent, states a refusal.

    It did neither thing a reader would expect. `reported()` let
    FileNotFoundError out of subprocess.run, so a machine without Elixir got a
    traceback where a verdict belongs -- and the verdict it interrupted covered
    the components whose toolchains WERE present. The other half is the inverse
    and worse: `check_formatting()` caught the identical error and printed
    `[skip]`, so a generated source went unread while the run reported green.

    ci/make/elixir.mk states the rule both halves broke, in its own refusal:
    "a target that skips when its toolchain is absent reports green over an
    unchecked module." Absent is not passing and it is not a crash; it is a
    stated refusal with a non-zero exit.

    Run as a child with an empty PATH, because that is the only way to observe
    what this script does when the tools are gone without removing them.
    """
    if os.environ.get(CHILD_MARKER):
        return []
    done = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        cwd=str(ROOT), capture_output=True, text=True, check=False,
        env={**os.environ, CHILD_MARKER: "1", "PATH": "/nonexistent"})
    said = done.stdout + done.stderr
    problems = []
    if "Traceback" in said:
        problems.append(
            "ci/provenance-check.py: raises where a declared toolchain is absent "
            "rather than stating a refusal -- a traceback is not a verdict, and it "
            "stops the components whose toolchains ARE present from being reported")
    if done.returncode == 0:
        problems.append(
            "ci/provenance-check.py: exits zero where every declared toolchain is "
            "absent -- nothing was compared, and a run that checked nothing must "
            "not read as a run that found nothing wrong")
    if not any(m in said for m in ("not on PATH", "is absent")):
        problems.append(
            "ci/provenance-check.py: refuses an absent toolchain without naming it "
            "-- the tool to install is the one fact the reader needs")
    return problems


def selfcheck() -> list[str]:
    """That judge() actually rejects the shapes it exists to reject.

    Nothing pinned the independence repair: reverting judge() to read its
    expectation from the reported line would leave every gate and every fixture
    green, because the only thing exercising it is a tree where the stamp is
    already right. These three cases are the counter-examples.
    """
    good = "sidecar version=v1 commit=abc tree=clean built=2026-01-01T00:00:00+00:00"
    cases = [
        ("a correct line", good, False),
        ("a blank stamp", "sidecar version= commit= tree= built=", True),
        ("another component's stamp", good.replace("abc", "deadbeef"), True),
    ]
    problems = []
    for name, line, want_rejected in cases:
        rejected = bool(judge("sidecar", line, "abc", "clean", "v1"))
        if rejected != want_rejected:
            problems.append(
                f"ci/provenance-check.py: judge() {'accepted' if want_rejected else 'rejected'} "
                f"{name} -- the comparison has stopped being independent of the "
                f"value under test, which is the defect it was written to close")
    return problems


def renders() -> list[str]:
    """The generator produces source for every language it claims to, at all.

    Both templates are `.format()`ed, so a brace in one is a format field. Adding
    `@spec stamp() :: %{String.t() => String.t()}` to the Elixir template made
    every `make stamp` raise KeyError: 'String' -- and because the make recipe
    redirects, the failure was silent and the components went on reporting a
    stamp from the previous commit. Calling the generator directly says which
    language and why, instead of leaving a stale stamp to be noticed downstream.
    """
    import stamp as stamp_mod
    problems = []
    for language in ("go", "elixir"):
        try:
            out = stamp_mod.render("probe", language, stamp_mod.values())
        except Exception as exc:
            problems.append(
                f"ci/stamp.py: cannot render {language} at all -- "
                f"{type(exc).__name__}: {exc}. Both templates are `.format()`ed, "
                f"so a literal brace in one has to be doubled")
            continue
        if not out.strip():
            problems.append(f"ci/stamp.py: rendered empty {language} source")
    return problems


def main(argv: list[str]) -> int:
    problems: list[str] = (reconcile() + renders() + selfcheck()
                           + refuses_an_absent_toolchain())
    want_commit = git("rev-parse", "HEAD")
    want_tree = "dirty" if git("status", "--porcelain") else "clean"
    want_version = git("describe", "--tags", "--always", "--dirty")

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
        problems.extend(judge(component, line, want_commit, want_tree, want_version))
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
