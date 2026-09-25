#!/usr/bin/env python3
"""Every component reports, at startup, the provenance it was stamped with. Task 3.13.

One checker rather than one test per component, for a reason the tree enforces:
four near-identical test files across four modules is duplication
ci/gates/code_duplication.py would refuse, and Go cannot share a helper across
module boundaries. So the assertion lives once, here, and runs against each.

## What is observed is STARTUP, not a function

Each component is started, and its line is read out of what it prints on the
way up. The Go mains print `buildstamp.Line()` first. The proxy prints
`Plugboard.provenance_line/0` from `Plugboard.Application.start/2`, so it is
started with its application running: `mix run -e ":ok"`, whose expression
prints nothing, so a provenance line in that output came from startup.

The previous command ran the proxy with `--no-start` and called the function
itself. That proved the function and said nothing about startup -- the proxy had
no application callback, starting it printed nothing, and this check passed.

## Two comparisons, because each passes over what the other catches

  * Against the GENERATED STAMP. Each component's stamp source -- the file
    ci/stamp.py writes, where `make stamp` puts it for that component's build --
    is parsed here, and every reported field, `built` included, has to equal it
    exactly, as does the component name. This catches a component reporting
    something other than its stamp: a `built` from its own clock, a value it
    worked out for itself, a line assembled where the stamp never reaches. A
    missing stamp is refused before the component is started.
  * Against GIT, read INDEPENDENTLY. A stamp can be wrong as well: blank, stale,
    another revision's. Compared only with itself, a blank stamp reported
    faithfully passes. So `commit`, `tree` and `version` are also derived from
    git here, and `component` from the directory being checked.

The second is the finding that sank the first attempt at this task. Its tests
built `want` out of the same stamp they compared against:

    want := buildstamp.Build.Commit
    got  := startupReport()
    assert strings.Contains(got, want)        // passes over a BLANK stamp

That passes when every field is empty and when the component name is wrong. A
test that cannot fail is not a test. The stamp comparison here does not repeat
it because it is never the only one: every field it holds that git can answer
is held to git as well.

`built` is the exception. ci/stamp.py's values() takes a build time from its
caller and falls back to the commit date only when given none, so git is not its
authority, and comparing against git would make this check a second place that
decides what a build time is. It is held to the stamp exactly, and to the shape
of an RFC 3339 instant anchored at both ends.

## Four checks

  1. Each component, started, reports a line carrying all four declared fields,
     each exactly once.
  2. Every reported field and the component name equal that component's
     generated stamp, read from its source rather than from the process.
  3. `commit` equals `git rev-parse HEAD`, `tree` matches the working tree's own
     porcelain status, and `version` equals `git describe`, all read here.
  4. Two stamps of ONE revision, one with a file modified, differ in `tree` --
     the dirty marker is about the working tree and not about the revision, which
     is exactly what `git describe --dirty` gets wrong on a repository with no
     tags.

selfcheck() feeds judge() the shapes each comparison exists to refuse, and
reads_what_it_writes() holds the stamp reader to what ci/stamp.py renders, so
neither half can stop working unnoticed over a tree whose stamps happen to be
right.

## What it does not decide

Whether the stamp reaches a RELEASED artifact -- reading provenance out of a
stopped artifact is task 70.7's -- and whether any configuration item collides
with a provenance field, which is task 5.3's against the schema task 5.1
validates. Nor the on-demand report, or reporting `unknown` explicitly for a
build with no provenance: task 5.3's as well. Each is named in the coverage line
rather than quietly skipped.
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
#: An RFC 3339 instant, whole. It was anchored at the start only, so
#: `2026-01-01T00:00:00` followed by anything at all passed -- a prefix test is
#: not a shape test. Matched with fullmatch(), which `$` is not: `$` also
#: matches before a trailing newline.
RFC3339 = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})"
)

#: How each component is started so it reports, and where its generated stamp
#: sits relative to it -- the STAMP path in ci/make/go.mk and ci/make/elixir.mk,
#: which is where ci/stamp.py's output lands. One entry per deployable that has
#: a toolchain; `contract` has none and is declared so in ci/vault.json.
#:
#: The COMMANDS and paths have to live here -- they are per-component facts, not
#: a pattern -- but the SET of components does not: it is declared in
#: ci/vault.json, and reconcile() below holds these keys to it in both
#: directions. A hardcoded set reconciled to nothing is how a fifth stamped
#: component gets built, shipped and never checked, while this script goes on
#: printing "4 components" as if that were the whole roster. A stamp path that
#: drifts from its make file is refused as a missing stamp, not skipped.
COMPONENTS: dict[str, tuple[list[str], str]] = {
    "sidecar": (["go", "run", "./cmd/telephone"], "internal/buildstamp/stamp.go"),
    "terminator": (["go", "run", "./cmd/terminator"], "internal/buildstamp/stamp.go"),
    "conformance": (
        ["go", "run", "./cmd/conformance"],
        "internal/buildstamp/stamp.go",
    ),
    # With the application RUNNING -- no `--no-start` -- and an expression that
    # prints nothing, so the only route to a provenance line in the output is
    # Plugboard.Application.start/2.
    "proxy": (["mix", "run", "-e", ":ok"], "lib/plugboard/build_stamp.ex"),
}


def reconcile() -> list[str]:
    """This file's component set against the vault's, both directions."""

    spec = json.loads((ROOT / "ci" / "vault.json").read_text())["code_standards"][
        "components"
    ]
    declared = {c for c in spec["candidates"] if not c.startswith("_")}
    no_toolchain = {c for c in spec.get("no_toolchain", {}) if not c.startswith("_")}
    expected = declared - no_toolchain
    problems = []
    for missing in sorted(expected - set(COMPONENTS)):
        problems.append(
            f"{missing}: declared a component with a toolchain in ci/vault.json "
            f"and this check does not start it -- it is stamped and unverified"
        )
    for extra in sorted(set(COMPONENTS) - expected):
        problems.append(
            f"{extra}: started by this check and not a component with a toolchain "
            f"in ci/vault.json -- the declaration outlived the component"
        )
    return problems


class ToolAbsent(Exception):
    """A declared tool is not on PATH.

    Carried rather than printed, so the CALLER decides what it means. An absent
    `mix` costs the proxy component and nothing else; an absent `git` costs every
    expectation this check derives, and those are different verdicts.
    """

    def __init__(self, tool: str) -> None:
        super().__init__(tool)
        self.tool = tool


def run_tool(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run cmd, or raise ToolAbsent naming it. Every subprocess here goes through
    this.

    Two of them did not, and each was wrong in its own direction: one let
    FileNotFoundError escape as a traceback, the other caught it and printed
    `[skip]`. Absent is neither. ci/make/elixir.mk says why in its own refusal --
    "a target that skips when its toolchain is absent reports green over an
    unchecked module" -- and a traceback is not a verdict either.
    """
    try:
        return subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, check=False
        )
    except OSError as err:
        raise ToolAbsent(cmd[0]) from err


def git(*args: str) -> str:
    return run_tool(["git", *args], ROOT).stdout.strip()


def reported(component: str) -> tuple[int, str]:
    command, _ = COMPONENTS[component]
    done = run_tool(command, ROOT / component)
    return done.returncode, (done.stdout + done.stderr)


#: A generated stamp, read back in the two shapes ci/stamp.py renders it: Go
#: struct-literal fields and a `const Component`, Elixir map pairs and an
#: `@component` attribute. A literal runs to the first unescaped quote, because
#: ci/stamp.py's escape() is what put the backslashes in.
_LITERAL = r'"((?:[^"\\\n]|\\.)*)"'
_STAMP_SHAPES = {
    ".go": (
        re.compile(rf"^\t(\w+):\s+{_LITERAL},$", re.M),
        re.compile(rf"^const Component = {_LITERAL}$", re.M),
    ),
    ".ex": (
        re.compile(rf'^\s+"(\w+)" => {_LITERAL},?$', re.M),
        re.compile(rf"^\s+@component {_LITERAL}$", re.M),
    ),
}
#: The inverse of ci/stamp.py's escape(), both languages at once: `\#` appears
#: only in the Elixir source, where it stops `#{` interpolating at compile time.
_ESCAPED = re.compile(r"\\(.)", re.S)
_UNESCAPE = {"n": "\n", "r": "\r", "t": "\t"}


def parse_stamp(source: str, suffix: str) -> dict[str, str]:
    """The fields and component name a generated stamp source holds.

    Keyed by ci/stamp.py's FIELDS, plus `component`. Go spells each field in
    CamelCase; that spelling is derived from FIELDS here rather than restated,
    and reads_what_it_writes() fails if the derivation stops matching the
    generator. A field this cannot find is left out rather than defaulted, so
    judge() names it.
    """
    import stamp as stamp_mod

    entry, named = _STAMP_SHAPES[suffix]
    known = {f: f for f in stamp_mod.FIELDS}
    known |= {"".join(p.title() for p in f.split("_")): f for f in stamp_mod.FIELDS}
    found = {known[k]: _unescape(v) for k, v in entry.findall(source) if k in known}
    component = named.search(source)
    if component:
        found["component"] = _unescape(component.group(1))
    return found


def _unescape(literal: str) -> str:
    return _ESCAPED.sub(lambda m: _UNESCAPE.get(m.group(1), m.group(1)), literal)


def read_stamp(path: Path) -> dict[str, str] | None:
    """A component's generated stamp, read from its SOURCE; None where absent.

    From the file ci/stamp.py wrote, never from the running component -- that is
    the value under test, and reading the expectation out of it is the defect
    this whole check is arranged around.
    """
    if not path.is_file():
        return None
    return parse_stamp(path.read_text(encoding="utf-8"), path.suffix)


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
        ["mix", "format", "--check-formatted", "lib/plugboard/build_stamp.ex"],
        "proxy",
        False,
    ),
    "proxy/lib/plugboard/build_stamp.ex (credo)": (
        ["mix", "credo", "--strict", "lib/plugboard/build_stamp.ex"],
        "proxy",
        False,
    ),
    # gofmt -l says nothing when a file is formatted and PRINTS ITS NAME when it
    # is not, exiting 0 either way -- so for it, and only for it, output is the
    # verdict. mix reports through its exit code and prints on every run.
    "sidecar/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"],
        "sidecar",
        True,
    ),
    "terminator/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"],
        "terminator",
        True,
    ),
    "conformance/internal/buildstamp/stamp.go": (
        ["gofmt", "-l", "internal/buildstamp/stamp.go"],
        "conformance",
        True,
    ),
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
            done = run_tool(cmd, root / cwd)
        except ToolAbsent as absent:
            problems.append(
                f"{rel}: {absent.tool} is not on PATH, so this generated source "
                f"was not read by the linter that refuses it. Install it and "
                f"re-run -- skipping here reports green over an unchecked file, "
                f"which is how the generated Elixir reached CI twice"
            )
            continue
        if done.returncode != 0 or (stdout_is_verdict and done.stdout.strip()):
            # The first line that carries WORDS. gofmt prints a bare filename and
            # mix prints a diff whose last line is a pipe character; quoting
            # either is a diagnosis nobody can act on, which is the shape of a
            # check that discards the evidence for its own verdict.
            said = [
                l.strip()
                for l in (done.stdout + done.stderr).splitlines()
                if any(c.isalpha() for c in l)
            ]
            problems.append(
                f"{rel}: the generator emitted source its own component's linter "
                f"refuses -- {said[0][:140] if said else 'exit ' + str(done.returncode)}. "
                f"Fix ci/stamp.py; the file is generated and editing it is undone "
                f"by the next `make stamp`"
            )
        else:
            print(f"  [ok  ] {rel}: formatter-clean")
    return problems


#: Each field of the reported line, and the stamp field it is held to. The line
#: says `built` where ci/stamp.py's FIELDS says `built_at`; that is the one
#: rename between them, stated here rather than guessed at.
REPORTED_AS = {
    "version": "version",
    "commit": "commit",
    "tree": "tree",
    "built": "built_at",
}


def judge(
    component: str,
    line: str,
    stamp: dict[str, str] | None,
    want_commit: str,
    want_tree: str,
    want_version: str,
) -> list[str]:
    """One component's reported line against its generated stamp, and against
    values read from git INDEPENDENTLY.

    A function rather than an inline block so selfcheck() below can feed it a
    missing stamp, a blank one, a stale one and a report that departs from a
    right one, and assert it rejects each. The recorded defect this replaces is
    a test whose expectation was read from the value under test, which passes
    over a blank stamp and over the wrong component name.
    """
    where = f"{component}/{COMPONENTS[component][1]}"
    if stamp is None:
        return [
            f"{component}: no generated stamp at {where}, so there is nothing to "
            f"hold its report to -- run `make stamp`. Refused before starting it, "
            f"because its build would fail on the missing source and name only "
            f"the symptom"
        ]
    problems = []
    for key in ("component", *REPORTED_AS.values()):
        if not stamp.get(key):
            problems.append(
                f"{component}: the generated stamp at {where} carries no `{key}`, "
                f"or a blank one -- a report held to it can only repeat the gap"
            )
    # Blank is reported just above; a name, where there is one, has to agree.
    stamped_as = stamp.get("component") or component
    named = line.split(" ", 1)[0]
    if {named, stamped_as} != {component}:
        problems.append(
            f"{component}: reports itself as {named!r} and its stamp at {where} "
            f"names {stamped_as!r} -- a stamp from another component reports "
            f"that component's provenance under this one's process"
        )
    pairs = FIELD.findall(line)
    fields = dict(pairs)
    for name, key in REPORTED_AS.items():
        count = [k for k, _ in pairs].count(name)
        if count == 0:
            problems.append(f"{component}: reports no `{name}` field")
        elif count > 1:
            # dict() keeps the LAST, so a line carrying a wrong value and then
            # the stamp's would compare equal and pass.
            problems.append(
                f"{component}: reports `{name}` {count} times, and which one is "
                f"the stamp is a question the line should not pose"
            )
        elif stamp.get(key) and fields[name] != stamp[key]:
            problems.append(
                f"{component}: reports {name} {fields[name]!r} and its generated "
                f"stamp at {where} says {stamp[key]!r} -- the startup report is "
                f"the stamp or it is not provenance, however much it resembles it"
            )
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
    # `version` is as independently derivable as the other two, and binding it
    # only to non-emptiness left one of the four declared fields checked by
    # nothing -- which is where the reference's stamped binaries went wrong.
    if want_version and fields.get("version") != want_version:
        problems.append(
            f"{component}: reports version {fields.get('version')!r} and "
            f"`git describe --tags --always --dirty` says {want_version!r}"
        )
    # `built` has no git counterpart to be held to (see the module docstring):
    # the stamp comparison above and this shape are all there is for it.
    if not RFC3339.fullmatch(fields.get("built", "")):
        problems.append(
            f"{component}: `built` is not an RFC 3339 instant: {fields.get('built')!r}"
        )
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
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, CHILD_MARKER: "1", "PATH": "/nonexistent"},
    )
    said = done.stdout + done.stderr
    problems = []
    if "Traceback" in said:
        problems.append(
            "ci/provenance-check.py: raises where a declared toolchain is absent "
            "rather than stating a refusal -- a traceback is not a verdict, and it "
            "stops the components whose toolchains ARE present from being reported"
        )
    if done.returncode == 0:
        problems.append(
            "ci/provenance-check.py: exits zero where every declared toolchain is "
            "absent -- nothing was compared, and a run that checked nothing must "
            "not read as a run that found nothing wrong"
        )
    if not any(m in said for m in ("not on PATH", "is absent")):
        problems.append(
            "ci/provenance-check.py: refuses an absent toolchain without naming it "
            "-- the tool to install is the one fact the reader needs"
        )
    return problems


def selfcheck() -> list[str]:
    """That judge() actually rejects the shapes it exists to reject.

    Nothing pinned the independence repair: reverting judge() to read its
    expectation from the reported line would leave every gate and every fixture
    green, because the only thing exercising it is a tree where the stamp is
    already right. These cases are the counter-examples.

    Most are refused by ONE comparison with every other holding, which is what
    makes each the evidence for that comparison: a stale stamp reported
    faithfully agrees with its stamp and only git refuses it; a `built` from the
    component's own clock agrees with git about everything git knows and only
    the stamp refuses it; a duplicated field and an instant anchored at its
    start only pass both, and are refused by the count and by the anchor.
    """
    stamp = {
        "component": "sidecar",
        "version": "v1",
        "commit": "abc",
        "tree": "clean",
        "built_at": "2026-01-01T00:00:00+00:00",
    }
    good = "sidecar version=v1 commit=abc tree=clean built=2026-01-01T00:00:00+00:00"
    blank = "sidecar version= commit= tree= built="
    clock = good.replace("2026-01-01T00:00:00", "2026-09-25T10:11:12")
    cases: list[tuple[str, str, dict[str, str] | None, bool]] = [
        ("a correct line", good, stamp, False),
        ("a blank report", blank, stamp, True),
        ("a missing stamp", good, None, True),
        (
            "a blank stamp, reported faithfully",
            blank,
            {**{k: "" for k in stamp}, "component": "sidecar"},
            True,
        ),
        (
            "a stale stamp, reported faithfully",
            good.replace("abc", "deadbeef"),
            {**stamp, "commit": "deadbeef"},
            True,
        ),
        ("a `built` from the component's own clock", clock, stamp, True),
        (
            "another component's stamp",
            good,
            {**stamp, "component": "terminator"},
            True,
        ),
        ("a field reported twice", f"{clock} built={stamp['built_at']}", stamp, True),
        (
            "an instant anchored at its start only",
            good.replace("+00:00", "junk"),
            {**stamp, "built_at": "2026-01-01T00:00:00junk"},
            True,
        ),
    ]
    problems = []
    for name, line, stamped, want_rejected in cases:
        rejected = bool(judge("sidecar", line, stamped, "abc", "clean", "v1"))
        if rejected != want_rejected:
            problems.append(
                f"ci/provenance-check.py: judge() {'accepted' if want_rejected else 'rejected'} "
                f"{name} -- a comparison has stopped refusing the shape it exists "
                f"to refuse, which is the defect this check was written to close"
            )
    return problems


def reads_what_it_writes() -> list[str]:
    """parse_stamp() recovers exactly what ci/stamp.py renders, in each language.

    The reader is a second parser of the generator's output, and a parser that
    has drifted from its generator does not fail loudly: it finds no fields, or
    the wrong ones, and judge() then reports a blank stamp that is not blank.
    Rendering a stamp here and reading it back makes that drift this check's
    failure, named as such. The version needs every escape ci/stamp.py emits,
    because a reader missing one agrees with the generator on every plain stamp
    and on nothing else.
    """
    import stamp as stamp_mod

    values = {
        "version": 'v1-"#{x}\\\t\n',
        "commit": "abc",
        "tree": "dirty",
        "built_at": "2026-01-01T00:00:00+00:00",
    }
    problems = []
    for language, suffix in (("go", ".go"), ("elixir", ".ex")):
        try:
            source = stamp_mod.render("probe", language, values)
        except Exception:  # renders() names it; a second report adds nothing
            continue
        got = parse_stamp(source, suffix)
        want = {**values, "component": "probe"}
        if got != want:
            problems.append(
                f"ci/provenance-check.py: reads {got!r} back out of the {language} "
                f"stamp ci/stamp.py renders from {want!r} -- the stamp reader has "
                f"drifted from the generator, so every comparison against a "
                f"stamp is a comparison against the reader's mistake"
            )
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
                f"so a literal brace in one has to be doubled"
            )
            continue
        if not out.strip():
            problems.append(f"ci/stamp.py: rendered empty {language} source")
    return problems


def main(argv: list[str]) -> int:
    problems: list[str] = (
        reconcile()
        + renders()
        + reads_what_it_writes()
        + selfcheck()
        + refuses_an_absent_toolchain()
    )
    # Every expectation below is derived from git, so an absent git is not one
    # component's problem -- there is nothing left to compare against. Refused
    # here, with the tool named, rather than raised from four lines down.
    try:
        want_commit = git("rev-parse", "HEAD")
        want_tree = "dirty" if git("status", "--porcelain") else "clean"
        want_version = git("describe", "--tags", "--always", "--dirty")
    except ToolAbsent as absent:
        print(
            f"[FAIL] provenance: {absent.tool} is not on PATH, so every value "
            f"this check compares against is underivable and nothing was "
            f"verified. Install it and re-run."
        )
        for problem in problems:
            print(f"  - {problem}")
        print("  rule: docs/code/rules/build-provenance-from-one-place.md")
        return 1

    for component in sorted(COMPONENTS):
        # (1) and (2) read the stamp first: without one there is nothing to hold
        # the report to, and starting the component would only fail its build.
        stamp = read_stamp(ROOT / component / COMPONENTS[component][1])
        if stamp is None:
            problems.extend(
                judge(component, "", None, want_commit, want_tree, want_version)
            )
            continue
        try:
            code, out = reported(component)
        except ToolAbsent as absent:
            problems.append(
                f"{component}: {absent.tool} is not on PATH, so nothing ran for it "
                f"and its stamp is unverified. Install it and re-run -- the other "
                f"components are still reported below, which is the half a "
                f"traceback here used to take with it"
            )
            continue
        if code != 0:
            problems.append(
                f"{component}: did not start ({out.strip().splitlines()[-1:] or ['no output']})"
            )
            continue
        line = next((l for l in out.splitlines() if l.startswith(component + " ")), "")
        if not line:
            problems.append(
                f"{component}: reports no provenance line at startup -- the "
                f"reference emitted 75 telemetry events and attached zero handlers, "
                f"and five of seven auditors read that as instrumentation"
            )
            continue
        # (1), (2) and (3): the fields, the stamp, git.
        found = judge(component, line, stamp, want_commit, want_tree, want_version)
        problems.extend(found)
        if not found:
            print(f"  [ok  ] {component}: at startup, equal to its stamp: {line[:72]}")

    # (2a) the generated sources are formatter-clean. Their components' linters
    # read them like any other file, and `make check` never sees them.
    problems.extend(check_formatting(ROOT))

    # (4) one revision, one modified file, two different markers
    import stamp as stamp_mod

    before = stamp_mod.values()
    scratch = ROOT / "ci" / ".provenance-probe"
    scratch.write_text("a modification, removed immediately\n", encoding="utf-8")
    try:
        after = stamp_mod.values()
    finally:
        scratch.unlink(missing_ok=True)
    if before["commit"] != after["commit"]:
        problems.append(
            "the dirty-marker probe changed the revision, so it proves nothing"
        )
    elif before["tree"] == after["tree"] == "dirty":
        print(
            "  [ok  ] dirty marker: the tree was already dirty, so both stamps say dirty "
            "-- the probe is inconclusive here and says so rather than claiming a pass"
        )
    elif before["tree"] == after["tree"]:
        problems.append(
            f"two stamps of one revision, one with a file modified, both report "
            f"tree={before['tree']!r} -- the marker is reading the revision rather "
            f"than the working tree, which is what `git describe --dirty` does on a "
            f"repository with no tags"
        )
    else:
        print(
            f"  [ok  ] dirty marker: {before['tree']} -> {after['tree']} across one modified file"
        )

    print(
        f"\ncoverage: {len(COMPONENTS)} component(s) started and reporting "
        f"provenance | held to each generated stamp: component, version, commit, "
        f"tree, built | derived independently from git: commit, tree, version | "
        f"excluded: contract (no toolchain, declared), a released artifact's stamp "
        f"(task 70.7), a configuration-name collision (task 5.3's, against task "
        f"5.1's schema), the on-demand report and an explicit `unknown` (task 5.3)"
    )
    if problems:
        print(f"[FAIL] provenance: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        print("  rule: docs/code/rules/build-provenance-from-one-place.md")
        return 1
    print("provenance: every component, started, reports the stamp it was built with")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
