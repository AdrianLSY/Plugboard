#!/usr/bin/env python3
"""Gate: an obligation enforced in two places is enforced the same way in both.

Enforces docs/method/rules/one-obligation-one-invocation.md. rebuild-plugboard
task 3.11.

The defect is precise and it is this repository's founding example: the prior art
ran `mix compile --warning-as-errors` in its local hook -- SINGULAR, and therefore
a flag the compiler ignores -- and the correct plural flag in CI. For months the
local guardrail checked nothing, CI checked everything, and the two agreed often
enough that nobody looked. A second encoding of one obligation does not announce
its drift; it just stops being the same check.

## What counts as a subject, and what deliberately does not

Only an obligation whose two invocations are INDEPENDENTLY WRITTEN. Most are not:
`.github/workflows/check.yml` runs `make check`, and `test.yml` runs the same make
targets a contributor runs, so there is one encoding reached from two places and
nothing can drift. Those are declared with `single_encoding: true` and reported as
such rather than silently skipped -- a subject set that quietly excludes most of
its members is the shape this repository refuses everywhere else.

The Go linter is the real case. `make -C <component> lint` spells the invocation
in ci/make/go.mk; CI hands its own `args:` to golangci/golangci-lint-action,
because the action caches the binary. Two spellings, one obligation.

## What it decides

For each dual-encoded obligation: the FLAGS both sides pass, after the declared
normalisation, are the same set. A flag on one side and not the other fails,
naming both spellings.

## What it does not decide

Whether the flags are the right ones -- that is the configuration's business --
or whether a tool behaves the same across versions. Nor anything about an
obligation enforced in exactly one place, which cannot drift from itself and is
reported as out of scope on every run.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root
from _workflow import executes, triggers

GATE_ID = "parity"
RULE_NOTE = "docs/method/rules/one-obligation-one-invocation.md"

MAKE_VAR = re.compile(r"\$\((\w+)\)")


def make_variables(text: str) -> dict[str, str]:
    """`NAME := value` / `NAME ?= value` assignments, for expanding a recipe."""
    out = {}
    for m in re.finditer(r"^(\w+)\s*[:?]?=\s*(.*)$", text, re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def expand(value: str, variables: dict[str, str], depth: int = 0) -> str:
    if depth > 5:
        return value
    def sub(m):
        return variables.get(m.group(1), m.group(0))
    grown = MAKE_VAR.sub(sub, value)
    return grown if grown == value else expand(grown, variables, depth + 1)


def flags(argv: str, normalisation: dict) -> set[str]:
    """The comparable flag set: `--name=value` pairs, values normalised.

    A path is reduced to its basename -- one side says `$(REPO_ROOT)/.golangci.yml`
    and the other `../.golangci.yml`, and they are the same file. That is a
    difference which is not a difference, and every one of them is DECLARED in
    ci/vault.json rather than decided here, because a normalisation nobody can see
    is an exemption.
    """
    path_flags = set(normalisation.get("path_flags", []))
    value_flags = set(normalisation.get("value_flags", []))
    tokens = argv.split()
    out, i = set(), 0
    while i < len(tokens):
        t = tokens[i]
        if not t.startswith("-"):
            i += 1
            continue
        if t in value_flags | path_flags and i + 1 < len(tokens):
            value = tokens[i + 1]
            if t in path_flags:
                value = value.rsplit("/", 1)[-1]
            out.add(f"{t}={value}")
            i += 2
            continue
        out.add(t)
        i += 1
    return out


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["parity"]
    norm = cfg.get("normalisation", {})
    obligations = {k: v for k, v in cfg["obligations"].items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)
    dual = single = 0

    for name, spec in sorted(obligations.items()):
        report.examine(name)
        if spec.get("single_encoding"):
            single += 1
            continue
        dual += 1

        mk = scan_root / spec["local"]["makefile"]
        wf = scan_root / spec["ci"]["workflow"]
        if not mk.is_file() or not wf.is_file():
            report.fail(
                f"{name}: declared dual-invocation and one side is absent "
                f"({spec['local']['makefile']}, {spec['ci']['workflow']})"
            )
            continue

        mk_text = mk.read_text(encoding="utf-8")
        m = re.search(spec["local"]["recipe_pattern"], mk_text, re.M)
        if not m:
            report.fail(
                f"{name}: {spec['local']['makefile']} no longer carries a recipe "
                f"matching its declared pattern, so the local invocation this "
                f"compares against is gone"
            )
            continue
        local = expand(m.group("argv"), make_variables(mk_text))

        from _workflow import executable_text
        runs = executable_text(wf.read_text(encoding="utf-8"))
        ci_matches = re.findall(spec["ci"]["argv_pattern"], runs, re.M)
        if not ci_matches:
            report.fail(
                f"{name}: {spec['ci']['workflow']} carries no invocation matching "
                f"its declared pattern in a position the runner EXECUTES -- a flag "
                f"set that appears only in a comment or a step name is not an "
                f"invocation"
            )
            continue

        want = flags(local, norm) | set(spec.get("implicit_local", []))
        # One finding per divergent FLAG, with the number of CI invocations it
        # diverges in -- not one per invocation. There are three
        # golangci-lint-action steps, one per Go module, so a single drifted flag
        # reported per step is the same defect printed three times, and a gate
        # whose output repeats itself is one that stops being read.
        missing_in, extra_in = {}, {}
        for found in ci_matches:
            got = flags(found if isinstance(found, str) else found[0], norm) \
                | set(spec.get("implicit_ci", []))
            for f in want - got:
                missing_in[f] = missing_in.get(f, 0) + 1
            for f in got - want:
                extra_in[f] = extra_in.get(f, 0) + 1
        total = len(ci_matches)
        for f, n in sorted(missing_in.items()):
            report.fail(
                f"{name}: `{f}` is passed locally and not in {n} of {total} CI "
                f"invocation(s) -- the prior art ran `--warning-as-errors` locally, "
                f"singular and therefore inert, and the plural flag in CI, for months"
            )
        for f, n in sorted(extra_in.items()):
            report.fail(
                f"{name}: `{f}` is passed in {n} of {total} CI invocation(s) and not "
                f"locally, so a contributor's run is the weaker of the two"
            )

    # (task 3.12) the standing checks run on an interval as well as on change.
    sched = cfg.get("schedule")
    if sched:
        rel = sched["workflow"]
        report.examine(f"schedule:{rel}")
        wf = scan_root / rel
        if not wf.is_file():
            report.fail(
                f"{rel}: the recurring runner ci/vault.json declares is absent, so a "
                f"gate broken by a change ELSEWHERE is found only when somebody "
                f"happens to push"
            )
        else:
            body = wf.read_text(encoding="utf-8")
            if sched["cron_trigger"] not in triggers(body):
                report.fail(
                    f"{rel}: does not trigger on `{sched['cron_trigger']}` -- without "
                    f"it this is a second on-change runner, which is the one thing it "
                    f"was not for"
                )
            for command in sched["invokes"]:
                if not executes(body, command):
                    report.fail(
                        f"{rel}: does not EXECUTE `{command}` -- the first attempt at "
                        f"this check compared against the whole file and was satisfied "
                        f"by a workflow that echoed the command names"
                    )

    report.coverage(
        covered=sorted(k for k, v in obligations.items() if not v.get("single_encoding")),
        excluded=[
            f"{k} (one encoding reached from two places, so nothing can drift)"
            for k, v in sorted(obligations.items()) if v.get("single_encoding")
        ] + ["whether the flags are the right ones (the configuration's business)"],
        kind="dual-invocation obligation",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  obligations: {dual} dual-encoded, {single} reached through one encoding")
    return report.finish(report_only=report_only)


main_guard(run)
