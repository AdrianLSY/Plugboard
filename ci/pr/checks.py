#!/usr/bin/env python3
"""Checks whose subject is a PULL REQUEST rather than the tree.

`make check` runs the vault gates, and every one of them decides a property of a
directory. These cannot: they read the pull-request body or the set of paths a
change touched. These subjects do not exist outside a forge, so the checks are not
vault gates and ci/gates/meta.py does not cover them.

That leaves the demonstration obligation unmet unless something else meets it, so
each check carries RECORDED CASES under ci/pr/cases/ -- a body, a path set, and
the verdict expected -- and `--self-test` runs every one and fails if any verdict
disagrees. The workflow runs `--self-test` before it runs the checks, so a check
that has stopped deciding fails the pull request that revealed it rather than
passing quietly. It is the same property ci/gates/meta.py asserts, by the only
means available to a check with no tree.

  description            A human-authored PR says what changed and why. A heading
                         or the template's unfilled prompt is not an answer.

  wire-contract-impact   rebuild-plugboard task 1.5. The body declares the
                         change's effect on the wire schema -- none, additive, or
                         breaking -- by ticking exactly one box. An unticked
                         section is not "none": it is nobody having answered, and
                         the schema is the one artifact no later release can
                         correct.

  docs-touched           rebuild-plugboard task 1.10. A change touching a
                         component root either touches the spine or says
                         `docs: n/a` with a reason. Keyed on ci/vault.json's
                         declared component set and declared spine, never on a
                         path list of its own -- the task asks for exactly that,
                         and a second list would drift from the first.

## What these checks do not decide

Whether the description explains the change well, the box ticked is the RIGHT
one, or the `docs: n/a` reason is a good one. docs/method/documentation-rules.md
states the last explicitly: CI checks for the marker's presence, the reviewer
checks its correctness. Saying so
here because a check whose limits are undocumented gets read as a guarantee.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = HERE / "cases"

TICKED = re.compile(r"^\s*[-*]\s*\[[xX]\]", re.M)
IMPACT_HEADING = re.compile(r"^#+\s*wire contract impact\s*$", re.I | re.M)
DESCRIPTION_HEADING = re.compile(r"^#+\s*description\s*$", re.I | re.M)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
# `docs: n/a` followed by a reason on the same line. The marker convention is
# stated in docs/method/documentation-rules.md and is not restated here: this is
# the regex that recognises it, which is a different artifact from the rule.
MARKER = re.compile(r"docs:\s*n/?a\b[\s—:,-]*(?P<reason>.*)", re.I)
MIN_REASON = 12
TEMPLATE = ".github/pull_request_template.md"


def template_lines() -> set[str]:
    """The template's own lines, which are a PROMPT and never an answer.

    The template carries `- [ ] Docs updated, or "docs: n/a" with a reason`. That
    line contains the marker, and the words after it clear the reason floor, so a
    body left exactly as the forge served it satisfied this check while touching
    contract/ -- the precise shape of green-over-nothing this repository exists to
    make unwritable. It was caught by adding a recorded case, not by reading the
    regex, which is the whole argument for the cases.
    """
    path = ROOT / TEMPLATE
    if not path.is_file():
        return set()
    return {
        l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()
    }


def manifest() -> dict:
    return json.loads((ROOT / "ci" / "vault.json").read_text(encoding="utf-8"))


def _section(body: str, heading_re: re.Pattern[str]) -> str | None:
    """The first matching heading's content, ignoring headings inside code fences."""
    found = False
    fence: str | None = None
    out: list[str] = []
    for line in body.splitlines():
        marker = FENCE.match(line)
        if marker:
            run, suffix = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not suffix.strip():
                fence = None
        elif fence is None:
            if not found:
                if heading_re.match(line):
                    found = True
                continue
            if line.startswith("#"):
                break
        if found:
            out.append(line)
    return "\n".join(out) if found else None


def description(body: str, changed: list[str], _mf: dict) -> str | None:
    """Require an actual summary under Description, not the template prompt."""
    section = _section(body, DESCRIPTION_HEADING)
    if section is None:
        return "the change description has no 'Description' section"
    if not re.search(r"\w", HTML_COMMENT.sub("", section)):
        return "the 'Description' section is empty; summarize what changed and why"
    return None


def wire_contract_impact(body: str, changed: list[str], _mf: dict) -> str | None:
    """None when satisfied, otherwise the refusal."""
    section = _section(body, IMPACT_HEADING)
    if section is None:
        return (
            "the change description has no 'Wire contract impact' section -- it is "
            "in the template the forge serves, and deleting it is not an answer. "
            "The wire schema is the one artifact no later release can correct."
        )
    if not TICKED.search(section):
        return (
            "no box is ticked under 'Wire contract impact'. An unticked section is "
            "not 'none' -- it is nobody having answered. Tick None, Additive, or "
            "BREAKING; BREAKING needs a version bump and a capability flag."
        )
    return None


def docs_touched(body: str, changed: list[str], mf: dict) -> str | None:
    spine = mf["spine"]
    components = [
        c
        for c in mf["code_standards"]["components"]["candidates"]
        if not c.startswith("_")
    ]
    triggering = sorted(
        p for p in changed if any(p == c or p.startswith(c + "/") for c in components)
    )
    if not triggering:
        return None
    if any(p == spine or p.startswith(spine + "/") for p in changed):
        return None
    prompts = template_lines()
    m = next(
        (
            found
            for line in body.splitlines()
            if line.strip() not in prompts
            for found in [MARKER.search(line)]
            if found
        ),
        None,
    )
    if m and len(m.group("reason").strip()) >= MIN_REASON:
        return None
    if m:
        return (
            f"carries a `docs: n/a` marker with no reason, and touches "
            f"{', '.join(triggering[:4])}. The marker is the place the reason goes; "
            f"a bare marker is the box-ticking the rule exists to refuse."
        )
    return (
        f"touches {', '.join(triggering[:4])} and neither touches {spine}/ nor says "
        f"`docs: n/a` with a reason. Documentation lands in the same change as the "
        f"behaviour, or the omission is stated -- see docs/method/documentation-rules.md."
    )


CHECKS = {
    "description": description,
    "wire-contract-impact": wire_contract_impact,
    "docs-touched": docs_touched,
}


def changed_paths(base: str, head: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--name-only", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [p for p in out.splitlines() if p]


def self_test() -> int:
    mf = manifest()
    cases = sorted(CASES.glob("*.json"))
    if not cases:
        print(
            "self-test: no recorded cases -- a check with no demonstration is untested"
        )
        return 1
    failures = 0
    for path in cases:
        case = json.loads(path.read_text(encoding="utf-8"))
        check = CHECKS[case["check"]]
        verdict = check(case.get("body", ""), case.get("changed", []), mf)
        got = "fail" if verdict else "pass"
        ok = got == case["expect"]
        failures += 0 if ok else 1
        mark = "ok  " if ok else "WRONG"
        print(
            f"  [{mark}] {path.name}: {case['check']} expected {case['expect']}, got {got}"
        )
        if not ok and verdict:
            print(f"          {verdict}")
    print(
        f"self-test: {len(cases)} recorded case(s), {failures} disagreeing "
        f"({len(CHECKS)} checks)"
    )
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    description = __doc__ or "Check a pull request description"
    ap = argparse.ArgumentParser(description=description.splitlines()[0])
    ap.add_argument(
        "--self-test",
        action="store_true",
        help="run every recorded case and fail on any disagreement",
    )
    ap.add_argument("--check", choices=sorted(CHECKS))
    ap.add_argument("--body", type=Path, help="file holding the pull-request body")
    ap.add_argument("--base", help="base ref, for the changed-path set")
    ap.add_argument("--head", default="HEAD", help="head ref, for the changed-path set")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.check:
        ap.error("one of --self-test or --check is required")

    body = args.body.read_text(encoding="utf-8") if args.body else sys.stdin.read()
    changed = changed_paths(args.base, args.head) if args.base else []
    verdict = CHECKS[args.check](body, changed, manifest())
    if verdict:
        print(f"[FAIL] {args.check}: {verdict}")
        return 1
    print(f"[ok] {args.check}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
