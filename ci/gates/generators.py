#!/usr/bin/env python3
"""Gate: a generated artifact is verified against something other than its generator.

Enforces docs/code-standards -- "A generated artifact is verified against
something other than its generator".

ci/gates/index_drift.py verifies a generated file by re-running its generator
and byte-comparing. That is a sound check for a hand edit and no check at all
for a wrong generator: wrong output is produced consistently, so it verifies as
current. Replacing one expression in ci/gen/indexes.py relabelled every note in
the vault "Untitled note" across thirteen index files, and `make check` exited
zero.

So each generator is pinned to an oracle it cannot move: a small input tree, and
the exact output it is expected to produce on that tree, both tracked. The
comparison runs against a COPY of the input, so a generator that writes is still
exercised in write mode.

Four cases, all four failing:

  1. A generator whose output on its input differs from the pinned expectation,
     naming the generator, the expectation file and the first differing line.
  2. A tool under ci/gen/ that the declaration does not name.
  3. A declared tool that does not exist.
  4. A generator that does not state the class of wrongness its input fails to
     reach. A partial oracle is fine; a partial oracle presenting itself as
     total converts an unexamined case into an apparently examined one.

## Why the expectation is tracked rather than derived

An expectation computed at check time is the generator again. A tracked one was
authored once and read -- each fixture here is small enough to verify by eye,
which is the property that makes it an oracle rather than a snapshot. It catches
drift from verified behaviour, not from an independent derivation, and each
generator says so in its own module.
"""

from __future__ import annotations

import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "generators"
RULE_NOTE = "docs/method/rules/generators-have-an-oracle.md"

BLIND_SPOT = "does not reach"


def first_difference(want: Path, got: Path) -> str:
    a = want.read_text(encoding="utf-8").splitlines()
    b = got.read_text(encoding="utf-8").splitlines() if got.is_file() else []
    for n, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            return f"line {n}: expected {x!r}, got {y!r}"
    if len(a) != len(b):
        return f"line {min(len(a), len(b)) + 1}: expected {len(a)} line(s), got {len(b)}"
    return "no textual difference (permissions or encoding)"


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["generators"]
    declared = {k: v for k, v in cfg["tools"].items() if not k.startswith("_")}
    gen_dir = scan_root / cfg["dir"]
    report = Report(GATE_ID, RULE_NOTE)

    on_disk = {
        p.relative_to(scan_root).as_posix()
        for p in sorted(gen_dir.glob("*.py"))
    } if gen_dir.is_dir() else set()

    # (2) and (3): the declaration is complete in both directions.
    for rel in sorted(on_disk - set(declared)):
        report.fail(
            f"{rel}: a tool under {cfg['dir']}/ that ci/vault.json's generators "
            f"declaration does not name -- an undeclared generator is the one "
            f"nothing pins"
        )
    for rel in sorted(set(declared) - on_disk):
        report.fail(f"{rel}: declared as a generator and does not exist")

    for rel in sorted(set(declared) & on_disk):
        report.examine(rel)
        spec = declared[rel]
        tree, expected = scan_root / spec["input"], scan_root / spec["expected"]

        # (4) the blind spot is stated.
        if BLIND_SPOT not in (scan_root / rel).read_text(encoding="utf-8"):
            report.fail(
                f"{rel}: does not state the class of wrongness its violating input "
                f"does not reach -- a partial oracle that presents itself as total "
                f"turns an unexamined case into an apparently examined one"
            )
        if not tree.is_dir():
            report.fail(f"{rel}: declared input tree '{spec['input']}' is absent")
            continue
        if not expected.is_dir():
            report.fail(f"{rel}: declared expectation '{spec['expected']}' is absent")
            continue

        # (1) the pinned comparison, run against a copy so write mode is exercised.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "tree"
            shutil.copytree(tree, work)
            done = subprocess.run(
                [sys.executable, str(scan_root / rel), "--root", str(work), "--write"],
                capture_output=True, text=True, cwd=str(scan_root),
            )
            if done.returncode != 0:
                report.fail(
                    f"{rel}: exited {done.returncode} against its own declared input "
                    f"-- {(done.stderr or done.stdout).strip().splitlines()[-1:] or ['no output']}"
                )
                continue
            for want in sorted(p for p in expected.rglob("*") if p.is_file()):
                sub = want.relative_to(expected)
                got = work / sub
                if not got.is_file():
                    report.fail(
                        f"{rel}: produced no {sub} -- the pinned expectation "
                        f"{spec['expected']}/{sub} has no counterpart in the run"
                    )
                elif not filecmp.cmp(want, got, shallow=False):
                    report.fail(
                        f"{rel}: output differs from the pinned expectation "
                        f"{spec['expected']}/{sub} -- {first_difference(want, got)}"
                    )

    report.coverage(
        covered=sorted(declared),
        excluded=[cfg["fixture_dir"]],
        kind="generator",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  generators declared: {len(declared)} | on disk: {len(on_disk)} | "
          f"pinned expectations compared: {len(set(declared) & on_disk)}")
    return report.finish(report_only=report_only)


main_guard(run)
