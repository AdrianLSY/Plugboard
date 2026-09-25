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

Exit status is non-zero if and only if a BLOCKING gate failed, or the run
exceeded its budget. `--report-only` forces every gate into report-only and
always exits zero.

## The budget, and how the run fits inside it (D32)

`make check` is the command run on every commit, and slow feedback changes what
gets written, so it carries a ceiling of the fast tier's shape: declared in
ci/vault.json as gate_policy.budget_seconds rather than written here, the
elapsed time printed on EVERY run, and a run over it failing with the remedy.
Raising the number is a change to D32, not a tuning step.

It fits for two reasons, both about not doing work twice or in series:

  * Gates are independent processes, so they run concurrently.
  * ci/gates/coverage.py's subject is every gate's own output, and it used to
    produce that output by running every gate a second time -- 63 of the run's
    120 seconds. It runs LAST, and reads the outputs this runner captured from a
    fresh directory named in GATE_OUTPUTS. Run on its own it still runs each
    gate itself, so the gate does not depend on the runner to decide.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

#: The gate that reads every other gate's output. It runs after them.
READS_OUTPUTS = "coverage"


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
    deferred = {
        k: v for k, v in policy["report_only_until"].items() if not k.startswith("_")
    }

    modules = sorted(
        p.stem for p in (root / "ci" / "gates").glob("*.py") if is_gate(p.stem)
    )

    # A gate in neither list is unclassified: fail rather than guess, so adding a
    # gate forces a decision about whether it blocks.
    unclassified = [
        m
        for m in modules
        if gate_id_for(m) not in blocking and gate_id_for(m) not in deferred
    ]

    mode = "REPORT-ONLY (forced)" if force_report_only else f"phase {policy['phase']}"
    budget = policy["budget_seconds"]
    print(f"== vault gates | {len(modules)} gate(s) | {mode}\n")

    started = time.monotonic()
    captured = Path(tempfile.mkdtemp(prefix="gate-outputs-"))

    def run_one(module: str, env: dict | None = None) -> tuple:
        gid = gate_id_for(module)
        is_blocking = (gid in blocking) and not force_report_only
        args = [sys.executable, str(root / "ci" / "gates" / f"{module}.py")]
        if not is_blocking:
            args.append("--report-only")
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(root / "ci" / "gates"),
            env=env,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        (captured / f"{module}.out").write_text(out, encoding="utf-8")
        failed = "[FAIL]" in out
        warned = "[warn]" in out
        crashed = "Traceback" in out
        return (gid, is_blocking, proc.returncode, failed, warned, crashed, out)

    try:
        first = [m for m in modules if m != READS_OUTPUTS]
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
            by_module = dict(zip(first, pool.map(run_one, first)))
        if READS_OUTPUTS in modules:
            by_module[READS_OUTPUTS] = run_one(
                READS_OUTPUTS, env={**os.environ, "GATE_OUTPUTS": str(captured)}
            )
    finally:
        shutil.rmtree(captured, ignore_errors=True)
    elapsed = time.monotonic() - started
    results = [by_module[m] for m in modules]

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
        note = (
            ""
            if is_blocking or force_report_only
            else f"  (blocks at {deferred.get(gid, '?')})"
        )
        print(f"   {gid:<{width}}  {policy_label:<11}  {state:<5}  exit={code}{note}")

    print("\n-- output")
    for _gid, _b, _c, _f, _w, _cr, out in results:
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
    over = elapsed > budget
    print(f"   elapsed        : {elapsed:.1f}s against a {budget}s budget")
    if over:
        print(
            f"   OVER BUDGET by {elapsed - budget:.1f}s. make check is the command run "
            f"on every commit, and its latency is a defect class, not a target. D32 "
            f"names the remedy: move ci/gates/meta.py's isolation cross-product to "
            f".github/workflows/scheduled.yml with a cheaper isolation property kept "
            f"on change, or remove the cost that grew. Raising the budget is a "
            f"change to D32, not a tuning step."
        )

    if force_report_only:
        print("\n   report-only: exiting 0 regardless of findings")
        return 0
    if unclassified or crashes or hard or over:
        return 1
    print("\n   all blocking gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
