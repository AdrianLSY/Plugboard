#!/usr/bin/env python3
"""Meta-check: every gate has a violating input, and the gate is what fails on it.

docs/code-standards -- "The gates are themselves demonstrated to fail":

  * every gate holds a deliberately violating input in the repository;
  * the gate is demonstrated to fail on it;
  * a gate that PASSES on its own violating input fails the build;
  * each violating input names the gate it exercises and that gate's rule note.

The reason this exists rather than being trusted: the reference project's
`mix precommit` ran `compile --warning-as-errors` -- singular, the wrong flag --
while CI ran the plural one, so the checker did not check and nobody noticed.
A gate that is never proven to fail is indistinguishable from a gate that
cannot fail.

## The neuter test, and why it is generic

Confirming a gate exits non-zero on its fixture is not enough: it could be
exiting non-zero for a reason that has nothing to do with its own rule -- an
uncaught exception, a hardcoded exit, a fixture that trips some other check.
So each gate is also run against its fixture with one surgical change: in a
throwaway copy of the tree, `Report.fail()` is made a no-op.

Every gate reports violations exclusively through `Report.fail()`, and
`Report.finish()` returns 0 when nothing was recorded. So with `fail()` neutered
a sound gate MUST exit 0. If it still exits non-zero, the failure was never the
gate's own logic, and the fixture proves nothing about the rule it claims to
demonstrate. That inference holds for every gate without this module knowing
anything about what any individual gate checks.

Bijection is established from the filesystem -- `ci/gates/<module>.py` against
`ci/broken-inputs/<gate-id>/` -- rather than from a declared roster, because a
roster is a second encoding of what the tree already states, and the two drift.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "meta"
RULE_NOTE = "docs/method/rules/gates-are-demonstrated-to-fail.md"

# This module checks the others; it is not its own subject.
NOT_A_GATE = {"meta", "a module whose name starts with _ (a shared library)"}


def gate_modules(root: Path) -> dict[str, Path]:
    return {
        p.stem: p
        for p in sorted((root / "ci" / "gates").glob("*.py"))
        if p.stem != "meta" and not p.stem.startswith("_")
    }


def gate_id_for(module: str) -> str:
    """ci/gates/out_of_scope.py <-> ci/broken-inputs/out-of-scope/."""
    return module.replace("_", "-")


def fixture_trees(fixture_dir: Path) -> list[Path]:
    """Every `tree*` subdirectory. A gate may need more than one scenario."""
    return sorted(p for p in fixture_dir.glob("tree*") if p.is_dir())


def run_gate(module_path: Path, tree: Path, *, gates_dir: Path | None = None) -> int:
    return subprocess.run(
        [sys.executable, str(module_path), "--root", str(tree)],
        capture_output=True,
        cwd=str(gates_dir or module_path.parent),
    ).returncode


def neuter_and_run(root: Path, module: str, tree: Path) -> tuple[int, str]:
    """Run the gate against its fixture with Report.fail made a no-op.

    The staged copy must be a *usable repository root*, not a bare directory:
    every gate resolves its manifest by walking up from its own file looking for
    ci/vault.json, so staging into an arbitrary temp dir makes each gate exit
    non-zero before a line of its own logic runs -- which reads exactly like the
    defect this test is meant to find. So the copy reproduces ci/vault.json,
    ci/gates/ and ci/gen/ under a fake root, and the fixture path stays absolute
    and points at the real tree.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fake_root = Path(tmp) / "repo"
        staged = fake_root / "ci" / "gates"
        staged.parent.mkdir(parents=True)
        shutil.copytree(root / "ci" / "gates", staged)
        shutil.copy2(root / "ci" / "vault.json", fake_root / "ci" / "vault.json")
        if (root / "ci" / "gen").is_dir():
            shutil.copytree(root / "ci" / "gen", fake_root / "ci" / "gen")
        common = staged / "_common.py"
        src = common.read_text(encoding="utf-8")
        patched, count = re.subn(
            r"(\n    def fail\(self, message: str\) -> None:\n)(        self\.failures\.append\(message\)\n)",
            r"\1        return  # NEUTERED by ci/gates/meta.py\n",
            src,
            count=1,
        )
        if count != 1:
            return -1, (
                "could not neuter Report.fail in _common.py -- its signature "
                "changed, so the neuter test is no longer proving anything"
            )
        common.write_text(patched, encoding="utf-8")
        code = run_gate(staged / f"{module}.py", tree.resolve(), gates_dir=staged)
        return code, ""


def declared_rule_note(module_path: Path) -> str | None:
    for line in module_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^RULE_NOTE\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def run(scan_root: Path, report_only: bool) -> int:
    root = repo_root()
    manifest = load_manifest(root)
    report = Report(GATE_ID, RULE_NOTE)
    broken = root / "ci" / "broken-inputs"
    modules = gate_modules(root)

    checked = 0
    for module, module_path in modules.items():
        gid = gate_id_for(module)
        fixture_dir = broken / gid

        # (1) every gate has a violating input
        if not fixture_dir.is_dir():
            report.fail(
                f"{module}: no violating input at ci/broken-inputs/{gid}/ -- "
                f"a gate with no demonstrated failure cannot be trusted"
            )
            continue

        trees = fixture_trees(fixture_dir)
        if not trees:
            report.fail(
                f"{gid}: no tree*/ scenario directory under its violating input"
            )
            continue

        # (2) the violating input names its gate and that gate's rule note
        gate_md = fixture_dir / "GATE.md"
        if not gate_md.is_file():
            report.fail(
                f"{gid}: violating input has no GATE.md naming what it exercises"
            )
        else:
            text = gate_md.read_text(encoding="utf-8")
            if module not in text:
                report.fail(f"{gid}/GATE.md: does not name its gate ({module})")
            note = declared_rule_note(module_path)
            if note and note.split("#")[0] not in text:
                report.fail(
                    f"{gid}/GATE.md: does not name its gate's rule note ({note})"
                )

        for tree in trees:
            label = f"{gid}/{tree.name}"

            # (3) the gate fails on its own violating input
            code = run_gate(module_path, tree)
            if code == 0:
                report.fail(
                    f"{label}: gate PASSES on its own violating input -- "
                    f"mis-wired flag, path or enumeration"
                )
                continue

            # (4) and the gate's own logic is what fails
            neutered, err = neuter_and_run(root, module, tree)
            if neutered == -1:
                report.fail(f"{label}: {err}")
            elif neutered != 0:
                report.fail(
                    f"{label}: still fails (exit {neutered}) with Report.fail neutered -- "
                    f"the failure is not the gate's own logic, so this fixture "
                    f"demonstrates nothing about the rule it claims"
                )
            checked += 1
            report.examine(f"{gid}/{tree.name}")

    # (5) ISOLATION: a violating input must fail its own gate and no other
    # PER-FILE gate. Whole-tree gates are excluded and the exclusion is declared
    # in ci/vault.json, because a minimal fixture necessarily fails all of them:
    # it has no entry point, no generated index, no reader configuration. Running
    # this over all twenty gates produced 165 failures, none of them a defect --
    # satisfying it literally means building one complete valid vault per
    # fixture. What survives is the check that matters: a links fixture must not
    # trip the wikilink gate, so each demonstration stays unambiguous.
    whole_tree = set(
        manifest["gate_policy"].get("whole_tree_gates", {}).get("gates", [])
    )
    # Both policy rosters are held to the gates that actually exist. A name in
    # either that is not a gate excuses nothing and reads as though it does:
    # `whole_tree_gates` silently widened the isolation exemption, and a typo in
    # `blocking` silently demoted a gate to report-only. Neither had anything
    # checking it, which is the shape this file exists to refuse.
    # Plus this gate's own id: meta excludes itself from the roster it checks,
    # and it is still a gate the policy may legitimately name.
    real = {gate_id_for(m) for m in modules} | {GATE_ID}
    policy = manifest["gate_policy"]
    for key, names in (
        ("whole_tree_gates.gates", whole_tree),
        ("blocking", set(policy.get("blocking", []))),
    ):
        for ghost in sorted(names - real):
            report.fail(
                f"ci/vault.json gate_policy.{key} names `{ghost}`, which is not a "
                f"gate. A roster entry matching no gate excuses nothing while "
                f"reading from the outside as though it does"
            )

    cross = 0
    for module, _module_path in modules.items():
        gid = gate_id_for(module)
        for tree in fixture_trees(broken / gid):
            for other, other_path in modules.items():
                if other == module or gate_id_for(other) in whole_tree:
                    continue
                if run_gate(other_path, tree) != 0:
                    cross += 1
                    report.fail(
                        f"{gid}/{tree.name}: also fails ci/gates/{other}.py -- a "
                        f"violating input that trips a second gate makes that "
                        f"gate's own demonstration ambiguous"
                    )

    report.coverage(
        covered=sorted(modules),
        excluded=sorted(NOT_A_GATE),
        kind="gate scenario",
        source="scan",
        scan_root=scan_root,
    )
    print(
        f"  gates: {len(modules)} | scenarios proven to fail by their own logic: "
        f"{checked} | per-file cross-gate failures: {cross} "
        f"(whole-tree gates excluded: {len(whole_tree)})"
    )
    return report.finish(report_only=report_only)


main_guard(run)
