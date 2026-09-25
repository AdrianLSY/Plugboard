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
from _workflow import executable_text

GATE_ID = "correspondences"
RULE_NOTE = "docs/method/rules/one-set-one-encoding.md"


def _dig(manifest: dict, dotted: str):
    node = manifest
    for part in dotted.split("."):
        node = node[part]
    return node


def _path_member(pattern: str) -> str:
    """One spelling for a root-anchored path, whichever file it came from.

    CODEOWNERS anchors with a leading slash and a shell prefix test does not, so
    `/contract/` and `contract/` are the same member and must compare equal.
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


def _workflow_env_words(text: str, variable: str) -> set[str]:
    """The words a workflow assigns to `variable`, provided an executed line reads it.

    The read is part of the member set's meaning. A variable declared and never
    expanded by a `run:` body is a list the workflow publishes and does not act
    on -- the shape of the reverted security gate that counted scanners named in
    a step's `name:` while every step ran `echo skipping`.
    """
    assigned = re.findall(rf"^\s+{re.escape(variable)}\s*:\s*(.*?)\s*$", text, re.M)
    if len(assigned) != 1:
        raise ValueError(
            f"{variable} is assigned {len(assigned)} times; exactly one assignment "
            f"is a member set, and more than one is a question of which step wins"
        )
    if not re.search(rf"\$\{{?{re.escape(variable)}\b", executable_text(text)):
        raise ValueError(
            f"{variable} is assigned and no executed line reads it, so the workflow "
            f"publishes the list and acts on none of it"
        )
    return {_path_member(w) for w in assigned[0].strip("'\"").split()}


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
                for absent in sorted(m for m in members if not (scan_root / m).exists()):
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
