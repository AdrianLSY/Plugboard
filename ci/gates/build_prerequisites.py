#!/usr/bin/env python3
"""Gate: a generated source is generated before anything compiles it.

Enforces docs/code/rules/generated-sources-are-generated-first.md.

## The defect this is made of

Build provenance (task 3.13) put a GENERATED package -- internal/buildstamp --
into every Go component's import graph. The make targets declared the dependency:
`lint: stamp`, `test-fast: stamp`. Two CI jobs reach the Go toolchain WITHOUT
going through make -- `govulncheck` in security.yml and the golangci-lint action
in test.yml -- so the make graph's dependency never reached them, and the security
job failed on `package plugboard/sidecar/internal/buildstamp is not in std`.

Nothing was wrong in either encoding read alone. The make file was right. The
workflow was right about what it ran. What was missing was the relation BETWEEN
them, which is the shape this repository keeps finding in itself and the reason
ci/gates/correspondences.py exists.

## Two halves, because the obligation has two encodings

  1. MAKE: every target whose recipe TYPE-CHECKS -- in either language -- lists
     the generating target among its prerequisites. Both languages, because the
     first version of this gate named only the Go make files and the Elixir half
     of the identical defect reached CI: `mix compile --warnings-as-errors` on a
     missing Plugboard.BuildStamp. A gate whose declared coverage omits half its
     subject reports green over that half. Add a target that compiles without it and
     this fails, so the make graph cannot quietly lose the edge.
  2. WORKFLOW: every job that reaches the toolchain around make runs the
     generator FIRST. Order is checked, not containment: a step that regenerates
     a source after the step that compiled it satisfies a containment test and
     fixes nothing.

## Why the operation, not the target name

The first draft keyed on `$(GO)` appearing anywhere in a recipe, and flagged
`fmt`. Checked rather than argued about: with the generated package deleted,
`go fmt ./...` exits 0 and `go vet ./...` fails on
`package .../internal/buildstamp is not in std`. `go fmt` does not type-check, so
it is not a compiling site -- and keying on the OPERATION says that, where an
exemption list keyed on the name `fmt` would have said only that this one target
was forgiven.

## What it does not decide

Whether the generated source is CORRECT -- ci/gates/provenance.py holds where it
comes from, ci/provenance-check.py holds what it says. Whether a command reached
through a variable, a script or an alias compiles anything: `run: $TOOL` runs
something no regex can name, as ci/gates/_workflow.py states. A floor, not a proof.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root
from _source import sources
from _workflow import first_execution

GATE_ID = "build-prerequisites"
RULE_NOTE = "docs/code/rules/generated-sources-are-generated-first.md"

#: A make rule. The leading `.` of `.PHONY` is excluded by requiring a letter or
#: underscore; the negative lookahead on `=` excludes `VAR := value`, which is a
#: colon in a line that is not a rule. Underscores and capitals are allowed
#: because make allows them and a target named `test_fast` whose recipe this
#: dropped would have been silently uncovered.
_RULE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(?!=)\s*(.*)$")
#: A job key. The trailing-comment group matters: `  lint:  # go only` is a job,
#: and without it that job's steps were absorbed into the previous job -- which
#: is silent NON-COVERAGE, the failure mode this gate exists to prevent.
_JOB = re.compile(r"^  ([A-Za-z0-9_-]+):[ \t]*(#.*)?$")


def compiling(cfg: dict) -> list[re.Pattern]:
    """One pattern per toolchain: any declared invocation followed by a declared verb.

    Declared as invocation + verb rather than as literal strings, so `$(GO) build`,
    `go build` and `$(GOCMD) build` are one declaration. A reviewer defeated the
    literal-string version with `cd sidecar && go build ./...` in a recipe and with
    `$(GO) install`, neither of which any listed literal matched.
    """
    out = []
    for name, spec in sorted(cfg["compiles"].items()):
        if name.startswith("_"):
            continue
        inv = "|".join(re.escape(i) for i in spec["invocations"])
        verbs = "|".join(re.escape(v) for v in spec["verbs"])
        out.append(
            re.compile(rf"(?:^|[\s;&|(]){{0,1}}(?:{inv})\s+(?:{verbs})(?![\w-])")
        )
    for tool in cfg["standalone_tools"]:
        out.append(re.compile(rf"(?<![\w/-]){re.escape(tool)}(?![\w-])"))
    return out


def first_match(body: str, patterns: list[re.Pattern]) -> int:
    """Source line index of the first EXECUTED line matching any pattern, or -1."""
    from _workflow import executable_lines

    for i, text in executable_lines(body):
        for seg in re.split(r"&&|\|\||;|\|", text):
            if any(p.search(seg.strip()) for p in patterns):
                return i
    return -1


def make_rules(text: str) -> dict[str, tuple[set[str], list[str]]]:
    """target -> (prerequisites, recipe lines). Recipe lines are tab-indented."""
    out: dict[str, tuple[set[str], list[str]]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("\t"):
            if current is not None:
                out[current][1].append(line)
            continue
        m = _RULE.match(line)
        if m:
            current = m.group(1)
            assert current is not None
            out.setdefault(current, (set(m.group(2).split()), []))
        elif line.strip() and not line.lstrip().startswith("#"):
            current = None
    return out


def jobs(body: str) -> list[tuple[str, str]]:
    """(job name, job body) for each job in a workflow."""
    lines = body.splitlines()
    starts = [(i, m.group(1)) for i, l in enumerate(lines) if (m := _JOB.match(l))]
    found = []
    for n, (i, name) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        found.append((name, "\n".join(lines[i:end])))
    return found


def run(scan_root: Path, report_only: bool) -> int:
    cfg = load_manifest(repo_root())["build_prerequisites"]
    target = cfg["prerequisite_target"]
    markers = compiling(cfg)
    compiles = markers
    provides = [c for c in cfg["provides"] if not c.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)
    covered: list[str] = []

    # 1. The make side. The roster is DISCOVERED -- every tracked `Makefile` and
    # `*.mk` -- not listed. A listed pair had already missed the Elixir include
    # once, and would miss a new component's Makefile the same way: a roster is
    # coverage that silently stops growing, and it reports a number while it does.
    manifest = load_manifest(repo_root())
    make_files = sources(
        scan_root,
        {"languages": {s: "make" for s in cfg["build_file_suffixes"]}},
        manifest,
    )
    for rel in make_files:
        path = scan_root / rel
        if not path.is_file():
            continue
        for name, (prereqs, recipe) in sorted(
            make_rules(path.read_text(encoding="utf-8")).items()
        ):
            if not any(m.search(l) for l in recipe for m in markers):
                continue
            report.examine(f"{rel}:{name}")
            covered.append(f"{rel}:{name}")
            if target not in prereqs:
                report.fail(
                    f"{rel}: target `{name}` type-checks but does not list "
                    f"`{target}` as a prerequisite -- it compiles a generated "
                    f"source without generating it, which fails on any tree where "
                    f"the generated file is absent. A clean checkout is exactly "
                    f"that tree"
                )

    # 2. The workflow side.
    wf_dir = scan_root / cfg["workflows_dir"]
    globs = cfg["workflow_globs"]
    found_wf = (
        sorted({p for g in globs for p in wf_dir.glob(g)}) if wf_dir.is_dir() else []
    )
    for path in found_wf:
        rel = str(path.relative_to(scan_root))
        for name, body in jobs(path.read_text(encoding="utf-8")):
            at = first_match(body, compiles)
            if at < 0:
                continue
            report.examine(f"{rel}:{name}")
            covered.append(f"{rel}:{name}")
            generated_at = first_execution(body, provides)  # literal commands
            if generated_at < 0:
                report.fail(
                    f"{rel}: job `{name}` reaches a toolchain without going "
                    f"through make, and never runs {' or '.join(provides)}. The "
                    f"dependency the make graph declares does not reach a step "
                    f"that bypasses make"
                )
            elif generated_at > at:
                report.fail(
                    f"{rel}: job `{name}` generates the source AFTER compiling it "
                    f"-- a containment check passes on this and the build still "
                    f"fails, which is why the order is what is read here"
                )

    report.coverage(
        covered=sorted(set(covered)),
        excluded=[
            "whether the generated source is right (ci/gates/provenance.py, ci/provenance-check.py)",
            "a toolchain reached through a variable, a script or an alias",
            "make-routed steps, whose dependency the make graph already carries",
        ],
        kind="compiling site",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  compiling sites held to `{target}`: {len(set(covered))}")
    return report.finish(report_only=report_only)


main_guard(run)
