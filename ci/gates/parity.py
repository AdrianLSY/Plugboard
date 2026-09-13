#!/usr/bin/env python3
"""Gate: an obligation enforced locally and in CI is enforced by one invocation.

Enforces docs/method/rules/one-obligation-one-invocation.md. rebuild-plugboard
tasks 3.11 and 3.12.

The reference project ran `mix compile --warning-as-errors` in its local hook --
singular, therefore a switch `mix` accepts and ignores -- and the plural,
correct flag in CI. For months the local guardrail checked nothing, and the only
observable difference was that the hook was fast. Both invocations existed. Both
were green. Nothing compared them.

## What an obligation is here, concretely

An **obligation** is one property this repository refuses on, declared in
ci/vault.json's `parity.obligations` with the two places it is invoked from:

  * a LOCAL site -- a make target reachable from `make precommit`, named as a
    component Makefile and a target. Its argv is read out of that Makefile and
    everything it includes, with make variables expanded.
  * a CI site -- either an action step whose `args:` are the tool's argv
    directly, or the make recipe a `run:` step reaches. The reaching step is
    DISCOVERED: the declaration names the recipe, never the command line, so
    "the step now runs something else" is a case that can actually fire.

Neither argv is written down in the declaration. The declaration names the two
SITES; the two argvs are read out of the tree. A gate holding a copy of the
expected flags would be a third encoding, and the third encoding is the one that
goes stale silently.

Two argvs are the same invocation when, after normalisation, they agree on the
program, the subcommand, the flag/value set, and the remaining positionals.
Normalisation is declared in `parity.normalisation`, not decided here: a path
argument is resolved against the working directory each site runs in (so
`$(REPO_ROOT)/.golangci.yml` from `sidecar/` and `../.golangci.yml` from the
action's `working-directory: sidecar` are the same file, and are not reported as
a difference), and a tool whose missing positional means `./...` has it supplied
on both sides.

Six cases, all six failing:

  1. The two resolved argvs differ -- both are printed, with the difference.
  2. The declared local site no longer invokes the obligation's tool.
  3. No step in the declared workflow reaches it -- the CI half is gone, or was
     pointed at a different recipe.
  4. A declared parity tool invoked DIRECTLY in a workflow and claimed by no
     declared obligation -- a second encoding of a checking tool that nothing
     compares to the local one. This is the clause that keeps the declaration
     from being a roster that goes stale: adding `run: mix format
     --check-formatted` to a workflow fails here until it is declared.
  5. The scheduled runner: absent, missing the declared interval or trigger,
     carrying one of the clauses `runner.forbidden_clauses` names, or not
     invoking one of the declared scheduled commands (task 3.12). "Invoking"
     means a `run:` step whose argv IS that command -- not the string appearing
     somewhere in the file. This clause was once a substring test over the file
     body, and the same workflow prints both command names in its run summary:
     `echo "| \\`make check-gates\\` | ..."`. Deleting both real steps left the
     gate green over a schedule that ran neither. The same hole has four
     spellings and all four are refused: the name as a step's `name:`, as a
     shell comment, as an `echo` argument, and as a line of a here-document body
     (`cat <<'EOF' >/dev/null` ... -- data the shell hands to `cat`, executed by
     nothing). A step that invokes the command only behind an `if:` -- its own or
     its job's -- fails too, because this gate does not evaluate workflow
     expressions and will not assume one.
  6. A declared obligation whose broken input is gone, so ci/parity.py has
     nothing to run either invocation against. Repository-scoped, for the reason
     ci/gates/binary_assets.py states: a violating input is deliberately partial
     and its file set has nothing to do with this manifest's.

## What this gate does NOT decide

It does not run either invocation, so it cannot see an INERT flag: a spelling
both sides share, which both tools accept and neither acts on, is identical on
both sides and passes here. That is the half ci/parity.py holds, by running both
invocations against a tracked broken input and requiring both to reject it --
and it is why the parity check is two programs rather than one. Do not read a
green run of this gate as "the obligation is enforced"; read it as "the two
invocations of it are the same invocation".

It does not decide that an obligation OUGHT to be enforced in both places. The
subject is the declared pairs. An obligation enforced locally and nowhere in CI
is a different rule, and no check here states it.

It does not decide that a scheduled run HAPPENED. A workflow file can declare an
interval; whether the hosting service fired it, and whether anyone looked, is
server-side and unreadable from the tree -- the same boundary
ci/gates/runner.py draws for branch protection.
"""

from __future__ import annotations

import posixpath
import re
import shlex
from pathlib import Path

from _common import Report, load_manifest, main_guard, on_tracked_tree, repo_root

GATE_ID = "parity"
RULE_NOTE = "docs/method/rules/one-obligation-one-invocation.md"

VAR = re.compile(r"\$[({]([A-Za-z_][A-Za-z0-9_]*)[)}]")
ASSIGN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:?+]?=\s*(.*?)\s*$")
TARGET = re.compile(r"^([A-Za-z0-9_./-]+)\s*:(?!=)")
INCLUDE = re.compile(r"^\s*[-]?include\s+(.+?)\s*$")


# --------------------------------------------------------------------------- make


def _expand(text: str, variables: dict[str, str]) -> str:
    """Substitute $(NAME)/${NAME}. Unknown names are left verbatim on purpose:
    an unexpandable recipe must be visible as one, not silently become an argv
    that no shell would ever produce."""
    for _ in range(5):
        new = VAR.sub(lambda m: variables.get(m.group(1), m.group(0)), text)
        if new == text:
            break
        text = new
    return text


def read_makefile(root: Path, rel: str, seen: set[str] | None = None) -> tuple[dict, dict]:
    """(variables, target -> recipe lines) for a makefile and everything it includes."""
    seen = seen if seen is not None else set()
    if rel in seen:
        return {}, {}
    seen.add(rel)
    path = root / rel
    if not path.is_file():
        return {}, {}
    variables: dict[str, str] = {}
    targets: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("\t"):
            if current:
                targets.setdefault(current, []).append(raw[1:])
            continue
        line = raw.split("#", 1)[0] if raw.lstrip().startswith("#") else raw
        current = None
        inc = INCLUDE.match(line)
        if inc:
            # Normalised textually rather than through the filesystem: a scan
            # root reached by a symlink would otherwise resolve every include to
            # a path outside it, and the includes would silently vanish.
            sub_rel = posixpath.normpath(
                posixpath.join(posixpath.dirname(rel), _expand(inc.group(1), variables))
            )
            if sub_rel.startswith(".."):
                continue
            sub_vars, sub_targets = read_makefile(root, sub_rel, seen)
            # The including file wins: sidecar/Makefile sets REPO_ROOT before
            # ci/make/go.mk defaults anything, which is what `?=` means.
            variables = {**sub_vars, **variables}
            targets.update(sub_targets)
            continue
        assign = ASSIGN.match(line)
        if assign and ":" not in assign.group(1):
            name, value = assign.group(1), _expand(assign.group(2), variables)
            if not (line.lstrip().startswith(name + " ?=") and name in variables):
                variables[name] = value
            continue
        hit = TARGET.match(line)
        if hit and not line.lstrip().startswith("."):
            current = hit.group(1)
            targets.setdefault(current, [])
    return variables, targets


def recipe_argvs(root: Path, rel: str, target: str) -> list[list[str]]:
    variables, targets = read_makefile(root, rel)
    out: list[list[str]] = []
    for line in targets.get(target, []):
        command = _expand(line, variables).lstrip("@-+").strip()
        if not command or command.startswith("if ") or command.startswith("@"):
            continue
        try:
            out.append(shlex.split(command))
        except ValueError:
            continue
    return out


# ------------------------------------------------------------------------ workflows


def uncommented(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


IF_KEY = re.compile(r"^\s*(?:-\s+)?if:\s*(\S.*?)\s*$")

# The word that ends a here-document. `<<<` is a here-STRING -- its operand is
# data on one line and the next line is an ordinary command -- so it is excluded
# on both sides rather than left to the word class to reject by accident.
HEREDOC = re.compile(r"(?<!<)<<-?\s*(?!<)(?P<quote>['\"]?)(?P<word>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)")


def workflow_steps(text: str) -> list[dict]:
    """Every `run:` command and every `uses:` step, each carrying the `if:` of
    the list item it belongs to.

    Line-oriented rather than a YAML parse, for the reason ci/gates/runner.py
    gives: ci/ is standard library only and the shape is small and known.

    The condition is attached here rather than looked up later because it is the
    difference between a step and a step that does not run, and the only place
    the two can still be told apart is while the item's own lines are in hand. A
    block scalar's body never reaches this loop -- the inner scan consumes it --
    so an `echo "- run: ..."` inside a shell heredoc cannot be mistaken for the
    start of a step.

    Inside a block scalar, a here-document BODY is data the shell feeds to the
    command on the line that opened it, and is executed by nothing. Every line of
    one was being yielded as its own command, which left the same hole an `echo`
    did: a summary step spelling

        cat <<'SUMMARY' >/dev/null
        make check-gates
        SUMMARY

    reported the declared command as invoked, and the schedule ran neither. So
    the body is consumed up to its terminator and only the opening line -- a real
    argv, `cat` -- is yielded. A delimiter this scan cannot recognise leaves the
    body readable as commands, which can only produce a refusal to look at; the
    reverse would produce a pass.
    """
    steps: list[dict] = []
    pending: list[dict] = []
    condition: str | None = None
    dash_indent: int | None = None

    def flush() -> None:
        for step in pending:
            step["if"] = condition
        steps.extend(pending)
        pending.clear()

    lines = uncommented(text).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip().lstrip("- ").strip()
        indent = len(line) - len(line.lstrip())
        raw = line.lstrip()
        if raw.startswith("- ") or raw == "-":
            if dash_indent is None or indent <= dash_indent:
                flush()
                condition = None
                dash_indent = indent
        elif line.strip() and dash_indent is not None and indent < dash_indent:
            # Left the list: the next dash belongs to a new one.
            dash_indent = None
        guard = IF_KEY.match(line)
        if guard:
            condition = guard.group(1)
        if stripped.startswith("run:"):
            body = stripped[4:].strip()
            if body in ("|", ">", "|-", ">-"):
                i += 1
                commands = []
                terminator: str | None = None
                while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                    text_line = lines[i].strip()
                    if terminator is not None:
                        # Inside a here-document: data, not a command.
                        if text_line == terminator:
                            terminator = None
                    elif text_line:
                        commands.append(text_line)
                        opened = HEREDOC.search(text_line)
                        if opened:
                            terminator = opened.group("word")
                    i += 1
                for command in commands:
                    pending.append({"kind": "run", "command": command})
                continue
            pending.append({"kind": "run", "command": body})
        elif stripped.startswith("uses:"):
            action = stripped[5:].strip().split("@")[0]
            step = {"kind": "uses", "action": action, "with": {}}
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indent):
                key = re.match(r"^\s*([a-z-]+):\s*(.*?)\s*$", lines[j])
                if key:
                    step["with"][key.group(1)] = key.group(2)
                j += 1
            pending.append(step)
            i = j
            continue
        i += 1
    flush()
    return steps


def job_conditions(text: str) -> list[str]:
    """Every `if:` sitting on a JOB rather than on one of its steps.

    A condition on the job guards every step inside it, so a declared command
    invoked by an unconditional step in a job nothing ever runs is as inert as
    one behind a step-level condition. Anchored on the `steps:` key: the job's
    own keys share its indentation, which is what distinguishes `jobs.<id>.if`
    from the `if:` of a step several columns further in.
    """
    lines = uncommented(text).splitlines()
    found: list[str] = []
    for i, line in enumerate(lines):
        if line.strip() != "steps:":
            continue
        indent = len(line) - len(line.lstrip())
        start = i
        while start > 0:
            previous = lines[start - 1]
            if previous.strip() and len(previous) - len(previous.lstrip()) < indent:
                break
            start -= 1
        end = i + 1
        while end < len(lines):
            nxt = lines[end]
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) < indent:
                break
            end += 1
        for sibling in lines[start:end]:
            hit = IF_KEY.match(sibling)
            if hit and len(sibling) - len(sibling.lstrip()) == indent:
                found.append(hit.group(1))
    return found


# --------------------------------------------------------------- shell commands


# A shell line is not one command. These end one and start the next; a token
# made only of these characters is punctuation rather than a program name.
CONTROL = {"|", "||", "&&", ";", ";;", "&", "|&", "(", ")", "{", "}"}
REDIRECT = re.compile(r"^\d*(?:>>|>&|&>|<<<|<<|<&|>|<)$")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def executed_argvs(line: str) -> list[list[str]]:
    """Every argv a shell would actually EXECUTE for this line, one per stage.

    `echo "| \\`make check-gates\\` |"` executes `echo`. The declared command is
    a substring of that line and is invoked by nothing in it, and a check that
    cannot tell the two apart is satisfied by a workflow that runs neither --
    which is the state this gate exists to refuse. So the line is tokenised into
    the commands a shell would run, and the match is made against argv[0:].
    """
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        # A line this tokeniser cannot read is not evidence that something ran.
        # Withholding a match can only produce a refusal to look at; inventing
        # one would produce a pass.
        return []
    stages: list[list[str]] = [[]]
    skip = False
    for token in tokens:
        if skip:
            skip = False
            continue
        if token in CONTROL:
            stages.append([])
            continue
        if REDIRECT.match(token):
            if stages[-1] and stages[-1][-1].isdigit():
                stages[-1].pop()  # the `2` of `2>&1` is a descriptor, not an argument
            skip = True  # and the target of a redirection is not a command
            continue
        stages[-1].append(token)
    out = []
    for argv in stages:
        while argv and ENV_ASSIGNMENT.match(argv[0]):
            argv = argv[1:]  # `FOO=bar make check` runs make
        if argv:
            out.append(argv)
    return out


def invoking_steps(steps: list[dict], command: str) -> list[dict]:
    """The steps whose `run:` body executes `command`, extra arguments allowed."""
    try:
        want = shlex.split(command)
    except ValueError:
        return []
    hits = []
    for step in steps:
        if step.get("kind") != "run":
            continue
        if any(argv[: len(want)] == want for argv in executed_argvs(step["command"])):
            hits.append(step)
    return hits


# ---------------------------------------------------------------------- comparison


def tool_key(argv: list[str]) -> tuple[str, str]:
    if not argv:
        return ("", "")
    program = Path(argv[0]).name
    sub = next((a for a in argv[1:] if not a.startswith("-")), "")
    return (program, sub)


def normalise(argv: list[str], workdir: str, norm: dict) -> tuple:
    """(program, subcommand, flags, positionals) -- comparable across two sites."""
    value_flags = set(norm.get("value_flags", []))
    path_flags = set(norm.get("path_flags", []))
    program = Path(argv[0]).name if argv else ""
    flags: dict[str, str] = {}
    positional: list[str] = []
    i = 1
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            if "=" in token:
                name, value = token.split("=", 1)
            elif token in value_flags and i + 1 < len(argv):
                name, value = token, argv[i + 1]
                i += 1
            else:
                name, value = token, ""
            if name in path_flags and value:
                value = _repo_relative(value, workdir)
            flags[name] = value
        else:
            positional.append(token)
        i += 1
    sub = positional[0] if positional else ""
    rest = positional[1:]
    implicit = norm.get("implicit_positional", {}).get(f"{program} {sub}".strip())
    if implicit and not rest:
        rest = [implicit]
    return (program, sub, tuple(sorted(flags.items())), tuple(sorted(rest)))


def _repo_relative(value: str, workdir: str) -> str:
    return posixpath.normpath(posixpath.join(workdir or ".", value))


def render(normalised: tuple) -> str:
    program, sub, flags, rest = normalised
    parts = [program, sub, *[f"{k}={v}" if v else k for k, v in flags], *rest]
    return " ".join(p for p in parts if p)


# ----------------------------------------------------------------------- the gate


def _local_argv(root: Path, site: dict, tool: tuple[str, str]) -> list[str] | None:
    for argv in recipe_argvs(root, site["makefile"], site["target"]):
        if tool_key(argv) == tool:
            return argv
    return None


def _ci_argvs(root: Path, site: dict, tool: tuple[str, str]):
    """Every (argv, workdir, claim, label) the declared CI site invokes the tool with.

    Two shapes of CI site, and neither names an argv:

      * `action` -- a step whose `args:` ARE the tool's arguments. The only shape
        that is a genuinely independent second encoding.
      * `reaches` -- the workflow runs `make`, and the step that reaches the named
        recipe is DISCOVERED rather than matched against a command string written
        down here. A declaration holding the command verbatim could only ever be
        satisfied or absent, so the case "the step was changed to run something
        else" would be unreachable -- which is a case that reads as enforcement
        and is none.
    """
    path = root / site["workflow"]
    if not path.is_file():
        return []
    steps = workflow_steps(path.read_text(encoding="utf-8"))
    found = []
    if "action" in site:
        for step in steps:
            if step.get("kind") != "uses" or step.get("action") != site["action"]:
                continue
            args = step["with"].get(site.get("argv_from", "args"), "")
            workdir = step["with"].get("working-directory", "")
            argv = [tool[0], *site.get("implicit", []), *shlex.split(args)]
            claim = f"{site['workflow']}:{site['action']}"
            found.append((argv, workdir, claim, f"{claim} ({workdir or '.'})"))
        return found

    via = site["reaches"]
    want_dir = str(Path(via["makefile"]).parent).replace(".", "").strip("/")
    for step in steps:
        if step["kind"] != "run":
            continue
        try:
            argv = shlex.split(step["command"])
        except ValueError:
            continue
        if not argv or Path(argv[0]).name != "make":
            continue
        directory = _make_directory(argv).strip("/")
        targets = [a for a in argv[1:] if not a.startswith("-") and a != directory]
        if directory != want_dir or via["target"] not in targets:
            continue
        resolved = _local_argv(root, via, tool)
        if resolved is None:
            continue
        claim = f"{site['workflow']}:{step['command'].strip()}"
        found.append((resolved, want_dir, claim, f"{claim} -> {via['makefile']}:{via['target']}"))
    return found


def _make_directory(argv: list[str]) -> str:
    for i, token in enumerate(argv):
        if token == "-C" and i + 1 < len(argv):
            return argv[i + 1]
        if token.startswith("-C") and len(token) > 2:
            return token[2:]
    return ""


def _check_schedule(root: Path, cfg: dict, manifest: dict, report: Report) -> None:
    spec = cfg["schedule"]
    rel = spec["workflow"]
    report.examine(rel)
    path = root / rel
    if not path.is_file():
        report.fail(
            f"{rel}: declared as the recurring runner and absent -- the meta-check and "
            f"the parity check then run only when a change happens to arrive, which is "
            f"the condition task 3.12 exists to remove"
        )
        return
    body = uncommented(path.read_text(encoding="utf-8"))
    if spec["cron"] not in body:
        report.fail(
            f"{rel}: does not declare the interval ci/vault.json states "
            f"(`{spec['cron']}`) -- an interval nothing holds is a comment"
        )
    triggers = re.search(r"^on:\s*$(.*?)(?=^\S)", body, re.M | re.S)
    block = triggers.group(1) if triggers else ""
    for want in spec["triggers"]:
        if not re.search(rf"^\s+{re.escape(want)}\s*:", block, re.M):
            report.fail(
                f"{rel}: does not trigger on `{want}` -- a gate broken by a change "
                f"elsewhere is found on the interval, and one broken by this change is "
                f"found on the change; dropping either leaves a window"
            )
    # The same clauses ci/gates/runner.py refuses, read from the SAME declaration
    # rather than copied: the recurring runner is not one of `runner.workflows`
    # (its subject is the harness rather than the tree), and a filter here would
    # defeat refusal in exactly the way that list exists to name.
    forbidden = {
        k: v for k, v in manifest["runner"]["forbidden_clauses"].items()
        if not k.startswith("_")
    }
    for key, why in sorted(forbidden.items()):
        if re.search(rf"^\s*{re.escape(key)}\s*:", body, re.M):
            report.fail(f"{rel}: carries `{key}:` -- {why}")
    # The declared commands, read from what the file EXECUTES. A substring test
    # over the file body passed a scheduled.yml whose only trace of either
    # command was the run summary printing their names -- `echo "| \`make
    # check-gates\` | ..."` satisfies "the string is present" and runs nothing.
    # So each declared command is matched against the argv of a `run:` step, and
    # against nothing else.
    steps = workflow_steps(path.read_text(encoding="utf-8"))
    guard = next(iter(job_conditions(path.read_text(encoding="utf-8"))), None)
    for command in spec["invokes"]:
        invoking = invoking_steps(steps, command)
        if not invoking:
            report.fail(
                f"{rel}: does not invoke `{command}` -- no step's `run:` body executes it "
                f"(the name inside a comment, a step `name:`, an `echo` argument or a "
                f"here-document body is not an invocation), and a schedule that runs "
                f"something else is not this declaration's schedule"
            )
            continue
        conditions = [step["if"] or guard for step in invoking]
        if all(conditions):
            report.fail(
                f"{rel}: invokes `{command}` only under a condition (`if: {conditions[0]}`) "
                f"-- the recurring runner's commands must run on the interval "
                f"unconditionally. This gate does not evaluate workflow expressions, so a "
                f"guarded step is a claim it cannot check rather than one it may assume"
            )


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    report = Report(GATE_ID, RULE_NOTE)
    cfg = manifest.get("parity")
    if not cfg:
        report.fail(
            "ci/vault.json: declares no `parity` section -- this gate's subject is the "
            "set of obligations enforced in two places, and an undeclared set is not an "
            "empty one. See docs/method/rules/one-obligation-one-invocation.md"
        )
        report.coverage(covered=[], excluded=[], kind="parity subject", source="manifest",
                        scan_root=scan_root)
        return report.finish(report_only=report_only)

    obligations = {k: v for k, v in cfg["obligations"].items() if not k.startswith("_")}
    norm = cfg.get("normalisation", {})
    # program -> the subcommands that CHECK something. `go install` is how a
    # runner obtains a linter and is not a second encoding of an obligation;
    # `go test` is. Keyed on the pair, so the difference is declared rather
    # than left to whoever reads the failure.
    tools = {
        k: set(v["subcommands"]) for k, v in cfg.get("tools", {}).items() if not k.startswith("_")
    }
    claimed: set[str] = set()
    agreed = 0

    for name, spec in sorted(obligations.items()):
        report.examine(name)
        tool = tuple(spec["tool"].split())
        tool = (tool[0], tool[1] if len(tool) > 1 else "")
        local = _local_argv(scan_root, spec["local"], tool)
        # (2) the local invocation.
        if local is None:
            report.fail(
                f"{name}: {spec['local']['makefile']}:{spec['local']['target']} invokes no "
                f"`{spec['tool']}` -- the obligation is declared enforced locally and is "
                f"not, so `make precommit` is green over a property nothing checked"
            )
            continue
        local_dir = str(Path(spec["local"]["makefile"]).parent).replace(".", "")
        local_norm = normalise(local, local_dir, norm)

        ci_sites = _ci_argvs(scan_root, spec["ci"], tool)
        # (3) the CI invocation: no step reaches the declared recipe.
        if not ci_sites:
            report.fail(
                f"{name}: {spec['ci']['workflow']} invokes no `{spec['tool']}` at the "
                f"declared site -- half of a dual-invocation obligation is gone, and the "
                f"remaining half is the one nobody watches"
            )
            continue
        for argv, workdir, claim, label in ci_sites:
            claimed.add(claim)
            ci_norm = normalise(argv, workdir, norm)
            # (1) divergence.
            if ci_norm != local_norm:
                report.fail(
                    f"{name}: the two invocations of `{spec['tool']}` differ.\n"
                    f"      local  {spec['local']['makefile']}:{spec['local']['target']}"
                    f"  ->  {render(local_norm)}\n"
                    f"      ci     {label}  ->  {render(ci_norm)}\n"
                    f"      difference: {_difference(local_norm, ci_norm)}"
                )
            else:
                agreed += 1

    # (4) a checking tool invoked directly in CI and claimed by no obligation.
    for rel in sorted(cfg.get("ci_workflows", [])):
        path = scan_root / rel
        if not path.is_file():
            continue
        for step in workflow_steps(path.read_text(encoding="utf-8")):
            if step["kind"] == "run":
                try:
                    argv = shlex.split(step["command"])
                except ValueError:
                    continue
                program, sub = tool_key(argv)
                label = f"{rel}:{step['command'].strip()}"
                watched = sub in tools.get(program, set())
            else:
                # An action wrapping a checking tool always invokes its checking
                # subcommand; there is no `uses:` spelling of `go install`.
                program = step["action"].split("/")[-1].replace("-action", "")
                label = f"{rel}:{step['action']}"
                watched = program in tools
            if watched and label not in claimed:
                report.fail(
                    f"{label}: invokes the checking tool `{program}` directly and no entry "
                    f"in ci/vault.json's parity.obligations claims it -- a second encoding "
                    f"of a checking tool that nothing compares to the local one is exactly "
                    f"the shape `--warning-as-errors` had"
                )

    # (5) the recurring runner.
    _check_schedule(scan_root, cfg, manifest, report)

    # (6) repository-scoped: the executing half needs its inputs to exist.
    if on_tracked_tree(scan_root):
        for name, spec in sorted(obligations.items()):
            rejects = spec.get("rejects")
            if rejects and not (scan_root / rejects).is_dir():
                report.fail(
                    f"{name}: declares the broken input '{rejects}', which is not there -- "
                    f"ci/parity.py then has nothing to run either invocation against, and "
                    f"the executing half of this check silently covers one fewer obligation"
                )

    report.coverage(
        covered=[*sorted(obligations), cfg["schedule"]["workflow"]],
        excluded=[
            "whether a shared spelling is inert (ci/parity.py runs both sides)",
            "whether an obligation ought to be enforced in both places",
            "whether a scheduled run fired (server-side, unreadable here)",
        ],
        kind="parity subject",
        source="manifest",
        scan_root=scan_root,
    )
    print(
        f"  obligations: {len(obligations)} | invocation pairs in agreement: {agreed} | "
        f"checking tools watched: {len(tools)} | interval: {cfg['schedule']['cron']}"
    )
    return report.finish(report_only=report_only)


def _difference(left: tuple, right: tuple) -> str:
    lf, rf = dict(left[2]), dict(right[2])
    out = []
    for key in sorted(set(lf) | set(rf)):
        if lf.get(key) != rf.get(key):
            out.append(f"{key}: local={lf.get(key, '<absent>') or '<set>'} ci={rf.get(key, '<absent>') or '<set>'}")
    if left[:2] != right[:2]:
        out.append(f"program/subcommand: local={' '.join(left[:2])} ci={' '.join(right[:2])}")
    if left[3] != right[3]:
        out.append(f"positionals: local={list(left[3])} ci={list(right[3])}")
    return "; ".join(out) or "identical after normalisation"


if __name__ == "__main__":
    main_guard(run)
