#!/usr/bin/env python3
"""Gate: every component is stamped from one place, and reports what it was stamped with.

Enforces rebuild-plugboard task 3.13. The build stamp -- version, commit,
dirty-tree marker, build time -- is computed in ONE recipe (ci/make/go.mk's
`stamp`, which ci/make/elixir.mk delegates to), emitted into one generated source
per component, and reported by that component at startup.

## What this gate DECIDES

  1. A component that computes its own provenance. Asking version control what
     this build is, from a component's own build file or source, is a second copy
     of the discovery, and two copies is how one component comes to report a
     dirty tree while another never does -- a drift neither side can see from
     where it stands. Matched as a pattern over git's option syntax, not as a
     substring: `git -C '$(STAMP_SRC)' rev-parse HEAD` is the spelling the one
     place itself uses, so a substring test would have caught only the copy
     nobody here would write and missed every paste of the real thing.
  2. A build fragment other than the one place computing it. The same defect one
     level up, and the likelier one: the copy arrives when a second language
     needs a stamp and delegating looks like a detour.
  3. A component with an entry point that does not report the stamp -- EVERY
     `package main` under its cmd/, not just the one its Makefile names as CMD.
     A stamp compiled into a binary that never says it is the prior art's shape
     exactly: 75 telemetry events emitted, zero handlers attached, and five of
     seven auditors read that as instrumentation.

     Decided over the source with comments and string literals REMOVED, and by
     looking for a CALL. Every entry point in this repository carries a header
     paragraph explaining where the reporter comes from, so a check asking
     whether the file contains its name is answered by the prose about the rule
     rather than by the code the rule governs. Measured: silencing all four Go
     entry points while leaving those paragraphs in place -- and the Elixir one,
     whose `@spec` and `def` still name the reporter twice -- left the gate
     reporting `[ok] provenance: no violations` over a tree where nothing said
     what it was built from at all.
  4. A component with no test CALLING what reports it. A startup line nothing
     asserts is a line that drifts from the stamp at the first refactor, and a
     test file that merely discusses the reporter in a comment asserts nothing
     about it. Same stripping, same call test, for the same reason.
  5. A shared fragment that exists and defines no `stamp` target -- and,
     separately, the one place being ABSENT while components are present. Only
     the second of those is conditioned on there being components: a fragment
     under ci/make/ exists in order to serve them, so one carrying no `stamp`
     target is defective wherever it sits, and the tree3 fixture demonstrates
     exactly that with no component present at all. This clause used to read
     "while components are present" for both halves, which described neither the
     code nor the fixture that pins it.
  6. A stamping mechanism that cannot tell a modified tree from a clean one.
     This is one of two cases decided by RUNNING something: the mechanism is
     invoked twice over a throwaway repository, once clean and once with a single
     file modified, and the two dirty-tree markers must differ while the commit
     stays the same. No reading of a recipe decides that, and a marker that never
     moves is indistinguishable from an honest one in every artifact it appears
     in.
  9. A field the one place emits blank, or in a shape it does not promise. The
     other executed case, off the same throwaway revision: all five fields
     present, the commit forty hex digits or the word `unknown`, the tree marker
     one of three words, the build time an RFC-3339 instant, and the component
     the name STAMP_COMPONENT was given -- so that the parameter being honoured
     at all is observable rather than assumed.

     It is decided HERE, once, and not in each component's test, because the
     shape of a field belongs to the recipe that emits it rather than to any
     binary it lands in. Four modules repeating these five patterns would be four
     copies of one thing (docs/code/rules/duplication-threshold.md), and each
     would be a snapshot of what the recipe emitted on the day it was pasted
     rather than an assertion about the recipe. The sidecar's test keeps one
     compiled-in copy on purpose, as the other end of the claim: that the values
     which actually reached a binary still look like this.
  7. (repository-scoped) A TRACKED generated stamp. Committing one makes the tree
     dirty the moment it is regenerated, so the marker it carries stops being
     true about the tree it describes.
  8. A target that consumes the stamp and does not depend on it. A `stamp` target
     that exists is not a `stamp` target that runs: drop it from the tier, lint
     and build prerequisites and every recipe still works, still compiles and
     still passes -- against whatever generated stamp an earlier build left on
     disk. The never-stamped case the compiler catches; the STALE-stamp case is
     caught by nothing else, and it is the one that reaches a shipped artifact
     and lies in it.

## What it does NOT decide

**Whether a configuration item shares a name with a provenance field.** Task 3.13
asks for that check and it is not here, because no component has a configuration
schema yet -- tasks 5.1 and 5.2 build them. A check written against a schema that
does not exist would pass over every component in the repository and report the
same green as one that had examined four. When the schemas land, the collision
check belongs beside them (task 5.3 names the refusal), and the field vocabulary
it must refuse is the one this gate holds: FIELDS below.

**Whether the reported values are TRUE.** That the commit is the commit, that the
build time is the build time: nothing in the tree can decide either. What is
decided here is that they come from one place, reach the binary, and are reported
and asserted.

**Whether a test's assertions are any good.** Case 4 decides that a test CALLS the
reporter, not that it checks anything about what comes back. The assertion with
teeth is the test itself, and a gate that claimed more here would be read as a
guarantee it cannot give.

That exclusion is real, and it is why the tests themselves have to carry the
weight. Each of the five stamped binaries binds its stamp against something
INDEPENDENT of the stamp -- its own component name as a literal, and a shape per
field -- rather than only comparing the reporter's output to the map the reporter
reads. A test built that second way cannot fail on a value: `want` and `got` are
rendered from the same map, every value cancels, and what survives asserts only
the field names and their order. Two of them were written that way and passed
over a wholly blank stamp and over `component=WRONG-NOT-TERMINATOR`.

The reasoning that produced them is worth naming, because it is plausible: one
recipe stamps all four components, so binding the value shapes once, in the
sidecar's test, looks like avoiding duplication. One recipe does stamp all four;
one ARTIFACT does not. Each component is a separate Go module compiling its own
generated build_stamp.go, so the sidecar's test binds the sidecar's compiled-in
values and reaches none of the others. A shared recipe is not a shared artifact.

**Provenance read from a stopped artifact.** That is task 70.7's obligation, and
this gate examines a running component's report and a build recipe only.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from _common import Report, load_manifest, main_guard, on_tracked_tree, repo_root

GATE_ID = "provenance"
RULE_NOTE = "docs/code/rules/build-provenance-from-one-place.md"

#: The one place, and the fragments that must reach it rather than copy it.
ONE_PLACE = "ci/make/go.mk"
FRAGMENTS = ("ci/make/go.mk", "ci/make/elixir.mk")
STAMP_TARGET = "stamp"

#: The provenance vocabulary. Stated here rather than in ci/vault.json for the
#: reason ci/gates/expected_outcomes.py states its registry path here: it is the
#: gate's own subject, five names long, and a declaration nothing else reads is
#: a second place to keep in step. It is the set a configuration item may not
#: collide with once there are configuration schemas to check.
FIELDS = ("component", "version", "commit", "tree", "built_at")

#: What reports the stamp, per language, and what the generated source is called.
REPORTER = {"go": "startupReport", "elixir": "report_provenance"}
STAMP_FILE = {"go": "build_stamp.go", "elixir": "build_stamp.ex"}


def code_only(text: str, lang: str) -> str:
    """The source with its comments and string literals blanked out.

    Case 3 and case 4 ask whether something CALLS the reporter. Asking whether
    the file CONTAINS its name answers a different question, and in this
    repository it answered it wrongly on every file: each entry point carries a
    header paragraph explaining where `startupReport` comes from, so all four Go
    binaries could be made to print a bare banner and the gate still reported
    `[ok] provenance: no violations` over a tree where nothing said what it was
    built from. Measured, on this tree, before this function existed.

    A rule whose check is satisfied by the prose explaining the rule is the exact
    shape docs/method/rules/ exists to refuse, so the text a pattern runs over is
    the text the compiler sees. Literals go too: a banner string that happens to
    name the reporter is documentation with quotes around it.

    Blanked rather than deleted -- each stripped run is replaced by spaces and
    newlines are kept -- so offsets and line numbers still line up with the file.
    """
    out = []
    i, n = 0, len(text)
    line_c, block_c, quote = False, False, ""
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if line_c:
            if ch == "\n":
                line_c = False
                out.append(ch)
            else:
                out.append(" ")
            i += 1
        elif block_c:
            if lang == "go" and ch == "*" and nxt == "/":
                block_c = False
                out.append("  ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
        elif quote:
            # A heredoc closes on its own three-quote run; a plain string closes
            # on its delimiter, and a backslash escapes the next character.
            if ch == "\\" and quote != "`" and len(quote) == 1:
                out.append("  ")
                i += 2
                continue
            if text.startswith(quote, i):
                out.append(" " * len(quote))
                i += len(quote)
                quote = ""
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
        elif lang == "go" and ch == "/" and nxt == "/":
            line_c = True
            out.append("  ")
            i += 2
        elif lang == "go" and ch == "/" and nxt == "*":
            block_c = True
            out.append("  ")
            i += 2
        elif lang == "elixir" and ch == "#" and nxt != "{":
            line_c = True
            out.append(" ")
            i += 1
        elif lang == "elixir" and text.startswith('"""', i):
            quote = '"""'
            out.append("   ")
            i += 3
        elif ch in ('"', "`", "'") and not (lang == "elixir" and ch == "`"):
            quote = ch
            out.append(" ")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def reporter_call(lang: str) -> re.Pattern[str]:
    """The reporter being INVOKED, as against defined or specified.

    Go: a call is the name followed by `(`. Elixir: the same, minus the two
    places the name legitimately appears without being a call -- its own `def`
    and its `@spec`. Without that exclusion the proxy's `application.ex` would
    satisfy this case by declaring the function and never calling it, which is a
    stamp compiled in and never reported wearing a definition as its alibi.
    """
    name = re.escape(REPORTER[lang])
    if lang == "elixir":
        return re.compile(rf"(?<!def )(?<!defp )(?<!@spec ){name}\s*\(")
    return re.compile(rf"\b{name}\s*\(")


def calls_reporter(text: str, lang: str) -> bool:
    return bool(reporter_call(lang).search(code_only(text, lang)))

#: Provenance discovery: anything asking version control what this build is.
#:
#: Matched as a PATTERN rather than as a substring, and that is the whole point.
#: Git's own options sit between `git` and its subcommand, and the one place uses
#: them: `git -C '$(STAMP_SRC)' rev-parse HEAD` and
#: `git --no-optional-locks -C '$(STAMP_SRC)' status --porcelain` are what
#: ci/make/go.mk writes. A substring test for "git rev-parse" sees neither -- so
#: the copy this rule is likeliest to meet, a paste of the one place, would have
#: been the one copy invisible to the check that forbids it, while only the naive
#: spelling nobody here writes was caught.
_WORD = r"""(?:'[^']*'|"[^"]*"|[^\s'";|&]+)"""
#: `-C <path>`, `-c k=v`, `--git-dir=...`, `--no-optional-locks`, `-P`: git's own
#: options, any number of them, before the subcommand.
_GIT_OPT = rf"(?:-[cC]\s+{_WORD}|--[A-Za-z][A-Za-z0-9-]*(?:=\S+)?|-[A-Za-z])"
#: `git`, however it is spelled, with its options skipped.
_GIT = rf"(?:\bgit\b|\$[({{]GIT[)}}])(?:\s+{_GIT_OPT})*\s+"
DISCOVERY = (
    ("git rev-parse", re.compile(_GIT + r"rev-parse\b")),
    ("git describe", re.compile(_GIT + r"describe\b")),
    ("git status --porcelain", re.compile(_GIT + r"status\b[^\n;|&]*?--porcelain\b")),
    ("git log -1", re.compile(_GIT + r"log\b[^\n;|&]*?\s-1(?!\S)")),
)

#: Targets that consume the stamp: they compile, run or lint the component's own
#: sources, so each has to be built against the tree it is running over rather
#: than against whatever an earlier build left on disk. `fmt` is not one of them:
#: gofmt reads syntax and never reaches the generated source's contents.
CONSUMERS = (
    "build", "dev", "gen", "lint",
    "test", "test-fast", "test-integration", "test-conformance",
)

#: A make RULE, as against an assignment (`:=`, `?=`, `::=`) or a recipe line
#: (tab-indented). Group 1 is the target list, group 2 the prerequisites.
RULE = re.compile(
    r"^(?![\t ])([A-Za-z0-9_.%/$()+-]+(?:[ \t]+[A-Za-z0-9_.%/$()+-]+)*)[ \t]*:(?![=:])([^#\n]*)",
    re.M,
)

#: An `include` DIRECTIVE naming one of the shared fragments -- the thing that
#: actually puts the `stamp` target within this file's reach.
#:
#: Not a substring test for the fragment's path. A file that merely MENTIONS
#: ci/make/go.mk mentions it in a comment, and whether case 8 examined a build
#: file would then depend on whether someone had written the fragment's name in
#: prose above it. That was not hypothetical: writing the word `ci/make/go.mk`
#: into a fixture's explanatory header turned the check on for that fixture and
#: moved its violation count. A check that switches itself on and off according
#: to the wording of a comment is not enforcing anything, in either direction.
INCLUDE = re.compile(
    r"^[ \t]*-?include[ \t]+[^\n#]*(?:" + "|".join(re.escape(f) for f in FRAGMENTS) + r")",
    re.M,
)

MARKER = re.compile(r"\btree=(\S+)")
COMMIT = re.compile(r"\bcommit=(\S+)")


def discovered(text: str) -> list[str]:
    """Every spelling of the discovery this text contains, named."""
    return [name for name, pattern in DISCOVERY if pattern.search(text)]


def rules(text: str) -> dict[str, list[str]]:
    """target -> its prerequisites, for every rule declared in one make file."""
    out: dict[str, list[str]] = {}
    for m in RULE.finditer(text):
        prereqs = m.group(2).split()
        for target in m.group(1).split():
            out.setdefault(target, []).extend(prereqs)
    return out


def depends_on(target: str, deps: dict[str, list[str]], want: str, seen: set[str] | None = None) -> bool:
    """Whether `want` is a prerequisite of `target`, directly or through another.

    Transitive, because `test: test-fast test-integration test-conformance` is an
    aggregate whose parts carry the dependency, and demanding it directly on the
    aggregate would be demanding a spelling rather than the property.
    """
    seen = set() if seen is None else seen
    if target in seen:
        return False
    seen.add(target)
    for prereq in deps.get(target, []):
        if prereq == want or depends_on(prereq, deps, want, seen):
            return True
    return False


def language(comp: Path) -> str | None:
    if (comp / "mix.exs").is_file():
        return "elixir"
    if (comp / "go.mod").is_file():
        return "go"
    return None


#: Not the component's own source: fetched dependencies and build output. A
#: third-party library asking git what IT is says nothing about this component,
#: and scanning a dependency tree on every run is slow as well as wrong.
NOT_ITS_OWN = {"_build", "deps", "dist", "node_modules", ".git"}


def component_files(comp: Path) -> list[Path]:
    """A component's own build files and sources -- never its generated stamp."""
    found = [p for p in (comp / "Makefile", comp / "mix.exs") if p.is_file()]
    for ext in ("*.go", "*.ex", "*.exs"):
        found += [
            p
            for p in comp.rglob(ext)
            if p.name not in STAMP_FILE.values() and not NOT_ITS_OWN & set(p.parts)
        ]
    return sorted(found)


def entry_points(comp: Path, lang: str) -> list[Path]:
    """Where this component starts, which is where it says what it is.

    EVERY `package main` under cmd/, not the one the Makefile's CMD names. A
    component's other binaries are shipped and spawned like its first one --
    conformance's recording-origin is the instrument at the far end of the
    harness, and a recorded exchange with no account of the instrument that took
    it is an anecdote. Reading a single CMD made those invisible while the
    coverage line still said the component was covered.
    """
    if lang == "elixir":
        return sorted((comp / "lib").rglob("application.ex"))
    return sorted(p for p in (comp / "cmd").glob("*/main.go") if p.is_file())


def test_files(comp: Path, lang: str) -> list[Path]:
    if lang == "elixir":
        return sorted((comp / "test").rglob("*.exs"))
    return sorted(comp.rglob("*_test.go"))


#: The name the gate stamps its throwaway tree with, so that STAMP_COMPONENT
#: being honoured at all is itself observable in the emitted stamp.
DEMO_COMPONENT = "demo"

#: Every field the stamping place reports, read back off the line it echoes.
#: `(\S+)` deliberately does not match an empty value: a field emitted blank is
#: reported as MISSING below, which is what it is.
EMITTED = re.compile(r"\b(" + "|".join(FIELDS) + r")=(\S+)")

#: What each field must look like when the one place emits it. This is the whole
#: of the stamp's value contract, and it lives HERE -- asserted against the
#: mechanism when it is RUN -- rather than compiled into each component's test as
#: another snapshot of a format owned somewhere else. Four modules each carrying
#: these five patterns would be four copies of one thing
#: (docs/code/rules/duplication-threshold.md), and each would be a snapshot of
#: whatever the recipe emitted on the day it was pasted. What a component's own
#: test binds is the value this file cannot know: which component it is.
SHAPES = {
    "component": re.compile(rf"^{DEMO_COMPONENT}$"),
    "version": re.compile(r"^\S+$"),
    "commit": re.compile(r"^([0-9a-f]{40}|unknown)$"),
    "tree": re.compile(r"^(clean|dirty|unknown)$"),
    "built_at": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
}


def stamp_once(one_place: Path, tree: Path) -> dict[str, str]:
    """Run the tree's own stamping mechanism against `tree`; return every field."""
    done = subprocess.run(
        [
            "make", "-s", "-f", str(one_place), STAMP_TARGET,
            f"REPO_ROOT={tree}", f"STAMP_SRC={tree}", f"STAMP_COMPONENT={DEMO_COMPONENT}",
            "STAMP_LANGUAGE=go", "STAMP_OUT=cmd/demo/build_stamp.go", "CMD=demo",
        ],
        capture_output=True, text=True, cwd=str(tree),
    )
    return dict(EMITTED.findall(done.stdout + done.stderr))


def dirty_markers(one_place: Path) -> tuple[dict[str, str], dict[str, str], str]:
    """Stamp one throwaway revision twice: clean, then with one file modified."""
    if not shutil.which("make") or not shutil.which("git"):
        return {}, {}, "make or git is not on PATH, so nothing was exercised"
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        (tree / "cmd" / "demo").mkdir(parents=True)
        (tree / "one.txt").write_text("one\n", encoding="utf-8")
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
        git = ["git", "-c", "user.name=gate", "-c", "user.email=gate@example.invalid"]
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "one revision"]):
            done = subprocess.run(git + args, cwd=str(tree), env=env, capture_output=True)
            if done.returncode != 0:
                return {}, {}, f"could not build a throwaway repository: {args[0]}"
        clean = stamp_once(one_place, tree)
        (tree / "one.txt").write_text("one modified file\n", encoding="utf-8")
        modified = stamp_once(one_place, tree)
        return clean, modified, ""


def check_emitted_shapes(report: Report, emitted: dict[str, str]) -> None:
    """(9) Every field the one place emits, held to the shape it promises.

    Decided by RUNNING the mechanism, like case 6, and over the same throwaway
    revision -- so it is the recipe that is on trial, not a generated file some
    earlier build left behind. A field that came out blank never matched
    `(\\S+)` and so is reported here as missing, which is the same defect said
    plainly: a stamp carrying an empty commit is not a stamp with a short value
    in it, it is a binary that cannot say what it was built from.
    """
    for name in FIELDS:
        value = emitted.get(name, "")
        if not value:
            report.fail(
                f"{ONE_PLACE}: its `{STAMP_TARGET}` target emitted no `{name}` -- a stamp "
                f"missing a field it names is a binary that cannot say what it was built "
                f"from, in the one field a reader would go to"
            )
        elif not SHAPES[name].match(value):
            report.fail(
                f"{ONE_PLACE}: its `{STAMP_TARGET}` target emitted {name}={value!r}, which "
                f"is not the shape this field promises ({SHAPES[name].pattern}) -- provenance "
                f"is a value of the promised shape, or the word unknown, never something "
                f"that merely resembles one"
            )


def check_dirty_marker(report: Report, one_place: Path) -> None:
    clean, modified, err = dirty_markers(one_place)
    if err:
        report.fail(f"{ONE_PLACE}: {err} -- the dirty-tree marker is then a claim nothing tested")
        return
    # (9) every field it emitted, held to its promised shape -- off the clean run,
    # because that is the one whose expected values are all knowable.
    check_emitted_shapes(report, clean)
    # The tree marker is checked on BOTH runs, because it is the only field whose
    # value legitimately differs between them and so the only one the clean run
    # cannot speak for. A mechanism emitting `tree=modified` instead of `dirty`
    # passes the clean run untouched and then writes a word no reader of this
    # repository's stamps is expecting into every dirty build.
    dirty = modified.get("tree", "")
    if dirty and not SHAPES["tree"].match(dirty):
        report.fail(
            f"{ONE_PLACE}: its `{STAMP_TARGET}` target emitted tree={dirty!r} for a "
            f"modified tree, which is not the shape this field promises "
            f"({SHAPES['tree'].pattern}) -- the marker is read by everything that "
            f"consumes a stamp, and a fourth word in that field is a value none of "
            f"them has a branch for"
        )

    if not clean.get("tree") or not modified.get("tree"):
        report.fail(
            f"{ONE_PLACE}: its `{STAMP_TARGET}` target reported no tree marker over a "
            f"throwaway repository -- a stamp that names no state of the tree it was "
            f"built from carries three fields and calls itself provenance"
        )
        return
    if clean["tree"] == modified["tree"]:
        report.fail(
            f"{ONE_PLACE}: two builds of one revision differing by one modified file "
            f"both reported tree={clean['tree']} -- a marker that never moves is "
            f"indistinguishable from an honest one in every artifact it reaches"
        )
    if clean.get("commit") and clean["commit"] != modified.get("commit"):
        report.fail(
            f"{ONE_PLACE}: the same revision stamped two different commits "
            f"({clean['commit']} and {modified.get('commit')}) -- the tree state has leaked "
            f"into the field that identifies the revision, and neither field can then be read"
        )


def check_stamp_wiring(report: Report, rel: str, text: str) -> None:
    """(8) A target that consumes the stamp and does not depend on it.

    Case 5 decides that the `stamp` target EXISTS. A target existing is not a
    target that runs: drop `stamp` from the tier and build prerequisites and
    every recipe here still works, still compiles, still passes -- against
    whatever generated stamp the last build happened to leave on disk. The
    never-stamped case is caught by the compiler (the reporter is undefined);
    the stale-stamp case is caught by nothing but this, and a stale stamp is the
    one that reaches an artifact and lies in it.
    """
    deps = rules(text)
    # Only where the stamp is actually in reach: a file that neither declares it
    # nor INCLUDES the fragment that does is not the place this is decided. The
    # reach test reads the `include` directive rather than any mention of the
    # fragment's path, so a comment naming ci/make/go.mk cannot switch this case
    # on and a build file that quietly stopped including it cannot switch it off.
    if STAMP_TARGET not in deps and not INCLUDE.search(text):
        return
    for target in CONSUMERS:
        if target in deps and not depends_on(target, deps, STAMP_TARGET):
            report.fail(
                f"{rel}: `{target}` does not depend on `{STAMP_TARGET}` -- it builds, "
                f"runs or lints this component's own sources against whatever stamp an "
                f"earlier build left on disk, so what the binary reports is the "
                f"provenance of some other tree and nothing can tell the two apart"
            )


def check_component(report: Report, scan_root: Path, comp: str, lang: str) -> None:
    path = scan_root / comp
    # (1) a second copy of the discovery, in the component itself.
    for source in component_files(path):
        text = source.read_text(encoding="utf-8", errors="replace")
        for marker in discovered(text):
            rel = source.relative_to(scan_root).as_posix()
            report.fail(
                f"{comp}: {rel} asks version control what this build is (`{marker}`) "
                f"-- the stamp comes from {ONE_PLACE} and nowhere else, or the two "
                f"copies drift and neither side can see it"
            )

    # (3) EVERY entry point reports it.
    entries = entry_points(path, lang)
    if not entries:
        report.fail(
            f"{comp}: no entry point found for a {lang} component, so there is no "
            f"startup at which it says what it was built from"
        )
    else:
        silent = [
            p for p in entries
            if not calls_reporter(p.read_text(encoding="utf-8", errors="replace"), lang)
        ]
        if silent:
            report.fail(
                f"{comp}: its entry point ({', '.join(p.relative_to(scan_root).as_posix() for p in silent)}) "
                f"never calls {REPORTER[lang]} -- the stamp is compiled in and never "
                f"reported, which is the prior art's 75 events with no handler"
            )

    # (8) its own build file, where it has one, wires the stamp into what builds.
    build = path / "Makefile"
    if build.is_file():
        check_stamp_wiring(report, f"{comp}/Makefile", build.read_text(encoding="utf-8"))

    # (4) a test EXERCISES what reports it -- a call, not a mention. A test file
    # whose comment explains startupReport and whose body never invokes it leaves
    # the reported value asserted by nothing while satisfying a name search, which
    # is the same defeat case 3 carried.
    tests = test_files(path, lang)
    if not any(calls_reporter(p.read_text(encoding="utf-8", errors="replace"), lang) for p in tests):
        report.fail(
            f"{comp}: no test under it calls {REPORTER[lang]} -- the reported value is "
            f"then asserted by nothing, and a startup line nobody reads drifts from the "
            f"stamp at the first refactor"
        )


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    candidates = [
        c for c in manifest["code_standards"]["components"]["candidates"]
        if not c.startswith("_")
    ]
    report = Report(GATE_ID, RULE_NOTE)

    present = {}
    for comp in candidates:
        if not (scan_root / comp / "Makefile").is_file():
            continue
        lang = language(scan_root / comp)
        if lang is None:
            continue
        report.examine(comp)
        present[comp] = lang

    fragments = [f for f in FRAGMENTS if (scan_root / f).is_file()]
    one_place = scan_root / ONE_PLACE

    # (5) the one place, and (2) any second copy of it.
    for rel in fragments:
        report.examine(rel)
        text = (scan_root / rel).read_text(encoding="utf-8")
        if f"\n{STAMP_TARGET}:" not in text:
            report.fail(
                f"{rel}: declares no `{STAMP_TARGET}` target -- every component it "
                f"serves is built with no provenance at all"
            )
        found = [] if rel == ONE_PLACE else discovered(text)
        if found:
            report.fail(
                f"{rel}: computes provenance itself rather than delegating to "
                f"{ONE_PLACE} -- a second copy of the discovery ({', '.join(found)}), "
                f"which is the whole of what this rule forbids"
            )
        # (8) the stamp exists here and is wired into what consumes it.
        check_stamp_wiring(report, rel, text)
    if present and not one_place.is_file():
        report.fail(
            f"{ONE_PLACE}: absent while {len(present)} component(s) are present -- "
            f"there is no one place, so each of them stamps itself or not at all"
        )

    for comp, lang in sorted(present.items()):
        check_component(report, scan_root, comp, lang)

    # (6) the one dynamic case: the marker has to move with the tree.
    if one_place.is_file() and f"\n{STAMP_TARGET}:" in one_place.read_text(encoding="utf-8"):
        check_dirty_marker(report, one_place)

    # (7) is about the TRACKED tree, so it is repository-scoped: a violating input
    # is untracked by construction and would report nothing either way.
    if on_tracked_tree(scan_root):
        for rel in tracked_stamps(scan_root):
            report.fail(
                f"{rel}: a generated stamp, tracked -- committing one makes the tree "
                f"dirty the moment it is regenerated, so the marker it carries stops "
                f"being true about the tree it describes"
            )

    report.coverage(
        covered=[*sorted(present), *fragments],
        excluded=[
            "whether a configuration item collides with a provenance field (no schema exists; tasks 5.1, 5.2)",
            "whether a reported value is TRUE -- that the commit is this tree's commit, that the build time is this build's",
            "whether a test that calls the reporter asserts anything worth asserting about what comes back",
            "a component's other binaries beyond cmd/*/main.go -- a package main outside cmd/ is not examined",
        ],
        # The counted set is the components AND the shared fragments: a failure
        # here names either, and a count that excluded one of them would be a
        # gate reporting a reach it does not have.
        kind="stamping subject",
        source="manifest",
        scan_root=scan_root,
    )
    # The entry points are NAMED, not just counted. A component's second binary is
    # shipped and spawned like its first, and "components stamped: 4" over a tree
    # where one component has two `package main` directories reads as a claim about
    # four things while saying nothing about which binaries were actually examined.
    # Printing them is what makes the difference between a covered second entry
    # point and an invisible one legible from the output alone.
    entries = {
        comp: [p.relative_to(scan_root / comp).as_posix() for p in entry_points(scan_root / comp, lang)]
        for comp, lang in sorted(present.items())
    }
    print(
        f"  components stamped: {len(present)} ({', '.join(f'{c}/{l}' for c, l in sorted(present.items())) or '-'})"
        f" | fragments: {len(fragments)} | fields: {', '.join(FIELDS)}"
    )
    named = "; ".join(f"{c}: {', '.join(v) or 'none'}" for c, v in entries.items())
    print(
        f"  entry points reporting the stamp: {sum(len(v) for v in entries.values())}"
        f" ({named or '-'})"
    )
    return report.finish(report_only=report_only)


def tracked_stamps(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    names = set(STAMP_FILE.values())
    return [p for p in out.decode("utf-8").split("\0") if p and p.rsplit("/", 1)[-1] in names]


main_guard(run)
