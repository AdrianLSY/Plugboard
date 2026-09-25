#!/usr/bin/env python3
"""Gate: a module and a function each stay under a declared ceiling.

Enforces docs/code/rules/module-size-ceiling.md (300 non-comment lines per file)
and docs/code/rules/function-size-ceiling.md (60 per clause), for every declared
source language. rebuild-plugboard task 3.5.

Comments do not count toward either. That is the half that matters: a file
counted by raw lines is padded with comments to move the number, and what the
rule asks for is the file split along whatever made it long.

Functions are measured per CLAUSE rather than per name, so a function with many
clauses is measured clause by clause and a template rendered inline is measured
with the function it sits in. The prior art's 813-line `render/1` is the case
being made unwritable, and its 1,380-line LiveView handling four unrelated
resources is the other one.

## Python is excluded by declaration, and measured on every run

The harness is Python, and some of its modules are over the module ceiling.
Task 3.5 asks for "both languages", meaning the two the components are written
in, so Python is declared out of scope in ci/vault.json with the reason and the
work that ends it. An exclusion nobody can see is an exemption, so each excluded
language is measured anyway: the files the gate would read if that language were
declared -- the same tracked set, the same scan exclusions, the same counter --
and the run prints how many are over the module ceiling and names each with its
count. The list printed is the list that would fail the day the language moves
into `languages`.

The count is measured rather than written down because a written one goes stale
the next time a module grows. The figure this replaced, in the declaration and
here, named four modules when a review found eight over, and every count it gave
had grown since it was written.

## What it does not decide

Whether a long function should have been long. Some genuinely are: a decision
table is one expression per row. The ceiling is a forcing function on structure,
not a claim about any particular function, and the remedy is always to split
along a responsibility rather than to raise the number.

Whether an exclusion has outlived its reason. The measurement is printed and
never fails: a count of zero fails nothing, and the declaration stays until the
change recorded in docs/method/follow-ups.md removes it. Nor does the
measurement count clauses: `clauses()` splits Go and Elixir only, so moving
Python in would bring the module ceiling and not the function one, and the
module ceiling is all an excluded language is measured against.
"""

from __future__ import annotations

from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, subject_source
from _source import COMMENT, clauses, code_lines, config, languages, sources

GATE_ID = "size-ceilings"
RULE_NOTE = "docs/code/rules/module-size-ceiling.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = config(manifest)
    module_max = cfg["module_lines"]
    function_max = cfg["function_lines"]
    excluded_langs = {
        k: v for k, v in cfg["excluded_languages"].items() if not k.startswith("_")
    }
    report = Report(GATE_ID, RULE_NOTE)

    files = sources(scan_root, cfg, manifest)
    widest = 0
    for rel in files:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        text = path.read_text(encoding="utf-8", errors="replace")
        comment = COMMENT.get("." + rel.rsplit(".", 1)[-1], "#")
        count = len(code_lines(text, comment))
        widest = max(widest, count)
        if count > module_max:
            report.fail(
                f"{rel}: {count} non-comment lines, ceiling {module_max} -- split "
                f"it along the responsibilities that made it long. Padding it with "
                f"comments moves the count and not the problem"
            )
        for name, line, body in clauses(rel, text):
            if body > function_max:
                report.fail(
                    f"{rel}:{line}: `{name}` is {body} non-comment lines, ceiling "
                    f"{function_max} -- measured per clause, so a clause is what "
                    f"gets split"
                )

    report.coverage(
        covered=sorted(set(languages(cfg).values())),
        excluded=[
            f"{ext} ({v['reason'][:48]}...)" for ext, v in excluded_langs.items()
        ],
        kind="source file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  files: {len(files)} | ceilings: {module_max} per module, "
        f"{function_max} per clause | widest module seen: {widest}"
    )
    for ext, entry in sorted(excluded_langs.items()):
        measured, over = over_ceiling(scan_root, cfg, manifest, ext, module_max)
        # Printed, never failed, and never prefixed "- ": ci/gates/coverage.py and
        # ci/gates/fixture_declarations.py read a "- " line as a failure naming a
        # subject, and an excluded file is not one of this run's subjects.
        print(
            f"  {ext} excluded: {entry['reason']}\n"
            f"     measured anyway: {len(over)} of {measured} {ext} file(s) over "
            f"{module_max} non-comment lines"
        )
        for rel, count in over:
            print(f"       {rel} {count}")
        print(f"     ends with: {entry['ends_with']}")
    return report.finish(report_only=report_only)


def over_ceiling(
    scan_root: Path, cfg: dict, manifest: dict, ext: str, module_max: int
) -> tuple[int, list[tuple[str, int]]]:
    """(files measured, [(path, count)] over the ceiling, largest first) for `ext`.

    The file set is `sources()` over the declared config with its language map
    narrowed to `ext`, not a second walk written here: what this prints has to be
    what moving `ext` into `languages` would fail, so it selects the way that
    move would -- tracked index, scan exclusions and all.
    """
    files = sources(scan_root, {**cfg, "languages": {ext: "excluded"}}, manifest)
    comment = COMMENT.get(ext, "#")
    over: list[tuple[str, int]] = []
    for rel in files:
        path = scan_root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        count = len(code_lines(text, comment))
        if count > module_max:
            over.append((rel, count))
    return len(files), sorted(over, key=lambda o: (-o[1], o[0]))


main_guard(run)
