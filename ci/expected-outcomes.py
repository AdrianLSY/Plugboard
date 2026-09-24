#!/usr/bin/env python3
"""Run every gating test and hold its outcome to the one recorded.

Serves rebuild-plugboard task 4.5. The gating tests are written before the code
they gate, so they are RED on purpose -- and a permanently red test inside an
ordinary tier makes every later change unmergeable under branch protection. So
they run here instead, against a recorded baseline, and the check fails when an
outcome differs IN EITHER DIRECTION:

  * red where green was recorded  -- a regression, the ordinary case;
  * green where red was recorded  -- a gate that closed and a registry that did
    not say so. Which is the direction nobody builds a check for, and the one
    that matters here: the whole value of a recorded red is that turning green is
    an event somebody has to acknowledge.

Advancing an entry to green therefore only passes in the same change that turns
the test green. Editing the registry alone fails.

Usage:
    python3 ci/expected-outcomes.py            # run them all
    python3 ci/expected-outcomes.py --list     # print the registry, run nothing
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BUILD_TAG = "gating"


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "ci" / "vault.json").is_file():
            return candidate
    raise SystemExit("could not locate ci/vault.json")


def registry(root: Path) -> dict:
    path = root / "ci" / "expected-outcomes.json"
    return json.loads(path.read_text(encoding="utf-8"))


def module_root(root: Path, pkg: str) -> Path:
    """The go.mod directory above pkg."""
    here = root / pkg
    for candidate in [here, *here.parents]:
        if (candidate / "go.mod").is_file():
            return candidate
    raise SystemExit(f"{pkg}: no go.mod above it, so it is not in a module")


def run_one(root: Path, key: str) -> tuple[str, str]:
    """(outcome, output) for one `<pkg>:<TestName>` key."""
    pkg, _, name = key.partition(":")
    mod = module_root(root, pkg)
    rel = "./" + (root / pkg).relative_to(mod).as_posix()
    done = subprocess.run(
        ["go", "test", "-count=1", f"-tags={BUILD_TAG}", "-run", f"^{name}$", rel],
        cwd=str(mod),
        capture_output=True,
        text=True,
    )
    return ("green" if done.returncode == 0 else "red"), done.stdout + done.stderr


def main(argv: list[str]) -> int:
    root = repo_root()
    entries = {
        k: v for k, v in registry(root)["gates"].items() if not k.startswith("_")
    }

    if "--list" in argv:
        for key, entry in sorted(entries.items()):
            print(f"  {entry['outcome']:<5} {key}")
            print(f"        closed by: {entry.get('closed_by', '-')}")
        return 0

    failures = []
    for key, entry in sorted(entries.items()):
        recorded = entry["outcome"]
        actual, output = run_one(root, key)
        mark = "ok  " if actual == recorded else "DIFF"
        print(f"  [{mark}] {key}: recorded {recorded}, ran {actual}")
        if actual == recorded:
            continue
        if actual == "green":
            failures.append(
                f"{key}: recorded RED and ran GREEN. The gate closed -- advance it to "
                f"green in ci/expected-outcomes.json in this same change, and say so. "
                f"A gate that closes unannounced is a debt nobody collected."
            )
        else:
            failures.append(
                f"{key}: recorded GREEN and ran RED. This is a regression, and the "
                f"output was:\n{output.strip()[:2000]}"
            )

    print(
        f"\ngating tests: {len(entries)} | differing from the record: {len(failures)}"
    )
    for message in failures:
        print(f"  - {message}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
