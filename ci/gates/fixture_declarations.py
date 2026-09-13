#!/usr/bin/env python3
"""Gate: a violating input states the failure it produces.

Enforces docs/code-standards -- "A violating input states the failure it
produces".

ci/gates/meta.py proves each gate FAILS on its own violating input. It does not
read what the fixture claims that failure is, and eleven GATE.md files stated a
violation count in prose. Four of them were wrong: citations said three and
emitted four, currency said four and emitted three, index-drift said four and
emitted six, rule-gate-correspondence said seven and emitted eight. Two of those
four were not wrong numbers but defects the numbers hid -- currency's fourth
case had stopped firing entirely, so the property that gate exists for was
undemonstrated while its fixture still failed on the other three.

So the declaration is machine-readable and beside the tree, and prose in the
accompanying note is explicitly NOT read as it.

Five cases, all five failing:

  1. A tree with no declaration at all.
  2. A declared count that disagrees with the emitted count, naming both.
  3. A declared case that matches no emitted failure line.
  4. A declared invocation whose exit status differs from the one it claims.
  5. A flag the gate's own argument handling accepts, shown in the accompanying
     note and absent from the declaration. `--self-test` was exactly that for
     two years of this repository's short life: documented as a second violating
     input, never performed.

## The unit is the tree, not the directory

More trees live under ci/broken-inputs than directories -- reachability carries
two scenarios -- and ci/gates/
meta.py already iterates `tree*`. A declaration keyed on the directory cannot
state what each scenario emits.

## An invocation declares an exit status, never a count

A count belongs to a tree. `--self-test` builds its own scenario in a temporary
repository, so the only thing an outside observer can asssert about it is how it
exited.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "fixture-declarations"
RULE_NOTE = "docs/method/rules/fixtures-declare-their-failure.md"

FAIL_COUNT = re.compile(r"\[FAIL\] [a-z-]+: (\d+) violation")
FLAG = re.compile(r"`?(--[a-z][a-z-]+)`?")
NOT_A_GATE = {"a module whose name starts with _ (a shared library)"}


def run_module(module: Path, args: list[str]) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, str(module), *args], capture_output=True, text=True
    )
    return done.returncode, done.stdout + done.stderr


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    fixtures = scan_root / "ci" / "broken-inputs"
    report = Report(GATE_ID, RULE_NOTE)

    if not fixtures.is_dir():
        report.fail(
            f"ci/broken-inputs/ is absent -- this gate's subject is the set of "
            f"violating trees, and there are none"
        )
        report.coverage(covered=[], excluded=[], kind="violating tree",
                        source="scan", scan_root=scan_root)
        return report.finish(report_only=report_only)

    read, skipped = [], []
    for d in sorted(p for p in fixtures.iterdir() if p.is_dir()):
        gid = d.name
        module = scan_root / "ci" / "gates" / (gid.replace("-", "_") + ".py")
        if not module.is_file() or module.stem.startswith("_"):
            # A directory pairing to a SCRIPT rather than a gate module, declared
            # in ci/vault.json gate_policy.script_paired_inputs. It is skipped
            # here and must therefore be reported as EXCLUDED: naming it among
            # the covered set was this gate's own coverage line asserting a reach
            # the run did not have, which is the defect
            # docs/method/rules/coverage-is-an-assertion.md exists for.
            skipped.append(gid)
            continue
        read.append(gid)
        decl_path = d / "expect.json"
        trees = sorted(p for p in d.glob("tree*") if p.is_dir())

        # (1) a tree with no declaration.
        if not decl_path.is_file():
            for tree in trees:
                report.examine(f"{gid}/{tree.name}")
            report.fail(
                f"ci/broken-inputs/{gid}/: {len(trees)} violating tree(s) and no "
                f"expect.json -- what a fixture demonstrates is a declaration, not "
                f"a sentence in its note"
            )
            continue
        try:
            decl = json.loads(decl_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.fail(f"ci/broken-inputs/{gid}/expect.json: not valid JSON ({exc.msg})")
            continue
        declared_trees = {k: v for k, v in decl.get("trees", {}).items() if not k.startswith("_")}

        for tree in trees:
            subject = f"{gid}/{tree.name}"
            report.examine(subject)
            claim = declared_trees.get(tree.name)
            if claim is None:
                report.fail(
                    f"{subject}: the tree exists and expect.json declares nothing "
                    f"for it -- the unit is the tree, because one gate may need "
                    f"more than one scenario"
                )
                continue
            code, output = run_module(module, ["--root", str(tree)])
            m = FAIL_COUNT.search(output)
            emitted = int(m.group(1)) if m else 0

            # (2) the count.
            if claim.get("violations") != emitted:
                report.fail(
                    f"{subject}: declares {claim.get('violations')} violation(s) and "
                    f"its gate emits {emitted} -- a fixture drifting from the gate it "
                    f"demonstrates reads as still current"
                )
            # (3) each declared case matches at least one emitted failure.
            emitted_lines = [l.strip() for l in output.splitlines() if l.strip().startswith("- ")]
            for case in claim.get("cases", []):
                if not any(case in l for l in emitted_lines):
                    report.fail(
                        f"{subject}: declares a case its gate no longer emits "
                        f"({case[:70]!r}) -- either the case died or the gate did"
                    )

        # (4) declared invocations are performed.
        declared_flags = set()
        for inv in decl.get("invocations", []):
            args = inv.get("args", [])
            declared_flags.update(a for a in args if a.startswith("--"))
            if "violations" in inv:
                report.fail(
                    f"ci/broken-inputs/{gid}/expect.json: an invocation declares a "
                    f"violation count -- a count belongs to a tree; an invocation "
                    f"declares an exit status"
                )
            report.examine(f"{gid} {' '.join(args)}")
            code, _ = run_module(module, args)
            if code != inv.get("exit"):
                report.fail(
                    f"ci/broken-inputs/{gid}/: `{' '.join(args)}` exited {code}, "
                    f"declared {inv.get('exit')}"
                )

        # (5) a flag the note demonstrates and the declaration omits.
        note = d / "GATE.md"
        if note.is_file():
            shown = set(FLAG.findall(note.read_text(encoding="utf-8")))
            source = module.read_text(encoding="utf-8")
            for flag in sorted(shown - declared_flags - {"--root"}):
                if f'"{flag}"' in source:
                    report.fail(
                        f"ci/broken-inputs/{gid}/GATE.md: demonstrates `{flag}`, which "
                        f"the gate accepts, and expect.json declares no invocation "
                        f"using it -- a demonstration the repository documents and "
                        f"never performs"
                    )

    report.coverage(
        covered=sorted(read),
        excluded=sorted([*NOT_A_GATE, *(f"{g} (script-paired, not a gate module)" for g in skipped)]),
        kind="violating tree or declared invocation",
        source="scan",
        scan_root=scan_root,
    )
    return report.finish(report_only=report_only)


main_guard(run)
