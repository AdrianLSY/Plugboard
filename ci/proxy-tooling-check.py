#!/usr/bin/env python3
"""Every tool in `make -C proxy lint` is demonstrated to refuse, one at a time.

Serves rebuild-plugboard task 2.2. The tooling half of that task is wiring:
`mix compile --warnings-as-errors`, `mix format --check-formatted`, Credo
strict, Dialyzer against a cached PLT, Sobelow and `mix deps.audit`, all
reachable from one target. This is the other half, and it is the half the prior
art skipped: each of those tools is shown to FAIL on an input built to violate
it, and to stay silent on the other five.

The reason that is a separate piece of work rather than an assumption: the prior
art declared Credo as a dependency and never invoked it, and its local guardrail
ran `compile --warning-as-errors` -- singular, accepted, inert -- while CI ran
the plural flag, for months (docs/history/reference-audit.md). A tool wired into
a target and never proven to refuse is indistinguishable from a tool that cannot.

## What this DECIDES

  1. The roster is complete: every command in the `lint` recipe of
     ci/make/elixir.mk is paired with a violating input that names it. The
     roster is parsed from the recipe, not declared here, so a tool added to
     lint and never demonstrated is a failure rather than a silence.
  2. The pairing BINDS: a tree's declared `tool` is among its declared `fails`,
     it declares a `case`, and it declares the files it plants. Without that
     first clause the roster is satisfied by a label -- swapping two trees'
     `tool` fields left every measured set unchanged, and the two assertions
     that would have caught it (case, reachability) are both decidable only
     when the named tool is among the tools that failed, so both skipped and
     the run said ok. A label is not a demonstration.
  3. A clean copy of proxy/ passes all of them, and passes `make -C proxy lint`.
     Without that, every result below means nothing.
  4. Per violating input: the exact SET of tools that fail is the set declared
     in expect.json. For five of the six that set is one tool -- the others are
     demonstrated blind to it. Any input whose set is larger has to name, per
     extra tool, the mechanism that forces it, and cite a file and a string
     this check looks up. A reason nothing reads is prose, and the whole
     directory exists because prose is not a declaration.
  5. The failing tool failed for the stated reason: its output carries the
     declared case substring, and that substring is NOT in what the same tool
     says about a clean copy. A tool exiting non-zero for an unrelated reason
     demonstrates nothing about the rule it is supposed to enforce, and a case
     the tool prints either way demonstrates nothing about the tool; this is
     the same inference ci/gates/meta.py makes with its neuter test.
  6. `make -C proxy lint` itself refuses on each input, which is what makes the
     tool REACHABLE from the target rather than merely installed.
  7. The declaration and ci/vault.json agree about who checks this directory.
     The vault's gate_policy.script_paired_inputs entry is what makes a
     directory with no ci/gates/<name>.py a decision instead of an orphan, and
     an entry naming a different script than expect.json's `checked_by` names
     nobody.

## What it does NOT decide

Whether each tool's configuration is the right one -- which Credo checks are
enabled, which Dialyzer flags, whether Sobelow's threshold is where it should
be. It decides that the configured tool fires, not that the configuration is
well chosen; that is review's.

Nor does it decide anything about a tool's reach. Sobelow reports on `lib/`
here with no Phoenix router present, and this check proves that by planting a
finding it catches -- it does not establish which of Sobelow's checks are
inapplicable to a non-Phoenix project, and several are.

Nor is it a gate. Its subject is six external processes against a copied tree,
not a property of the tree, so it is not in ci/gates/ and does not belong inside
`make check` -- the command a contributor runs on every commit starts no
process. It is invoked on its own.

## Why the copy is tar and not `git archive`

`git archive` exports the committed tree. Running these tools over that means
reporting on code that is not the code in the working tree, and a green result
over unpatched sources is the exact shape of a check that looks like it ran. The
scratch copy is a tar of the working tree, planted violations laid over it.

Usage:
    python3 ci/proxy-tooling-check.py                 # every violating input
    python3 ci/proxy-tooling-check.py --list          # the pairing, run nothing
    python3 ci/proxy-tooling-check.py --only credo    # one input
    python3 ci/proxy-tooling-check.py --keep          # leave the scratch trees
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURES = "ci/broken-inputs/proxy-tooling"
RECIPE = "ci/make/elixir.mk"
COMPONENT = "proxy"
SELF = "ci/proxy-tooling-check.py"
VAULT = "ci/vault.json"

#: Copied into the scratch tree so proxy/Makefile's `include $(REPO_ROOT)/...`
#: resolves and `make -C proxy lint` is the same recipe it is in the repository.
#:
#: ci/stamp.py is here because `lint` now declares `stamp`, which runs it. Without
#: it the copy's very first target fails and every tool below reports against a
#: tree that never compiled -- the baseline check caught exactly that, which is
#: what a baseline is for.
SUPPORT = ["ci/make", "ci/stamp.py"]

#: Requirements of the copy, each with the command that satisfies it. A missing
#: one is refused rather than worked around: building a PLT inside a throwaway
#: copy six times over is the kind of slowness that stops a check being run.
PREREQUISITES = {
    "deps": ("proxy/deps", "make -C proxy deps"),
    "build": ("proxy/_build", "make -C proxy lint"),
}

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "ci" / "vault.json").is_file():
            return candidate
    raise SystemExit("could not locate ci/vault.json")


def tool_id(task: str) -> str:
    """`deps.audit` is a directory name too, and a dot is not one."""
    return task.replace(".", "-")


def lint_commands(root: Path) -> list[tuple[str, list[str]]]:
    """(tool id, argv) for each command in the lint recipe, in recipe order.

    Parsed rather than declared: a roster written here is a second encoding of
    what ci/make/elixir.mk states, and the two drift in the direction where a
    tool is added to lint and demonstrated by nothing.
    """
    text = (root / RECIPE).read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("lint:"))
    except StopIteration:
        raise SystemExit(f"{RECIPE}: declares no `lint` target, so there is no roster")
    commands = []
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        argv = line.strip().lstrip("@-").split()
        if not argv or argv[0] != "$(MIX)":
            raise SystemExit(
                f"{RECIPE}: the lint recipe holds `{line.strip()}`, which is not a "
                f"$(MIX) invocation -- this check pairs a violating input to a mix "
                f"task, and cannot pair one to that"
            )
        commands.append((tool_id(argv[1]), argv[1:]))
    return commands


def declaration(root: Path) -> tuple[dict, object]:
    """(the trees, whatever `checked_by` says). Both are read; see check_ownership."""
    path = root / FIXTURES / "expect.json"
    if not path.is_file():
        raise SystemExit(f"{FIXTURES}/expect.json: absent, so nothing declares what these inputs do")
    document = json.loads(path.read_text(encoding="utf-8"))
    trees = document.get("trees", {})
    return (
        {k: v for k, v in trees.items() if not k.startswith("_")},
        document.get("checked_by"),
    )


def tar_copy(src: Path, dst: Path) -> None:
    """Copy src's CONTENTS into dst, or src itself when src is a file.

    Never `git archive`: see the docstring. The file case exists because one
    support entry is a single script, ci/stamp.py, and tar -C on a file is an
    error rather than a copy.
    """
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        dst.chmod(src.stat().st_mode)
        return
    dst.mkdir(parents=True, exist_ok=True)
    producer = subprocess.Popen(
        ["tar", "-cf", "-", "-C", str(src), "."], stdout=subprocess.PIPE
    )
    consumer = subprocess.run(["tar", "-xf", "-", "-C", str(dst)], stdin=producer.stdout)
    if producer.stdout is not None:
        producer.stdout.close()
    if producer.wait() != 0 or consumer.returncode != 0:
        raise SystemExit(f"tar: copying {src} to {dst} failed")


def render(tools: list[str]) -> str:
    """An empty set is the interesting case, so it is a word and not `[]`."""
    return ", ".join(tools) if tools else "none"


def run(cwd: Path, argv: list[str]) -> tuple[int, str]:
    done = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True)
    return done.returncode, ANSI.sub("", done.stdout + done.stderr)


def failing_set(proxy: Path, commands: list[tuple[str, list[str]]], mix: str) -> dict[str, tuple[int, str]]:
    """Every tool's outcome, not the first failure: the SET is the assertion."""
    return {tid: run(proxy, [mix, *args]) for tid, args in commands}


def stage(root: Path, scratch: Path, name: str) -> Path:
    """A scratch tree that `make -C proxy lint` runs in unchanged."""
    tree = scratch / name
    tar_copy(root / COMPONENT, tree / COMPONENT)
    for rel in SUPPORT:
        tar_copy(root / rel, tree / rel)
    return tree


class Findings:
    """Accumulate and report all of them. One at a time is slow feedback, and
    slow feedback is what makes assertions cheap (docs/code/testing.md)."""

    def __init__(self) -> None:
        self.items: list[str] = []
        self._examined: set[str] = set()
        self._excluded: dict[str, str] = {}

    def fail(self, message: str) -> None:
        self.items.append(message)

    def examine(self, task: str) -> None:
        """One lint command whose refusal was actually MEASURED on this run.

        Derived, never handed over as a literal: the count used to be
        `len(commands)`, so a run narrowed by --only, and a run that stopped
        because mix was absent, both printed the full roster as their reach.
        Same rule as ci/gates/_common.py's Report.examine, for the same reason.
        """
        self._examined.add(task)

    def exclude(self, task: str, why: str) -> None:
        self._excluded[task] = why

    @property
    def examined(self) -> set[str]:
        return set(self._examined)

    def finish(self, source: str, roster: int) -> int:
        count = len(self._examined)
        noun = "lint command" if count == 1 else "lint commands"
        covered = ", ".join(sorted(self._examined)) or "-"
        excluded = (
            ", ".join(f"{t} ({w})" for t, w in sorted(self._excluded.items())) or "-"
        )
        print(
            f"\ncoverage: {count} {noun} from the lint recipe of {source}"
            f" | covered: {covered} | excluded: {excluded}"
        )
        if not self.items:
            # "every" is a claim about the roster, so it is only made by a run
            # that reached the roster. A narrowed run says what it reached.
            print(
                "proxy tooling: every lint command is demonstrated to refuse"
                if count == roster
                else f"proxy tooling: the {count} of {roster} lint commands this run "
                f"reached are demonstrated to refuse -- the rest are excluded above"
            )
            return 0
        print(f"\n[FAIL] proxy-tooling: {len(self.items)} finding(s)")
        for item in self.items:
            print(f"  - {item}")
        return 1


def check_plants(root: Path, name: str, entry: dict, found: Findings) -> None:
    """`plants` names exactly the files the tree overlays onto proxy/.

    Read, not decorative. A field shaped like an assertion that asserts nothing
    is the defect ci/gates/fixture_declarations.py exists for, one layer in.
    Both directions are checked: a plant that is not on disk is a declaration of
    a violation nobody planted, and a file on disk that is not declared is a
    change to the copied tree nothing asserts about -- which is how a fixture
    grows a second violation and the `fails` set silently starts meaning
    something else.
    """
    tree = root / FIXTURES / name
    on_disk = sorted(
        str(p.relative_to(tree)) for p in tree.rglob("*") if p.is_file()
    )
    plants = entry.get("plants")
    if not isinstance(plants, list) or not plants:
        found.fail(
            f"{FIXTURES}/expect.json: '{name}' declares no `plants` -- the files it "
            f"lays over {COMPONENT}/ are then whatever happens to be in the directory, "
            f"and the tree holds {render(on_disk)}"
        )
        return
    declared_plants = sorted(str(p) for p in plants)
    for rel in declared_plants:
        if rel not in on_disk:
            found.fail(
                f"{FIXTURES}/{name}/{rel}: declared in `plants` and absent -- the "
                f"violation the `fails` set is attributed to is not in the tree"
            )
        elif (root / COMPONENT / rel).exists() and rel not in (entry.get("derived_from") or {}):
            found.fail(
                f"{FIXTURES}/{name}/{rel}: plants over the real {COMPONENT}/{rel} and "
                f"is not declared `derived_from` it -- a fixture that REPLACES a file "
                f"of the component silently drops whatever that file holds, and the "
                f"tools below would be reporting on a tree nobody described"
            )
    for rel in on_disk:
        if rel not in declared_plants:
            found.fail(
                f"{FIXTURES}/{name}/{rel}: in the tree and not in `plants` -- an "
                f"input nothing asserts about is an input nothing runs"
            )


def check_forced(root: Path, name: str, tool: str, reason, found: Findings) -> None:
    """A wider failing set has to name the mechanism that forces it, checkably.

    `why_not_alone` used to be any truthy string, which licensed an arbitrarily
    large declared set for the price of a sentence. So it names, per extra tool,
    a `because` and a `forced_by` citation: a file and a string in it. When the
    mechanism is removed from the file, the reason stops being true and this
    says so, instead of the set quietly staying declared.
    """
    where = f"{FIXTURES}/expect.json: '{name}'.why_not_alone['{tool}']"
    if not isinstance(reason, dict) or not str(reason.get("because", "")).strip():
        found.fail(
            f"{where}: no `because` -- '{tool}' is declared to fail alongside the "
            f"tool this input is for, and an unexplained second failure is the "
            f"difference between a demonstration and a tree that breaks everything"
        )
        return
    citations = reason.get("forced_by")
    if not isinstance(citations, dict) or not citations:
        found.fail(
            f"{where}: a `because` and no `forced_by` -- a reason nothing looks up "
            f"is prose, and this directory exists because prose is not a declaration. "
            f"Cite the file and the string that forces it"
        )
        return
    for rel, quote in sorted(citations.items()):
        path = root / rel
        if not path.is_file():
            found.fail(f"{where}: cites {rel}, which is not a file")
        elif str(quote) not in path.read_text(encoding="utf-8"):
            found.fail(
                f"{where}: cites {rel} for {str(quote)[:60]!r} and that file no longer "
                f"holds it -- the mechanism the wider failing set is blamed on is gone, "
                f"so the set has to be re-measured rather than re-declared"
            )


def check_ownership(root: Path, declared_by: object, found: Findings) -> None:
    """expect.json and ci/vault.json agree that THIS script checks the directory.

    ci/vault.json's gate_policy.script_paired_inputs is what makes a directory
    under ci/broken-inputs with no ci/gates/<name>.py a decision rather than an
    orphan. Two declarations of the same fact drift; this reads both.
    """
    if declared_by != SELF:
        found.fail(
            f"{FIXTURES}/expect.json: `checked_by` is {declared_by!r} and this script "
            f"is {SELF} -- the inputs name a checker that is not the one running them"
        )
    policy = json.loads((root / VAULT).read_text(encoding="utf-8")).get("gate_policy", {})
    entry = policy.get("script_paired_inputs", {}).get(FIXTURES)
    if not isinstance(entry, dict):
        found.fail(
            f"{VAULT}: gate_policy.script_paired_inputs declares nothing for {FIXTURES} "
            f"-- a directory here with no ci/gates/<name>.py and no entry there is an "
            f"orphan, and reads as one to every gate that pairs the two"
        )
    elif entry.get("checked_by") != SELF:
        found.fail(
            f"{VAULT}: gate_policy.script_paired_inputs['{FIXTURES}'].checked_by is "
            f"{entry.get('checked_by')!r} and {FIXTURES}/expect.json names {SELF} -- "
            f"two declarations of who checks this directory, disagreeing"
        )


def check_roster(root: Path, commands, declared, found: Findings) -> None:
    """The declaration itself, before any process runs.

    Kept separate from the measurements because a declaration that does not bind
    makes every measurement under it meaningless: the measured set is compared
    against `fails`, and the case and reachability assertions are both decidable
    only when the named tool is among the tools that failed. Swap two trees'
    `tool` fields and nothing measured changes, both of those skip, and the run
    reports ok over two tools bound to no input. So the binding is asserted here.
    """
    argv_by_tool = {tid: " ".join(args) for tid, args in commands}
    by_tool = {}
    for name, entry in declared.items():
        by_tool.setdefault(entry.get("tool"), []).append(name)
    for tid, args in commands:
        names = by_tool.get(tid, [])
        if not names:
            found.fail(
                f"`mix {' '.join(args)}` is in the lint recipe and no violating "
                f"input under {FIXTURES}/ names it -- a tool wired into a target "
                f"and never shown to refuse is indistinguishable from one that cannot"
            )
    known = set(argv_by_tool)
    for name, entry in sorted(declared.items()):
        tid = entry.get("tool")
        if tid not in known:
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' names tool '{tid}', which the "
                f"lint recipe does not invoke -- the input demonstrates a tool "
                f"nothing runs"
            )
        if not (root / FIXTURES / name).is_dir():
            found.fail(f"{FIXTURES}/{name}: declared and absent")
        else:
            check_plants(root, name, entry, found)

        fails = entry.get("fails")
        if not isinstance(fails, list) or not fails:
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' declares no failing tools -- an "
                f"input that makes nothing refuse demonstrates nothing, and the "
                f"exact-set assertion is satisfied by every tool staying silent"
            )
            fails = []
        for other in sorted(set(fails) - known):
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' declares '{other}' among its "
                f"failing tools and the lint recipe does not invoke it"
            )
        # The binding. Everything else about this tree is read through it.
        if tid in known and tid not in fails:
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' names tool '{tid}' and does not "
                f"list it in `fails` ({render(sorted(fails))}) -- the input is then "
                f"bound to no tool at all: the measured set is compared against "
                f"`fails`, and both the case and the `make -C {COMPONENT} lint` "
                f"assertions are decidable only when '{tid}' is among the tools that "
                f"failed, so both would skip and the tree would report ok"
            )
        case = entry.get("case")
        if not isinstance(case, str) or not case.strip():
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' declares no `case` -- then `mix "
                f"{argv_by_tool.get(tid, tid)}` exiting non-zero for any reason at all "
                f"reads as a demonstration of the rule it is supposed to enforce"
            )

        extras = sorted(set(fails) - {tid})
        why = entry.get("why_not_alone")
        if extras and not isinstance(why, dict):
            found.fail(
                f"{FIXTURES}/expect.json: '{name}' declares {render(extras)} failing "
                f"alongside '{tid}' and no `why_not_alone` map -- one tool failing "
                f"alone is the property this check exists for, and an input that "
                f"cannot show it has to say why, per tool, where this check reads it"
            )
            why = {}
        why = why if isinstance(why, dict) else {}
        for other in extras:
            if other not in why:
                found.fail(
                    f"{FIXTURES}/expect.json: '{name}' declares '{other}' failing "
                    f"alongside '{tid}' and `why_not_alone` does not cover it"
                )
        for other in sorted(set(why) - set(extras)):
            found.fail(
                f"{FIXTURES}/expect.json: '{name}'.why_not_alone explains '{other}', "
                f"which it does not declare failing -- a licence for a failure that "
                f"is not claimed"
            )
        for other in extras:
            if other in why:
                check_forced(root, name, other, why[other], found)

    # Any directory, not `tree*`: a fixture directory named something else is
    # still a tree laid over the component, and matching on a prefix means the
    # one that is misnamed is the one nothing asserts about.
    on_disk = {
        p.name for p in (root / FIXTURES).iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    }
    for name in sorted(on_disk - set(declared)):
        found.fail(
            f"{FIXTURES}/{name}: a violating input expect.json declares nothing "
            f"for -- an input nothing asserts about is an input nothing runs"
        )


def check_derivation(root: Path, name: str, entry: dict, found: Findings) -> None:
    """A fixture that EXTENDS a real file must still contain it.

    The lockfile fixture is proxy/mix.lock plus one entry. When the real lock
    changes and the fixture does not, the copy's dependencies diverge from its
    build and several tools fail at once -- a true failure naming the wrong
    cause. This names the right one.
    """
    for rel, source_rel in (entry.get("derived_from") or {}).items():
        fixture = root / FIXTURES / name / rel
        source = root / source_rel
        if not fixture.is_file() or not source.is_file():
            found.fail(f"{FIXTURES}/{name}/{rel}: declared as derived from {source_rel}, and one of the two is absent")
            continue
        held = set(fixture.read_text(encoding="utf-8").splitlines())
        missing = [
            l for l in source.read_text(encoding="utf-8").splitlines()
            if l.strip() and l not in held
        ]
        if missing:
            found.fail(
                f"{FIXTURES}/{name}/{rel}: no longer contains every line of "
                f"{source_rel} ({len(missing)} missing, first: {missing[0].strip()[:60]!r}) "
                f"-- the fixture has drifted from the file it extends, and the tools "
                f"would fail here for that reason instead of the planted one"
            )


def main(argv: list[str]) -> int:
    root = repo_root()
    mix = shutil.which("mix")
    commands = lint_commands(root)
    declared, declared_by = declaration(root)
    found = Findings()
    #: tool id -> the command a contributor would type. The id is the
    #: directory-safe spelling (`deps-audit`), and `mix deps-audit` is not a
    #: task -- a failure message that names it hands the reader "The task
    #: deps-audit could not be found".
    argv_by_tool = {tid: " ".join(args) for tid, args in commands}
    task_by_tool = {tid: args[0] for tid, args in commands}

    if "--list" in argv:
        for tid, args in commands:
            names = [n for n, e in sorted(declared.items()) if e.get("tool") == tid]
            for name in names or ["(no violating input)"]:
                entry = declared.get(name, {})
                print(
                    f"  {tid:<12} mix {' '.join(args):<28} {name:<18} "
                    f"fails: {render(entry.get('fails', []))}"
                )
        return 0

    check_ownership(root, declared_by, found)
    check_roster(root, commands, declared, found)

    only = None
    if "--only" in argv:
        at = argv.index("--only") + 1
        if at >= len(argv):
            raise SystemExit("--only takes a tool id or a tree name; see --list")
        only = argv[at]
    selected = {
        n: e for n, e in sorted(declared.items())
        if only is None or e.get("tool") == only or n == only
    }
    if only is not None and not selected:
        raise SystemExit(f"--only {only}: no violating input names that tool")

    # A missing toolchain STOPS the run: every tree below would fail for that
    # reason and report nothing about any tool. A roster finding does not stop
    # it -- those are findings about the declaration, and the trees that do
    # exist still have something to demonstrate.
    blocked = mix is None or any(
        not (root / rel).exists() for rel, _ in PREREQUISITES.values()
    )
    if mix is None:
        found.fail(
            "mix is not on PATH, so nothing ran. A check that skips when its "
            "toolchain is absent reports green over an unexamined tool, which is "
            "the shape of the defect this check exists to refuse"
        )
    for label, (rel, how) in PREREQUISITES.items():
        if not (root / rel).exists():
            found.fail(
                f"{rel}: absent, so the scratch copy has no {label} and every tool "
                f"below would fail for that reason. Run `{how}` once and re-run this"
            )
    if blocked:
        for tid in argv_by_tool:
            found.exclude(task_by_tool[tid], "nothing ran: toolchain or build absent")
        return found.finish(RECIPE, len(commands))

    scratch = Path(tempfile.mkdtemp(prefix="proxy-tooling-"))
    keep = "--keep" in argv
    try:
        base = stage(root, scratch, "baseline")
        outcomes = failing_set(base / COMPONENT, commands, mix)
        #: What each tool says about an UNVIOLATED copy. Kept because a `case`
        #: the tool prints anyway discriminates nothing: it would be carried by
        #: the output of a run that found the planted violation and by the
        #: output of a run that found nothing, and the assertion it is the
        #: subject of would hold either way.
        baseline_output = {tid: output for tid, (_, output) in outcomes.items()}
        clean = True
        for tid, (code, output) in outcomes.items():
            if code != 0:
                clean = False
                found.fail(
                    f"baseline: `mix {argv_by_tool[tid]}` fails on an unmodified copy of {COMPONENT}/ "
                    f"(exit {code}) -- every result below is meaningless until that is "
                    f"true, and the last lines were:\n      "
                    + "\n      ".join(output.strip().splitlines()[-6:])
                )
        code, _ = run(base, ["make", "-C", COMPONENT, "lint"])
        if code != 0:
            clean = False
            found.fail(f"baseline: `make -C {COMPONENT} lint` fails on an unmodified copy (exit {code})")
        print(
            f"  [{'ok  ' if clean else 'FAIL'}] baseline: {len(outcomes)} tools and "
            f"`make -C {COMPONENT} lint` on a clean copy of {COMPONENT}/"
        )

        for name, entry in selected.items():
            tid = entry.get("tool")
            check_derivation(root, name, entry, found)
            tree = stage(root, scratch, name)
            tar_copy(root / FIXTURES / name, tree / COMPONENT)
            outcomes = failing_set(tree / COMPONENT, commands, mix)
            observed = sorted(t for t, (code, _) in outcomes.items() if code != 0)
            expected = sorted(entry.get("fails", []))

            if tid in task_by_tool:
                found.examine(task_by_tool[tid])
            if observed != expected:
                found.fail(
                    f"{name}: the tools that fail are {render(observed)}, and "
                    f"expect.json declares {render(expected)} -- "
                    + (
                        f"`mix {argv_by_tool.get(tid, tid)}` did not refuse its own violating input"
                        if tid not in observed
                        else "a tool that is supposed to be blind to this input saw it"
                    )
                )
            # The case and the target are only decidable when the tool DID
            # refuse. Reporting them otherwise buries the one finding that
            # matters under two restatements of it.
            case = entry.get("case")
            # Decidable without the tool refusing, and it has to be: a case the
            # tool prints on a clean tree makes the assertion below true of a
            # run that saw nothing.
            if clean and case and case in baseline_output.get(tid, ""):
                found.fail(
                    f"{name}: the declared case ({case[:60]!r}) is in `mix "
                    f"{argv_by_tool.get(tid, tid)}`'s output on an UNVIOLATED copy of "
                    f"{COMPONENT}/ too -- it does not tell a run that found the planted "
                    f"violation apart from a run that found nothing, so the assertion it "
                    f"is the subject of holds either way"
                )
            if tid in observed and case and case not in outcomes[tid][1]:
                found.fail(
                    f"{name}: `mix {argv_by_tool.get(tid, tid)}` failed and its output does not carry the "
                    f"declared case ({case[:60]!r}) -- a tool exiting non-zero for "
                    f"some other reason demonstrates nothing about the rule it enforces"
                )
            code, _ = run(tree, ["make", "-C", COMPONENT, "lint"])
            if tid in observed and code == 0:
                found.fail(
                    f"{name}: `make -C {COMPONENT} lint` PASSES on it while `mix "
                    f"{argv_by_tool.get(tid, tid)}` "
                    f"refuses it -- the tool is installed and not reachable from the "
                    f"target, which is the prior art's exact defect"
                )
            mark = "ok  " if observed == expected else "FAIL"
            print(f"  [{mark}] {name}: fails {render(observed)}, make lint exit {code}")
    finally:
        if keep:
            print(f"\nscratch trees kept at {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)

    # What the run did NOT reach, named rather than absorbed into the count.
    for tid, task in sorted(task_by_tool.items()):
        if task in found.examined:
            continue
        found.exclude(
            task,
            f"--only {only}" if only is not None
            else "no violating input names it",
        )
    return found.finish(RECIPE, len(commands))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
