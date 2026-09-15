#!/usr/bin/env python3
"""Gate: build provenance is derived in one place, and nowhere else.

Enforces docs/code/rules/build-provenance-from-one-place.md. rebuild-plugboard
task 3.13.

## Why the first attempt at this gate was worthless, and what is different

It matched the git commands as plain substrings against whole files. The exact
spelling `ci/stamp.py` used defeated it -- `_git("rev-parse", "HEAD")` never
contains the string `git rev-parse` -- so it passed over the tree it governed.
Patching its matching back to the form a reviewer had already condemned left
every fixture still green, which is the tell: nothing was pinned to the repair.

The second attempt, in this file's own first draft, repeated it. Declaring
`git rev-parse` and friends as `derives_with` failed the one place immediately,
for the same reason.

So the subject is not a command spelling. It is EXECUTION. A component that
derives its own provenance has to run a subprocess -- there is no other route
from Go, Elixir or make to git -- and that is a property of a handful of
language primitives that do not get respelled. Comments and doc strings are
stripped first, because every subject file in this tree mentions git in prose
while none of them runs it, and a gate that cannot tell those apart is a gate
nobody can leave switched on.

Three directions, which is what pins it:

  1. A subject file that executes anything fails, naming the primitive. Two
     derivations drift apart while each looks self-consistent.
  2. The one place that has STOPPED deriving fails. Move the computation out and
     this gate goes red, so the arrangement cannot be quietly dismantled. The
     previous version could not detect this at all.
  3. A build file that never calls the one place fails. A stamp nothing
     generates is reported empty, which at startup reads exactly like a binary
     that was never stamped.

## Why the marker is `git` and not "runs a subprocess"

The first draft of the discovered version refused any execution primitive --
exec.Command, os/exec, System.cmd, Port.open -- and immediately flagged four
conformance files. Rightly, on its own terms, and wrongly in fact: the conformance
harness STARTS PROCESSES for a living. That is its job, not a provenance
derivation.

So the marker is `git` itself, in executable text. A component has no legitimate
reason to name it: provenance is the only thing it would be asking for, and that
comes from the generated stamp. Stripping comments first is what makes this
usable at all -- seven files in this tree mention git in prose and none runs it.

## Why the roster is discovered

The first version of this file listed its subjects in ci/vault.json. A reviewer
attacking it planted sidecar/cmd/probe/main.go -- a new Go main deriving its own
commit with exec.Command("git", "rev-parse", "--short", "HEAD") -- and the gate
passed, because the list did not name the new file. A declared roster is coverage
that silently stops growing, which is worse than no coverage: it reports a number.

So every TRACKED source under a declared component root is a subject. Tracked is
the right set, not every file on disk: CI checks out what is tracked, so an
untracked experiment is not in any build.

## What it does not decide

Whether the reported values are RIGHT -- ci/provenance-check.py runs each of the
four components and compares against git read independently. Whether a released
artifact carries the stamp: task 70.7's. Whether a configuration item collides
with a provenance field: needs the schema task 5.2 builds, and is named there
rather than faked here.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, subject_source
from _source import config, scan_excludes, sources

GATE_ID = "provenance"
RULE_NOTE = "docs/code/rules/build-provenance-from-one-place.md"


#: Elixir doc strings are attribute-prefixed heredocs. They are prose, and every
#: other heredoc is not, so they are removed by name rather than by stripping all
#: heredocs -- a string is executable text, and `System.cmd("git", ...)` is one.
_EX_DOC = re.compile(r'@(?:module)?doc\s+"""(?:.|\n)*?"""')

#: A comment the BUILD RUNS. `go generate` executes these, so a `//go:generate`
#: that derives provenance is executable text that comment-stripping would delete
#: by construction. Found by a reviewer, who used exactly that to hide one.
_GO_DIRECTIVE = "//go:"


def _scan(text: str, line: tuple, block: list, quotes: list, keep: tuple) -> str:
    """Comments removed, string literals preserved, by scanning rather than regex.

    A regex deleting from `//` to end of line also deletes the rest of any line
    holding "http://" inside a string. A reviewer used that to hide an
    exec.Command("git", ...) from this gate, in Go that compiles and vets clean;
    the same trick worked in Elixir, where `#{` begins an interpolation and not a
    comment. Both needed the scanner to know it is inside a string.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        quote = next((q for q in quotes if text.startswith(q, i)), None)
        if quote:
            out.append(quote)
            j = i + len(quote)
            while j < n:
                if text[j] == "\\" and quote != "`":
                    out.append(text[j:j + 2])
                    j += 2
                    continue
                if text.startswith(quote, j):
                    out.append(quote)
                    j += len(quote)
                    break
                out.append(text[j])
                j += 1
            i = j
            continue
        opened = next(((a, b) for a, b in block if text.startswith(a, i)), None)
        if opened:
            end = text.find(opened[1], i + len(opened[0]))
            i = n if end < 0 else end + len(opened[1])
            continue
        marker = next((c for c in line if text.startswith(c, i)), None)
        if marker and not any(text.startswith(k, i) for k in keep):
            end = text.find("\n", i)
            i = n if end < 0 else end
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def strip_prose(text: str, suffix: str) -> str:
    """Only what RUNS. Comments and doc strings gone; string literals kept."""
    if suffix == ".go":
        return _scan(text, ("//",), [("/*", "*/")], ['"', "`", "'"], (_GO_DIRECTIVE,))
    if suffix in (".ex", ".exs"):
        return _scan(_EX_DOC.sub("", text), ("#",), [], ['"""', '"', "'"], ())
    return _scan(text, ("#",), [], [], ())


def derives(source: Path) -> list[str]:
    """What is missing from the one place, read as CODE rather than as text.

    Parsed with `ast` -- standard library, so the gate keeps its no-dependency
    rule. A substring search over the file was satisfied by this module's own
    docstring, which names both `subprocess` and `git` while running neither: the
    check could not have failed, and a reviewer showed it by deleting the entire
    derivation and watching the gate stay green.
    """
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"does not parse ({exc.msg})"]
    missing = []
    runs_git = any(
        isinstance(node, ast.Call)
        and any(isinstance(a, ast.Constant) and a.value == "git"
                for arg in node.args
                for a in (arg.elts if isinstance(arg, (ast.List, ast.Tuple)) else [arg]))
        for node in ast.walk(tree)
    )
    if not runs_git:
        missing.append("any call passing `git` as a command argument")
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    if "subprocess" not in names:
        missing.append("any use of `subprocess`")
    return missing


def build_files(scan_root: Path, cfg: dict, manifest: dict) -> list[str]:
    """Every TRACKED build file: `Makefile` and `*.mk`, discovered not listed.

    Through the same reader the source roster uses, with the build-file suffixes
    standing in for the language suffixes -- so "tracked" means exactly what it
    means there, and a vendored proxy/deps/mix_audit/Makefile that no checkout of
    this repository contains is not a subject.
    """
    suffixes = {s: "make" for s in cfg["build_file_suffixes"]}
    return sources(scan_root, {"languages": suffixes}, manifest)


#: A file a build recipe hands to an interpreter. `$(VAR)/` prefixes are dropped
#: because make expands them and this does not need to: what matters is the path
#: inside the tree.
_SCRIPT = re.compile(r"(?:\$\([A-Za-z_]+\)/)?([\w./-]+\.(?:sh|bash|py))")


def invoked_scripts(scan_root: Path, build_files: list[str]) -> list[str]:
    """Every script a build file hands to an interpreter, as a subject.

    One level of shell indirection defeated the first discovered roster: a
    reviewer put `git rev-parse --short HEAD` in ci/derive-provenance.sh and one
    line in ci/make/go.mk --

        PROV := $(shell sh $(REPO_ROOT)/ci/derive-provenance.sh)

    -- so go.mk named no git, the script was under no component root, and the
    derivation ran at make parse time while the gate reported no violations. It
    is tree-second-derivation's exact defect moved one file sideways.

    Sweeping in every tracked *.sh would have caught it and also caught scripts
    no build runs. Following the invocation catches what the build reaches, which
    is the set that can actually derive anything.
    """
    found: set[str] = set()
    for rel in build_files:
        path = scan_root / rel
        if not path.is_file():
            continue
        for match in _SCRIPT.findall(path.read_text(encoding="utf-8")):
            candidate = match.lstrip("./")
            if (scan_root / candidate).is_file():
                found.add(candidate)
    return sorted(found)


def _fields_of(source: Path) -> list[str]:
    """The string members of the module's FIELDS assignment, read as code."""
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(x, ast.Name) and x.id == "FIELDS" for x in node.targets):
            value = node.value
            if isinstance(value, (ast.Tuple, ast.List)):
                return [e.value for e in value.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["provenance"]
    one_place = cfg["one_place"]
    fields = [f for f in cfg["fields"] if not f.startswith("_")]
    forbidden = [m for m in cfg["executes"] if not m.startswith("_")]
    # The roster is DISCOVERED, not listed. A hardcoded subject list is coverage
    # that silently stops growing: a reviewer planted sidecar/cmd/probe/main.go,
    # a new Go main deriving its own commit with exec.Command("git", ...), and
    # the listed version of this gate passed over it because the list did not
    # name it. Every tracked source under a declared component root is held.
    roots = tuple(r for r in cfg["component_roots"] if not r.startswith("_"))
    discovered = [s for s in sources(scan_root, config(manifest), manifest)
                  if s.startswith(roots)]
    # Build files are discovered too. Listing them missed every per-component
    # Makefile -- conformance/Makefile among them -- so a component's own build
    # file could derive provenance freely while the gate reported green over the
    # shared includes it did name.
    builds = sorted(set(build_files(scan_root, cfg, manifest)))
    # Plus whatever those build files hand to an interpreter. The one place is
    # excluded: it is the file that IS allowed to derive.
    reached = [s for s in invoked_scripts(scan_root, builds) if s != one_place]
    subjects = sorted(set(discovered) | set(builds) | set(reached))
    calls = {k: v for k, v in cfg["called_as"].items() if not k.startswith("_")}
    #: Files that legitimately name git for a reason that is not provenance.
    #: Declared with the reason, and held in BOTH directions below: an entry whose
    #: file has stopped naming git is an exemption outliving what earned it.
    permitted = {k: v for k, v in cfg["permitted_git"].items() if not k.startswith("_")}
    used: set[str] = set()
    report = Report(GATE_ID, RULE_NOTE)

    # (2) The one place still derives it.
    source = scan_root / one_place
    report.examine(one_place)
    if not source.is_file():
        report.fail(
            f"{one_place}: the one place provenance is derived is absent, so "
            f"every component either carries no stamp or has grown its own"
        )
    else:
        gone = derives(source)
        declared = set(_fields_of(source))
        absent = [f for f in fields if f not in declared]
        if absent:
            gone.append(f"the field(s) {', '.join(absent)} in its FIELDS tuple")
        if gone:
            report.fail(
                f"{one_place}: no longer holds {'; '.join(gone)} -- the "
                f"computation has left the one place, which is the arrangement "
                f"this gate exists to hold. Moving it back is the fix; widening "
                f"this check is not"
            )

    # (1) and (3) Each subject file: derives nothing itself, and calls the one
    # place where it is the thing that must generate a stamp.
    for rel in subjects:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        raw = path.read_text(encoding="utf-8")
        body = strip_prose(raw, path.suffix if path.suffix else ".mk")
        # One finding per FILE, not per primitive: `exec.Command("git", ...)`
        # trips two markers and is one defect.
        hits = [m for m in forbidden
                if re.search(rf"(?<![\w.]){re.escape(m)}(?![\w])", body)]
        if hits and rel in permitted:
            used.add(rel)
        elif hits:
            report.fail(
                f"{rel}: names {', '.join(f'`{h}`' for h in hits)} in executable "
                f"text -- provenance is derived once, in {one_place}. A second "
                f"derivation drifts from the first while both stay "
                f"self-consistent, so neither looks wrong on its own"
            )
        if rel in calls and calls[rel] not in raw:
            report.fail(
                f"{rel}: never invokes `{calls[rel]}` -- a component whose stamp "
                f"nothing generates reports an empty one, and an empty stamp "
                f"reads at startup exactly like a binary that was never stamped"
            )

    for rel, reason in sorted(permitted.items()):
        if rel in used or not (scan_root / rel).is_file():
            continue
        report.fail(
            f"{rel}: declared a permitted use of git -- \"{reason[:70]}...\" -- "
            f"but it no longer names git. The exemption outlived what earned it; "
            f"delete it"
        )

    report.coverage(
        covered=[one_place, *subjects],
        excluded=[
            "whether the reported values are right (ci/provenance-check.py runs each component)",
            "whether a released artifact carries the stamp (task 70.7)",
            "a configuration item colliding with a provenance field (needs task 5.2's schema)",
        ],
        kind="provenance subject",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(f"  one place: {one_place} | discovered sources: {len(discovered)} | "
          f"build files: {len(builds)} | scripts they invoke: {len(reached)} | "
          f"execution primitives refused: {len(forbidden)}")
    return report.finish(report_only=report_only)


main_guard(run)
