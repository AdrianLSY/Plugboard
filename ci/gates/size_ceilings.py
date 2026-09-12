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

## Python is excluded, by declaration and with a measurement

The harness is Python, and four of its modules are over the ceiling today -- the
largest at 442 non-comment lines. Task 3.5 asks for "both languages", meaning the
two the components are written in, so Python is declared out of scope in
ci/vault.json with the reason and the work that ends it, and the count is printed
on every run rather than left for somebody to discover. An exclusion nobody can
see is an exemption.

## What it does not decide

Whether a long function should have been long. Some genuinely are: a decision
table is one expression per row. The ceiling is a forcing function on structure,
not a claim about any particular function, and the remedy is always to split
along a responsibility rather than to raise the number.
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
    excluded_langs = {k: v for k, v in cfg["excluded_languages"].items()
                      if not k.startswith("_")}
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
        excluded=[f"{ext} ({v['reason'][:48]}...)" for ext, v in excluded_langs.items()],
        kind="source file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  files: {len(files)} | ceilings: {module_max} per module, "
        f"{function_max} per clause | widest module seen: {widest}"
    )
    for ext, entry in sorted(excluded_langs.items()):
        print(f"  {ext} excluded: {entry['reason']}\n     ends with: {entry['ends_with']}")
    return report.finish(report_only=report_only)


main_guard(run)
