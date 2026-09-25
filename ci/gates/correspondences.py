#!/usr/bin/env python3
"""Gate: a published enumeration and the computed one are reconciled.

Enforces docs/code-standards -- "A published enumeration and the computed one
are reconciled".

The live instance this gate exists for: `docs/rule-index.md` published "42 rules
-- 20 gated" while `ci/gates/rule_gate_correspondence.py` counted 43 / 21 over
the same set. One `make check` run printed both. The missing member was
`docs/method/authority-precedence.md` -- a gated rule appearing in no row of the
index `CLAUDE.md` routes every reader to. `ci/gates/index_drift.py` passed over
it because it compared the generator to its own output, never to the gate's
count.

Five cases, all five failing:

  1. A member one side holds and the other omits, in EITHER direction, named as
     a member rather than as a count.
  2. A side that resolves to nothing. An empty side reconciles with anything.
  3. A resolver that cannot run -- reported as a failure, never raised as a
     crash, because a reconciliation that dies takes the rest of the run with it.
  4. A correspondence both of whose sides now resolve through one resolver. That
     is no longer a pair, and leaving it declared invites a second encoding back
     under a name that looks checked.
  5. A side declared `in_tree` naming a path the tree does not hold. Two sets can
     agree perfectly about a directory that does not exist, and a rule over
     nothing reads exactly like a rule over something.

## The pair that needs case 5

`.github/CODEOWNERS` against the paths `dependabot-auto-merge.yml` refuses to
advance unattended (rebuild-plugboard task 1.9). The owner reviews and nothing
blocks on that review -- a sole maintainer cannot approve their own pull request
-- so what stops an unattended input advancing a person-reviewed path is the
workflow's exclusion. Two encodings, deliberately: each is read by a different
party (the forge requests review from one, the workflow refuses from the other),
and deriving either from the other would let one deleted line remove both.
Reconciling them member by member is what makes that safe. The forge ignores a
CODEOWNERS line it cannot resolve without any warning, and ignores a path that
matches nothing just as quietly, which is why the owner side is held to the tree.

## Why declared rather than discovered

Three triggers were drafted and measured before this one. "Published in a
tracked artifact a reader is routed to" produced 361 findings with a single true
positive, because an in-force requirement already makes very nearly every
tracked subject reachable from an entry point -- so the trigger narrowed nothing. A pair
of encodings is a fact about how this repository was built. A person knows it; a
regex cannot recover it. So it is declared, and the declaration names which
resolver each side uses.

## Why members and not counts

A count says two encodings disagree. It cannot say which member diverged, and
the member is the whole of the diagnosis: "42 against 43" sent nobody to
authority-precedence.md.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, rule_notes
from _workflow import executable_lines

GATE_ID = "correspondences"
RULE_NOTE = "docs/method/rules/one-set-one-encoding.md"


def _dig(manifest: dict, dotted: str):
    node = manifest
    for part in dotted.split("."):
        node = node[part]
    return node


def _path_member(pattern: str) -> str:
    """A CODEOWNERS pattern, spelled as the member the workflow's list names.

    CODEOWNERS anchors a root path with a leading slash; the workflow tests each
    of its words as a prefix of a repo-relative changed path, which never begins
    with one. So `/contract/` in CODEOWNERS is the member `contract/`, and the
    slash is dropped HERE, on the CODEOWNERS side only. The workflow's words are
    compared as written: normalising `/contract/` there too would reconcile an
    exclusion that matches no changed path and refuses nothing, which is why
    _workflow_env_words refuses that spelling instead of repairing it.
    """
    return pattern.lstrip("/")


def _codeowners_paths(text: str) -> set[str]:
    """Every path pattern a CODEOWNERS file assigns, anchored at the root.

    A glob or an unanchored pattern is refused rather than approximated: it
    matches a set of paths, not one prefix, and a reconciliation that guessed at
    that set would report agreement it had not checked.
    """
    members = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern = line.split()[0]
        if not pattern.startswith("/") or any(c in pattern for c in "*?["):
            raise ValueError(
                f"{pattern!r} is a glob or unanchored pattern, which names a set of "
                f"paths rather than one prefix and cannot be compared member by member"
            )
        members.add(_path_member(pattern))
    return members


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _structural(line: str) -> bool:
    """A line that carries YAML structure: neither blank nor a comment."""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _yaml_parent(lines: list[str], at: int) -> int | None:
    """The nearest line above `at` indented less than it: the key or list item
    it sits under, or None at the top level."""
    depth = _indent(lines[at])
    for j in range(at - 1, -1, -1):
        if _structural(lines[j]) and _indent(lines[j]) < depth:
            return j
    return None


def _single_line_value(lines: list[str], at: int, variable: str) -> str:
    """The scalar assigned on line `at`, which must be single-line plain or quoted.

    Anything else is refused by name. Split as raw text, a folded block became
    the one member `>-` and a trailing comment became the members `#` and
    `reviewed`: each failed closed, and each blamed the wrong thing.
    """

    def unsupported(spelling: str) -> ValueError:
        return ValueError(
            f"{variable} at line {at + 1} is {spelling}; only a single-line plain "
            f"or quoted scalar is read, so spell it as one line of space-separated "
            f"paths"
        )

    raw = lines[at].split(":", 1)[1].strip()
    if raw.startswith(("|", ">")):
        raise unsupported(f"a block scalar ({raw!r})")
    if raw.startswith(("'", '"')):
        close = raw.find(raw[0], 1)
        if close < 0:
            raise unsupported("a quoted scalar that does not close on its line")
        value, rest = raw[1:close], raw[close + 1 :]
        if rest.strip() and not re.match(r"\s+#", rest):
            raise unsupported(
                f"a quoted scalar followed by more text ({rest.strip()!r})"
            )
    else:
        value = re.sub(r"(?:^|\s+)#.*$", "", raw)  # ' #' opens a YAML comment
    for k in range(at + 1, len(lines)):
        if not _structural(lines[k]):
            continue
        if _indent(lines[k]) > _indent(lines[at]):
            raise unsupported(f"a plain scalar continued onto line {k + 1}")
        break
    return value


def _assignment_scope(lines: list[str], at: int, variable: str) -> tuple[int, int, str]:
    """(first, end, where): the source lines whose executed text sees line `at`.

    A step's `env:` is visible to that step alone. Read across the whole file, an
    exclusion left on the fetch-metadata step passed while the refusing step
    looped over an empty variable and the merge step ran. So a step-level
    assignment is scoped to its step -- from the enclosing `- ` item to the next
    item at the same indent -- and a job- or workflow-level one keeps the file.
    """
    env = _yaml_parent(lines, at)
    if env is None or not re.match(r"\s*(?:-\s+)?env\s*:\s*$", lines[env]):
        held = lines[env].strip() if env is not None else "the top level"
        raise ValueError(
            f"{variable} is assigned at line {at + 1} under {held!r}, not an env: "
            f"block, so no step's shell sees it as a variable"
        )
    item = env if lines[env].lstrip().startswith("- ") else _yaml_parent(lines, env)
    steps = _yaml_parent(lines, item) if item is not None else None
    if (
        item is None
        or not lines[item].lstrip().startswith("- ")
        or steps is None
        or not re.match(r"\s*steps\s*:\s*$", lines[steps])
    ):
        return 0, len(lines), "anywhere in the file"
    end = next(
        (
            k
            for k in range(item + 1, len(lines))
            if _structural(lines[k]) and _indent(lines[k]) <= _indent(lines[item])
        ),
        len(lines),
    )
    return item, end, f"in the step at line {item + 1} that assigns it"


_SEPARATORS = re.compile(r"&&|\|\||;|\|")


def _segments(line: str) -> list[str]:
    """Each command position on a shell line, as _workflow._runs splits them."""
    return [segment.strip() for segment in _SEPARATORS.split(line)]


def _workflow_env_words(text: str, variable: str) -> set[str]:
    """The words a workflow assigns to `variable`, provided the step holding them
    acts on them.

    The read is part of the member set's meaning. A variable declared and never
    expanded where the shell acts on it is a list the workflow publishes and does
    not enforce -- the shape of the reverted security gate that counted scanners
    named in a step's `name:` while every step ran `echo skipping`. So:

      * Only a single-line plain or quoted scalar is read: one layer of matching
        quotes and a trailing YAML comment are stripped, and a block scalar
        (`|`, `>`) or a scalar continued onto the next line is refused by name.
      * A word beginning with `/` is refused, not normalised. The workflow tests
        each word as a prefix of a repo-relative changed path, so the CODEOWNERS
        spelling copied across matches nothing and refuses nothing.
      * A step-level `env:` counts only that step's executed lines; job- and
        workflow-level `env:` keep the whole file. An assignment under any other
        key is refused, because no shell sees it as a variable at all.
      * The one read recognised is `for NAME in ...` at a command position with
        `$VAR`, `${VAR}` or `${{ env.VAR }}` an unquoted word of its list, because
        that is where the shell acts on each word. A shell comment is not a read,
        nor an echo, nor a quoted expansion -- one word, so the loop runs once
        with the whole list as a single prefix. Anything else is refused rather
        than guessed at.
      * A step that reassigns the variable (`VAR=`, `export VAR=`) is refused: its
        loop acts on that value, not on the list reconciled here.

    What this still cannot decide: a read reached through a script file, a
    function or another variable, and a reassignment by `read`, `unset` or a
    sourced file. Stated because the check is a floor, not a proof -- the same
    limit _workflow.executes() states for a command.
    """
    lines = text.splitlines()
    var = re.escape(variable)
    assigned = [i for i, line in enumerate(lines) if re.match(rf"\s+{var}\s*:", line)]
    if len(assigned) != 1:
        raise ValueError(
            f"{variable} is assigned {len(assigned)} times; exactly one assignment "
            f"is a member set, and more than one is a question of which step wins"
        )
    at = assigned[0]
    words = _single_line_value(lines, at, variable).split()
    anchored = [w for w in words if w.startswith("/")]
    if anchored:
        raise ValueError(
            f"{variable} names {anchored!r}; the workflow tests each word as a prefix "
            f"of a repo-relative changed path, which never begins with '/', so a "
            f"leading slash matches nothing and refuses nothing"
        )

    first, end, where = _assignment_scope(lines, at, variable)
    executed = [
        (i, line)
        for i, line in executable_lines(text)
        if first <= i < end and not line.strip().startswith("#")
    ]
    reassigns = re.compile(rf"(?:export\s+)?{var}=")
    for i, line in executed:
        if any(reassigns.match(segment) for segment in _segments(line)):
            raise ValueError(
                f"{variable} is reassigned by the shell at line {i + 1} "
                f"({line.strip()!r}), so the loop acts on that value and not on "
                f"the list reconciled here"
            )
    expansion = re.compile(
        rf"(?:^|\s)(?:\${var}|\$\{{{var}\}}|\$\{{\{{\s*env\.{var}\s*\}}\}})(?=\s|$)"
    )
    loop = re.compile(r"(?:(?:do|then|else)\s+)*for\s+\w+\s+in\s+(.*)$")
    word_lists = [
        m.group(1)
        for _i, line in executed
        for segment in _segments(line)
        if (m := loop.match(segment))
    ]
    if not any(expansion.search(listed) for listed in word_lists):
        raise ValueError(
            f"{variable} is assigned and no executed line reads it {where} as a "
            f"'for NAME in ...' word list, the only read this gate recognises: "
            f"${variable}, ${{{variable}}} or ${{{{ env.{variable} }}}} standing "
            f"unquoted in that list is where the shell acts on each word, and any "
            f"other read is refused rather than guessed at"
        )
    return set(words)


#: Resolver kinds whose `path` names a file in the tree rather than a manifest key.
FILE_KINDS = {"codeowners_paths", "workflow_env_words"}


def _where(pair: dict) -> str:
    """Which file each side is, when both are files -- a member alone says what
    diverged, and a reader then has to find out where."""
    sides = [pair["computed"], pair["published"]]
    if not all(s.get("kind") in FILE_KINDS for s in sides):
        return ""
    named = [
        f"{s['path']} ({s['variable']})" if s.get("variable") else s["path"]
        for s in sides
    ]
    return f" [computed: {named[0]}; published: {named[1]}]"


def resolve(side: dict, scan_root: Path, manifest: dict) -> tuple[set[str], str | None]:
    """(members, error). An error is returned, never raised."""
    kind = side.get("kind")
    try:
        if kind == "gate_modules":
            d = scan_root / "ci" / "gates"
            return {
                p.stem.replace("_", "-")
                for p in d.glob("*.py")
                if not p.stem.startswith("_")
            }, None
        if kind == "manifest_list":
            return {str(x) for x in _dig(manifest, side["path"])}, None
        if kind == "rule_notes":
            return set(rule_notes(scan_root, manifest["code_standards"])), None
        if kind == "workflow_files":
            # Every tracked workflow the forge would run. The published side is
            # ci/vault.json's runner.workflows, and ci/gates/runner.py checks the
            # forbidden clauses only on what that declares -- so a workflow file
            # the declaration omits is one whose path filters, branch filters and
            # continue-on-error nothing reads. Three of five were in exactly that
            # state until rebuild-plugboard task 3.1 was settled.
            d = scan_root / side["path"]
            return (
                {(Path(side["path"]) / p.name).as_posix() for p in d.glob("*.yml")}
                if d.is_dir()
                else set()
            ), None
        if kind == "manifest_keys":
            return {
                str(k)
                for k in _dig(manifest, side["path"])
                if not str(k).startswith("_")
            }, None
        if kind == "codeowners_paths":
            text = (scan_root / side["path"]).read_text(encoding="utf-8")
            return _codeowners_paths(text), None
        if kind == "workflow_env_words":
            text = (scan_root / side["path"]).read_text(encoding="utf-8")
            return _workflow_env_words(text, side["variable"]), None
        return set(), f"unknown resolver kind {kind!r}"
    except Exception as exc:  # a resolver that cannot run is a finding, not a crash
        return set(), f"{type(exc).__name__}: {exc}"


def run(scan_root: Path, report_only: bool) -> int:
    # This gate's subject IS the declaration, so a violating input must be able
    # to carry a different one. Where the scan root holds a manifest, that is
    # the one under test; otherwise the repository's.
    manifest = load_manifest(
        scan_root if (scan_root / "ci" / "vault.json").is_file() else repo_root()
    )
    cfg = manifest["correspondences"]
    declared = {k: v for k, v in cfg["declared"].items() if not k.startswith("_")}
    retired = {k: v for k, v in cfg.get("retired", {}).items() if not k.startswith("_")}
    report = Report(GATE_ID, RULE_NOTE)

    for name, pair in sorted(declared.items()):
        report.examine(name)
        sides = {}
        for which in ("computed", "published"):
            side = pair.get(which)
            if not isinstance(side, dict):
                report.fail(f"{name}: declares no '{which}' side")
                continue
            if not side.get("members"):
                report.fail(
                    f"{name}/{which}: names no members -- an artifact stating a "
                    f"cardinal without naming its members is not a side, because a "
                    f"count cannot say which member diverged"
                )
            members, error = resolve(side, scan_root, manifest)
            if error:
                report.fail(
                    f"{name}/{which}: its resolver could not run ({error}) -- "
                    f"reported rather than raised, so one broken side does not take "
                    f"the rest of the run with it"
                )
                continue
            if not members:
                report.fail(
                    f"{name}/{which}: resolved to nothing -- an empty side "
                    f"reconciles with anything, which is not the same as agreeing"
                )
            # (5) a path two sets agree about is still a rule over nothing if the
            # tree does not hold it.
            if side.get("in_tree"):
                for absent in sorted(
                    m for m in members if not (scan_root / m).exists()
                ):
                    report.fail(
                        f"{name}/{which}: names '{absent}', which is absent from the "
                        f"tree -- {side.get('path', 'the side')} would then govern "
                        f"nothing while reading as though it governed something"
                    )
            sides[which] = (members, side.get("kind"))

        if len(sides) != 2:
            continue
        # (4) both sides through one resolver is no longer a pair.
        if sides["computed"][1] == sides["published"][1]:
            report.fail(
                f"{name}: both sides declare the resolver kind "
                f"{sides['computed'][1]!r} -- a correspondence closed by collapsing "
                f"onto one resolver is retired with that resolver recorded, not left "
                f"declared as though it were still checked"
            )
            continue
        # (1) both directions, named by member.
        computed, published = sides["computed"][0], sides["published"][0]
        where = _where(pair)
        for missing in sorted(computed - published):
            report.fail(
                f"{name}: '{missing}' is held by the computed side and absent from "
                f"the published one{where}"
            )
        for extra in sorted(published - computed):
            report.fail(
                f"{name}: '{extra}' is published and the computed side does not hold "
                f"it{where}"
            )

    for name, entry in sorted(retired.items()):
        report.examine(f"retired:{name}")
        if not (entry.get("closed_by") and entry.get("reason")):
            report.fail(
                f"retired correspondence '{name}': records no 'closed_by' resolver "
                f"and reason -- a retirement with no stated cause is indistinguishable "
                f"from a deletion"
            )

    report.coverage(
        covered=sorted(declared),
        excluded=sorted(f"retired:{k}" for k in retired),
        kind="correspondence",
        source="manifest",
        scan_root=scan_root,
    )
    print(f"  correspondences: {len(declared)} live | {len(retired)} retired")
    return report.finish(report_only=report_only)


main_guard(run)
