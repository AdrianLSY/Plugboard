#!/usr/bin/env python3
"""Gate: a helper that waits never performs the transition it waits for.

Enforces docs/code/rules/no-helper-repairing-awaited-state.md. rebuild-plugboard
task 3.8: fails when a harness or test helper calls a reload, restart, resync or
reconcile entry point from a wait, poll or retry path, naming the file and line.

The defect, exactly: the prior attempt's wait helper called `MountStore.reload_all()`
on timeout and then reported success. 947 lines of tests for a cache-invalidation
mechanism passed while the mechanism had never run under test -- because the
helper performed by hand the thing it was waiting to observe, and a helper that
repairs what it waits for turns a failing assertion into a passing one.

Discarding the repair's return value is prohibited on the same footing, because
that is what makes it invisible at the call site.

## The decidable form

A file that is a test or a declared harness path, a function whose name or
enclosing block carries a waiting word, and a call to a repairing verb inside it.
Both vocabularies are declared in ci/vault.json rather than written here.

## What it does not decide

A repair spelled some other way -- `MountStore.recompute()`, or a private helper
that reloads without saying so. The vocabulary is the vocabulary; widening it to
every verb would fire on every test. The residue is
[checklist item 5](docs/code/reviewing.md#the-review-checklist) and review's.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, subject_source
from _source import COMMENT, code_lines, config, sources

GATE_ID = "no-repair"
RULE_NOTE = "docs/code/rules/no-helper-repairing-awaited-state.md"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = config(manifest)
    guard = manifest["code_standards"]["no_repair"]
    waiting = [w for w in guard["waiting_words"] if not w.startswith("_")]
    repairing = [w for w in guard["repairing_words"] if not w.startswith("_")]
    harness_paths = [p for p in guard["harness_paths"] if not p.startswith("_")]
    report = Report(GATE_ID, RULE_NOTE)

    wait_re = re.compile("|".join(re.escape(w) for w in waiting), re.I)
    repair_re = re.compile(
        r"\b(" + "|".join(re.escape(w) for w in repairing) + r")\w*\s*\(", re.I)

    files = [
        rel for rel in sources(scan_root, cfg, manifest)
        if "_test." in rel or any(rel.startswith(p) for p in harness_paths)
    ]
    for rel in files:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        comment = COMMENT.get("." + rel.rsplit(".", 1)[-1], "#")
        lines = code_lines(path.read_text(encoding="utf-8", errors="replace"), comment)
        in_wait = False
        for n, text in lines:
            if wait_re.search(text):
                in_wait = True
            if not in_wait:
                continue
            m = repair_re.search(text)
            if not m:
                continue
            report.fail(
                f"{rel}:{n}: `{m.group(1)}` called from a waiting path -- a helper "
                f"waits, observes and FAILS. The prior attempt's wait helper called "
                f"reload_all() on timeout and reported success, so 947 lines of "
                f"tests passed over a mechanism that had never run"
            )

    report.coverage(
        covered=["tests", *harness_paths],
        excluded=["a repair spelled outside the declared vocabulary (review's)"],
        kind="test or harness file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  files: {len(files)} | waiting words: {len(waiting)} | repairing verbs: "
        f"{len(repairing)}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
