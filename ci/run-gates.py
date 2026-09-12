#!/usr/bin/env python3
"""The aggregating target: run every vault gate and enumerate what ran.

tasks.md 1.11 -- one target that runs every gate with a report-only mode, and
records which gates are blocking at which point in the task list.

Three properties matter, and each has a reason:

  * IT ENUMERATES EVERY GATE IT RAN. The change's own risk register carried the
    figure "seven new gates" while the task list introduced roughly thirty. A
    prose count drifts; a build output cannot. So the inventory is printed here
    and the roster is discovered from the filesystem -- ci/gates/*.py against
    ci/broken-inputs/<gate-id>/ -- rather than declared in a list that would
    become the same kind of stale claim.

  * BLOCKING IS PER-GATE AND RECORDED, NOT GLOBAL. A gate that cannot pass on
    the tree it governs is not a gate, so a gate lands in report-only and is
    flipped by the task that makes the tree satisfy it. ci/vault.json's
    gate_policy holds which are blocking now and which task flips each of the
    rest, so the flip is a decision rather than something discovered during
    application.

  * A REPORT-ONLY GATE'S FAILURES ARE STILL PRINTED. Suppressing the output
    would make the report-only phase indistinguishable from a passing one, and
    the whole point of the phase is to watch the count go to zero as the content
    lands.

Exit status is non-zero if and only if a BLOCKING gate failed. `--report-only`
forces every gate into report-only and always exits zero.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

#: A module whose name starts with `_` is a shared library, not a gate. This
#: was six hardcoded copies of {"_common"} until ci/gates/_source.py arrived
#: and made every one of them wrong in the same commit.
def is_gate(stem: str) -> bool:
    return not stem.startswith("_")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "ci" / "vault.json").is_file():
            return candidate
    raise SystemExit("could not locate ci/vault.json")


def gate_id_for(module: str) -> str:
    return module.replace("_", "-")


def main(argv: list[str]) -> int:
    force_report_only = "--report-only" in argv
    unknown = [a for a in argv if a not in {"--report-only"}]
    if unknown:
        raise SystemExit(f"unknown argument(s): {', '.join(unknown)}")

    root = repo_root()
    manifest = json.loads((root / "ci" / "vault.json").read_text(encoding="utf-8"))
    policy = manifest["gate_policy"]
    blocking = set(policy["blocking"])
    deferred = {k: v for k, v in policy["report_only_until"].items() if not k.startswith("_")}

    modules = sorted(
        p.stem for p in (root / "ci" / "gates").glob("*.py") if is_gate(p.stem)
    )

    # A gate in neither list is unclassified: fail rather than guess, so adding a
    # gate forces a decision about whether it blocks.
    unclassified = [
        m for m in modules if gate_id_for(m) not in blocking and gate_id_for(m) not in deferred
    ]

    mode = "REPORT-ONLY (forced)" if force_report_only else f"phase {policy['phase']}"
    print(f"== vault gates | {len(modules)} gate(s) | {mode}\n")

    results = []
    for module in modules:
        gid = gate_id_for(module)
        is_blocking = (gid in blocking) and not force_report_only
        args = [sys.executable, str(root / "ci" / "gates" / f"{module}.py")]
        if not is_blocking:
            args.append("--report-only")
        proc = subprocess.run(args, capture_output=True, text=True, cwd=str(root / "ci" / "gates"))
        out = (proc.stdout or "") + (proc.stderr or "")
        failed = "[FAIL]" in out
        warned = "[warn]" in out
        crashed = "Traceback" in out
        results.append((gid, is_blocking, proc.returncode, failed, warned, crashed, out))

    width = max(len(g) for g, *_ in results)
    print("-- inventory")
    for gid, is_blocking, code, failed, warned, crashed, _out in results:
        if crashed:
            state = "CRASH"
        elif failed:
            state = "FAIL"
        elif warned:
            state = "warn"
        else:
            state = "ok"
        policy_label = "blocking" if is_blocking else "report-only"
        note = "" if is_blocking or force_report_only else f"  (blocks at {deferred.get(gid, '?')})"
        print(f"   {gid:<{width}}  {policy_label:<11}  {state:<5}  exit={code}{note}")

    print("\n-- output")
    for gid, _b, _c, _f, _w, _cr, out in results:
        for line in out.rstrip("\n").splitlines():
            print(f"   {line}")
        print()

    hard = [g for g, b, c, _f, _w, _cr, _o in results if b and c != 0]
    crashes = [g for g, _b, _c, _f, _w, cr, _o in results if cr]
    warns = [g for g, b, _c, _f, w, _cr, _o in results if w and not b]

    print("-- summary")
    print(f"   gates run      : {len(results)}")
    print(f"   blocking       : {sum(1 for _g, b, *_ in results if b)}")
    print(f"   report-only    : {sum(1 for _g, b, *_ in results if not b)}")
    if warns:
        print(f"   warning (expected, not yet blocking): {', '.join(warns)}")
    if crashes:
        print(f"   CRASHED        : {', '.join(crashes)}")
    if unclassified:
        print(
            f"   UNCLASSIFIED   : {', '.join(unclassified)} -- add each to "
            f"gate_policy.blocking or gate_policy.report_only_until in ci/vault.json"
        )
    if hard:
        print(f"   FAILED         : {', '.join(hard)}")

    if force_report_only:
        print("\n   report-only: exiting 0 regardless of findings")
        return 0
    if unclassified or crashes or hard:
        return 1
    print("\n   all blocking gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
