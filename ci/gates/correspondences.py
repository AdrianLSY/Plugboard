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

Four cases, all four failing:

  1. A member one side holds and the other omits, in EITHER direction, named as
     a member rather than as a count.
  2. A side that resolves to nothing. An empty side reconciles with anything.
  3. A resolver that cannot run -- reported as a failure, never raised as a
     crash, because a reconciliation that dies takes the rest of the run with it.
  4. A correspondence both of whose sides now resolve through one resolver. That
     is no longer a pair, and leaving it declared invites a second encoding back
     under a name that looks checked.

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

from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, rule_notes

GATE_ID = "correspondences"
RULE_NOTE = "docs/method/rules/one-set-one-encoding.md"


def _dig(manifest: dict, dotted: str):
    node = manifest
    for part in dotted.split("."):
        node = node[part]
    return node


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
        for missing in sorted(computed - published):
            report.fail(
                f"{name}: '{missing}' is held by the computed side and absent from "
                f"the published one"
            )
        for extra in sorted(published - computed):
            report.fail(
                f"{name}: '{extra}' is published and the computed side does not hold "
                f"it"
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
