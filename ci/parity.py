#!/usr/bin/env python3
"""The dual-invocation parity check: both invocations, run, against one broken input.

rebuild-plugboard task 3.11. Run it directly:

    python3 ci/parity.py                 # every declared obligation
    python3 ci/parity.py --only go-lint  # one of them
    python3 ci/parity.py --list          # what would run, and with which argv

## What this decides, and why it is a second program

ci/gates/parity.py compares the two invocations of an obligation as TEXT: it
reads the local argv out of the makefiles and the CI argv out of the workflow,
normalises both, and refuses when they differ. That catches a flag that drifted
on one side. It cannot catch a flag that is wrong on BOTH sides, because a wrong
flag spelled the same way twice is not a difference.

That second case is the one that cost the reference project months. `mix compile
--warning-as-errors` is singular; `mix` accepts the switch, ignores it, and
exits zero over a module full of warnings. Nothing about the text says so. The
only thing that says so is running it against a module with a warning in it and
watching what it does.

So this program executes. For every obligation declaring a broken input, it
stages that input into a scratch directory, runs the LOCAL invocation and the CI
invocation against it, and requires both to exit non-zero. Three outcomes:

    PARITY      both invocations rejected the input.
    DIVERGENCE  one rejected it and the other did not -- which one is named.
                This is `--warning-as-errors` exactly.
    INERT       neither rejected it. The two invocations agree, and they agree
                on doing nothing. A text comparison reports this as a pass.

## Refusing rather than skipping

An obligation whose tool is not on PATH is REPORTED AND REFUSED, never skipped.
A run that quietly covered three obligations instead of five reads exactly like
one that covered five, which is the reporting failure this whole check is about
-- and it is the same reason ci/make/elixir.mk refuses when `mix` is absent.

## What it does NOT decide

Whether the broken input is the right broken input. This program asserts that
both invocations refuse one specific thing; it cannot assert that they refuse
everything they ought to. A weakened input -- one the tool rejects for a reason
that has nothing to do with the obligation -- passes here and is review's to
catch, which is why each input is a minimal project holding exactly one defect.

WHY an invocation exited non-zero. A tool that refuses an unknown flag, or dies
on a missing file, is counted here as a rejection: the exit status is all this
program reads. A flag that drifted on ONE side is therefore ci/gates/parity.py's
to catch, from the text, on every change -- the two halves of this check cover
each other's blind spot and neither is sufficient alone.

It does not decide that an obligation is enforced in both places at all. That is
ci/gates/parity.py's, from the declaration, on every change.

It does not time anything, and it does not run `make check`: the aggregating
target is the 86-second command a contributor runs on every commit, and nesting
it here would mean the recurring runner re-runs every gate to learn nothing this
program decides.
"""

from __future__ import annotations

import json
import posixpath
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ci" / "gates"))

from parity import _ci_argvs, _local_argv, normalise, render  # noqa: E402

VERDICTS = {"parity": "PARITY", "divergence": "DIVERGENCE", "inert": "INERT"}

# `--list` runs nothing, so an obligation that HAS a broken input is not one
# "declared without" a broken input -- it is one this invocation did not execute.
# Collapsing the two made the listing report `declared without one: 5` over a set
# in which three inputs exist, and then sign off `[ok] parity: every executed
# obligation was rejected by both of its invocations` over zero executions. A
# verdict printed after running nothing is the one shape this check exists to
# refuse, so the listing gets its own verdict and its own closing line.
LISTED = "listed"


def absolutise(argv: list[str], workdir: str, norm: dict) -> list[str]:
    """A path argument is written relative to the directory its site runs in. The
    staged input is somewhere else, so those become absolute before the run --
    otherwise the invocation would fail for the wrong reason and be counted as a
    rejection."""
    path_flags = set(norm.get("path_flags", []))
    value_flags = set(norm.get("value_flags", []))
    out: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in path_flags and i + 1 < len(argv):
            rel = posixpath.normpath(posixpath.join(workdir or ".", argv[i + 1]))
            out += [token, str(ROOT / rel)]
            i += 2
            continue
        if "=" in token and token.split("=", 1)[0] in path_flags:
            name, value = token.split("=", 1)
            rel = posixpath.normpath(posixpath.join(workdir or ".", value))
            out.append(f"{name}={ROOT / rel}")
            i += 1
            continue
        if token in value_flags and i + 1 < len(argv):
            out += [token, argv[i + 1]]
            i += 2
            continue
        out.append(token)
        i += 1
    return out


def run_against(argv: list[str], staged: Path) -> tuple[int | None, str]:
    if shutil.which(argv[0]) is None:
        return None, f"{argv[0]} is not on PATH"
    done = subprocess.run(argv, cwd=str(staged), capture_output=True, text=True)
    tail = (done.stdout + done.stderr).strip().splitlines()
    return done.returncode, tail[-1] if tail else ""


def check(name: str, spec: dict, cfg: dict, listing: bool) -> tuple[str, list[str]]:
    """(verdict, lines). verdict is a key of VERDICTS, or 'refused' / 'declared'."""
    norm = cfg.get("normalisation", {})
    tool = spec["tool"].split()
    tool = (tool[0], tool[1] if len(tool) > 1 else "")
    local = _local_argv(ROOT, spec["local"], tool)
    ci_sites = _ci_argvs(ROOT, spec["ci"], tool)
    if local is None or not ci_sites:
        missing = "local" if local is None else "CI"
        return "refused", [
            f"    the {missing} site invokes no `{spec['tool']}` -- ci/gates/parity.py "
            f"decides that case on every change; this run cannot proceed over it."
        ]

    local_dir = str(Path(spec["local"]["makefile"]).parent).replace(".", "")
    sides = [("local", local, local_dir, f"{spec['local']['makefile']}:{spec['local']['target']}")]
    for argv, workdir, _claim, label in ci_sites:
        sides.append(("ci", argv, workdir, label))

    lines = []
    for which, argv, workdir, label in sides:
        lines.append(f"    {which:<6} {render(normalise(argv, workdir, norm))}   [{label}]")

    if not spec.get("rejects"):
        lines.append(f"    not executed: {spec.get('why_no_input', 'no broken input declared')}")
        return "declared", lines
    if listing:
        lines.append(f"    not executed: --list runs nothing. Its broken input "
                     f"{spec['rejects']} is there; this invocation did not use it")
        return LISTED, lines

    source = ROOT / spec["rejects"]
    if not source.is_dir():
        lines.append(f"    the declared broken input {spec['rejects']} is absent")
        return "refused", lines

    rejected: list[str] = []
    accepted: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for which, argv, workdir, label in sides:
            staged = Path(tmp) / f"{which}-{len(rejected) + len(accepted)}"
            shutil.copytree(source, staged)
            code, last = run_against(absolutise(argv, workdir, norm), staged)
            if code is None:
                lines.append(f"    REFUSED: {last} -- an obligation whose tool is absent is "
                             f"not an obligation this run covered")
                return "refused", lines
            (rejected if code != 0 else accepted).append(f"{which} ({label}) exit {code}")
            lines.append(f"    {which:<6} exit {code}  {last[:90]}")

    if accepted and rejected:
        lines.append(f"    the two invocations disagree about {spec['rejects']}: "
                     f"{'; '.join(rejected)} rejected it, {'; '.join(accepted)} did not")
        return "divergence", lines
    if accepted:
        lines.append(f"    NEITHER invocation rejected {spec['rejects']} -- they agree, and "
                     f"they agree on deciding nothing. A text comparison reads this as a pass")
        return "inert", lines
    return "parity", lines


def main(argv: list[str]) -> int:
    only = None
    listing = False
    rest = list(argv)
    while rest:
        arg = rest.pop(0)
        if arg == "--only":
            only = rest.pop(0) if rest else None
        elif arg == "--list":
            listing = True
        else:
            raise SystemExit(f"unknown argument: {arg}")

    manifest = json.loads((ROOT / "ci" / "vault.json").read_text(encoding="utf-8"))
    cfg = manifest.get("parity")
    if not cfg:
        print("[FAIL] parity: ci/vault.json declares no `parity` section, so this check "
              "has no subject -- an undeclared set is not an empty one")
        return 1
    obligations = {k: v for k, v in cfg["obligations"].items() if not k.startswith("_")}
    if only:
        obligations = {k: v for k, v in obligations.items() if k == only}
        if not obligations:
            raise SystemExit(f"no declared obligation named {only!r}")

    print(f"== dual-invocation parity | {len(obligations)} declared obligation(s)"
          f"{' | listing only' if listing else ''}\n"
          "   each argv below is the NORMALISED form the two sides are compared in\n")
    tally: dict[str, list[str]] = {}
    for name, spec in sorted(obligations.items()):
        verdict, lines = check(name, spec, cfg, listing)
        tally.setdefault(verdict, []).append(name)
        label = VERDICTS.get(verdict, verdict.upper())
        print(f"  [{label}] {name}: {spec['obligation']}")
        for line in lines:
            print(line)
        print()

    executed = len(tally.get("parity", [])) + len(tally.get("divergence", [])) + len(tally.get("inert", []))
    print(f"  obligations: {len(obligations)} | executed against a broken input: {executed} "
          f"| declared without one: {len(tally.get('declared', []))}"
          + (f" | not executed by --list: {len(tally.get(LISTED, []))}" if listing else ""))
    broken = [*tally.get("divergence", []), *tally.get("inert", []), *tally.get("refused", [])]
    if broken:
        print(f"\n[FAIL] parity: {len(broken)} obligation(s) not in parity: {', '.join(sorted(broken))}")
        print("  rule: docs/method/rules/one-obligation-one-invocation.md")
        return 1
    if listing:
        # No verdict: nothing ran. Saying "[ok]" here would be a pass reported
        # over zero invocations, which is the failure the whole check is about.
        print("\n[listing] parity: nothing was run. Drop --list to execute both "
              "invocations of each obligation against its broken input")
        return 0
    print("\n[ok] parity: every executed obligation was rejected by both of its invocations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
