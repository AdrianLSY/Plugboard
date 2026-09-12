#!/usr/bin/env python3
"""Run a command, report how long it took, and fail it over the declared budget.

Serves docs/code/rules/fast-tier-latency-budget.md -- the fast tier's wall-clock
ceiling, read from ci/vault.json rather than written here so the number the rule
states and the number enforced cannot be two numbers.

This is a correctness control and not a convenience. The audit's completeness
critic put it best, and it is the reason the ceiling is enforced rather than
hoped for:

    When feedback is slow, an agent (or a person) writes assertions that are
    cheap to satisfy rather than assertions that are expensive to satisfy.

So the elapsed time is printed on EVERY run, passing included. A budget nobody
sees until it is breached gives no warning as the suite creeps toward it, and the
creep is the part that changes what gets written.

The remedy for a breach is stated in the rule and refused here: move the test to
its tier, or fix the architecture that made it slow. Never raise the ceiling, and
never delete coverage to fit under it.

Usage:
    python3 ci/fast-tier.py -- <command> [args...]
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "ci" / "vault.json").is_file():
            return candidate
    raise SystemExit("could not locate ci/vault.json")


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "--" or len(argv) < 2:
        raise SystemExit("usage: python3 ci/fast-tier.py -- <command> [args...]")
    command = argv[1:]
    root = repo_root()
    cfg = json.loads((root / "ci" / "vault.json").read_text(encoding="utf-8"))
    budget = cfg["code_standards"]["test_tiers"]["fast_budget_seconds"]

    started = time.monotonic()
    code = subprocess.run(command, cwd=str(root)).returncode
    elapsed = time.monotonic() - started

    print(f"\nfast tier: {elapsed:.1f}s against a {budget}s budget", file=sys.stderr)
    if code != 0:
        print("fast tier: the suite failed; the budget is not the finding here", file=sys.stderr)
        return code
    if elapsed > budget:
        print(
            f"fast tier: OVER BUDGET by {elapsed - budget:.1f}s. Suite latency is a "
            f"defect class, not a target -- move the slow test to its tier "
            f"(docs/code/rules/test-tiers.md) or fix the architecture that made it "
            f"slow. Raising the ceiling and deleting coverage are both refused: "
            f"docs/code/rules/fast-tier-latency-budget.md",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
