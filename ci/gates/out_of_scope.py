#!/usr/bin/env python3
"""Gate: an artifact declared out of scope stays byte-unchanged.

Enforces docs/knowledge-base -- "An artifact declared out of scope stays
byte-unchanged":

  * every path in the declared out-of-scope set is byte-identical to its
    content at the declared baseline ref -- a modification, a deletion, or an
    untracked addition under a declared prefix all fail;
  * the failure names the offending path AND the change that declared it out of
    scope, because "who said this was off limits" is the fact the contributor
    needs and the one prose loses;
  * the declared set is asserted to actually cover `rebuild-plugboard`'s
    sixteen specification files -- a set that silently covers nothing is a
    green gate over an unguarded tree, which is worse than no gate;
  * every violation is reported in one run, and a passing run states the
    baseline it compared against and how many files it covered.

The concrete defect that motivated it: this change invokes `/opsx:update` seven
times, and that tool reconciles the artifacts *around* the one it was asked to
revise, over glob-expanded spec paths, forbidding only their creation and never
their revision. So a coherence pass can reach a specification no task named,
and an intention recorded in prose is not a control. The gate is the control.

Two mechanics are deliberate and are the reason this gate does not look like
the others:

  * The subject is version-control history, not file contents, so the check is
    `git diff` against `out_of_scope.baseline_ref` plus a scan for untracked
    additions under each declared prefix -- not a walk of the tree.
  * The manifest read is the scan root's own. A violation of this requirement
    is a property of the *declaration* plus history, never of a file's bytes,
    so a fixture tree can only exercise it by carrying its own declaration --
    and a scan root carrying no declaration is reported not applicable rather
    than failed, which is what keeps another gate's violating input from
    failing this one. On the real run the scan root IS the repository root, by
    definition of repo_root(), so nothing about the real check changes.

A fixture tree cannot hold git history (a nested repository would be a gitlink,
and this repository forbids submodules), so the byte-modification case is
proven by `--self-test`, which builds the scenario in a temporary git
repository and asserts this gate fails on it. See
ci/broken-inputs/out-of-scope/GATE.md for the reproduction command.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import (
    MANIFEST_NAME,
    Report,
    candidates,
    classify,
    exempt_roots,
    load_manifest,
    main_guard,
    on_tracked_tree,
    scan_excludes,
)

GATE_ID = "out-of-scope"
RULE_NOTE = "docs/method/rules/out-of-scope-byte-unchanged.md"

# ci/vault.json declares the SET (a directory prefix); it does not declare the
# shape of what that set must cover, and this gate must not invent a manifest
# key. So the coverage assertion task 1.12 names is stated here, next to the
# requirement text it comes from: the sixteen specification files of
# rebuild-plugboard. If the change ever legitimately gains or loses a
# specification, this constant is the one place that moves, in the same commit.
SPEC_SET_ROOT = "openspec/changes/rebuild-plugboard/specs"
SPEC_FILENAME = "spec.md"
EXPECTED_SPEC_FILES = 16


def _git(root: Path, *args: str) -> tuple[int, bytes]:
    """Run git in `root`; return (exit code, stdout). Never raises."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False
        )
    except FileNotFoundError:  # no git on PATH: reported by the caller, not fatal
        return 127, b""
    return done.returncode, done.stdout


def _zsplit(payload: bytes) -> list[str]:
    return [
        item for item in payload.decode("utf-8", "surrogateescape").split("\0") if item
    ]


def _under_any(rel: str, prefixes: list[str]) -> str | None:
    """The declared prefix covering `rel`, or None. Files are prefixes too."""
    for prefix in prefixes:
        if rel == prefix or rel.startswith(prefix.rstrip("/") + "/"):
            return prefix
    return None


def _files_at_ref(root: Path, ref: str, prefixes: list[str]) -> list[str] | None:
    """Every file the baseline ref holds under the declared prefixes."""
    code, out = _git(root, "ls-tree", "-r", "-z", "--name-only", ref, "--", *prefixes)
    if code != 0:
        return None
    return sorted(_zsplit(out))


def _first_changed_line(root: Path, ref: str, rel: str) -> int | None:
    """The first changed line on the working-tree side, for a named location."""
    code, out = _git(root, "diff", "-U0", "--no-renames", ref, "--", rel)
    if code != 0:
        return None
    for line in out.decode("utf-8", "surrogateescape").splitlines():
        if line.startswith("@@"):
            # @@ -12,0 +13,2 @@ -> the new-side start, which is where a reader looks.
            try:
                new_side = line.split("+", 1)[1].split(" ", 1)[0]
                return int(new_side.split(",", 1)[0])
            except (IndexError, ValueError):
                return None
    return None


def _changed_paths(root: Path, ref: str, prefix: str) -> list[tuple[str, str]] | None:
    """(status, path) for every tracked change under `prefix` since `ref`.

    --no-renames on purpose: a rename out of the declared set must be reported
    as the deletion it is, naming the path that left, not only its destination.
    """
    code, out = _git(
        root, "diff", "-z", "--name-status", "--no-renames", ref, "--", prefix
    )
    if code != 0:
        return None
    fields = _zsplit(out)
    return [(fields[i], fields[i + 1]) for i in range(0, len(fields) - 1, 2)]


def _untracked(root: Path, prefix: str) -> list[str]:
    _code, out = _git(
        root, "ls-files", "-z", "--others", "--exclude-standard", "--", prefix
    )
    return sorted(_zsplit(out))


def _status_word(status: str) -> str:
    return {
        "M": "modified",
        "D": "deleted",
        "A": "added",
        "T": "type changed",
    }.get(status[:1], f"changed ({status})")


def _declares_own_set(scan_root: Path) -> bool:
    """Does this scan root carry the manifest whose declaration is the subject?

    The repository root always does, by definition of repo_root(). A fixture
    tree does only if it was built for THIS gate -- which matters because the
    subject here is a declaration, so another gate's fixture tree has nothing
    for this gate to assert and must not be failed by it. A violating input
    fails the gate it exercises and no other.
    """
    return (scan_root / "ci" / MANIFEST_NAME).is_file()


def run(scan_root: Path, report_only: bool) -> int:
    report = Report(GATE_ID, RULE_NOTE)
    if not _declares_own_set(scan_root):
        print(
            f"  note: {scan_root} carries no ci/{MANIFEST_NAME} and no history -- this "
            f"gate's subject is a declared set plus its baseline, so there is nothing "
            f"here to assert; not applicable"
        )
        report.coverage(
            covered=[],
            excluded=[scan_root.name],
            kind="specification",
            source="scan",
            scan_root=scan_root,
        )
        return report.finish(report_only=report_only)

    manifest = load_manifest(scan_root)

    declared = manifest.get("out_of_scope", {})
    prefixes = [p for p in declared.get("paths", []) if isinstance(p, str)]
    declared_by = declared.get("declared_by")
    baseline_ref = declared.get("baseline_ref")

    # A declaration that cannot name its owner or its baseline cannot produce
    # the failure the requirement asks for, so its absence is itself a failure.
    if not prefixes:
        report.fail(
            "ci/vault.json out_of_scope.paths is empty -- the out-of-scope set is "
            "declared in the manifest, not in prose; a change with nothing declared "
            "cannot assert anything unchanged"
        )
    if not declared_by:
        report.fail(
            "ci/vault.json out_of_scope.declared_by is missing -- a failure must name "
            "the change that declared the path out of scope"
        )
    if not baseline_ref:
        report.fail(
            "ci/vault.json out_of_scope.baseline_ref is missing -- byte-unchanged is "
            "meaningless without the revision it is unchanged against"
        )
    owners = declared_by if isinstance(declared_by, list) else [declared_by]
    owners = [o for o in owners if o]
    owner = ", ".join(owners) or "<undeclared change>"

    # A declaration cannot outlive its reason. This set protects the specs from
    # the changes that declared it; once every one of those has been archived,
    # the declaration is asserting a freeze nobody decided on -- which a pinned
    # baseline makes permanent. Failing here forces the removal to be deliberate.
    live = [o for o in owners if (scan_root / "openspec" / "changes" / o).is_dir()]
    if owners and not live and on_tracked_tree(scan_root):
        report.fail(
            f"ci/vault.json out_of_scope: every declaring change ({owner}) has been "
            f"archived, so this declaration has outlived its reason -- remove it, or "
            f"re-baseline it under a change that is actually in flight. A pinned "
            f"baseline left behind reads as a permanent freeze on "
            f"{', '.join(prefixes)}, which nobody decided"
        )

    md_paths, from_index = candidates(scan_root, manifest)
    excluded_from_run: list[str] = []

    # ---- the byte-unchanged assertion, over history -------------------------
    baseline_sha = None
    subject_files: list[str] = []
    if from_index and baseline_ref:
        code, out = _git(
            scan_root, "rev-parse", "--verify", f"{baseline_ref}^{{commit}}"
        )
        if code != 0:
            report.fail(
                f"baseline ref '{baseline_ref}' (ci/vault.json out_of_scope.baseline_ref) "
                f"does not resolve in {scan_root} -- declared by {owner}"
            )
        else:
            baseline_sha = out.decode().strip()
            subject_files = _files_at_ref(scan_root, baseline_sha, prefixes) or []
            for prefix in prefixes:
                for status, rel in (
                    _changed_paths(scan_root, baseline_sha, prefix) or []
                ):
                    where = _first_changed_line(scan_root, baseline_sha, rel)
                    at = f" (first change at line {where})" if where else ""
                    report.fail(
                        f"{rel}: {_status_word(status)} since {baseline_ref} "
                        f"({baseline_sha[:12]}){at} -- declared out of scope by "
                        f"{owner} under '{prefix}'; a revision this set covers is "
                        f"follow-up work, not an edit"
                    )
                for rel in _untracked(scan_root, prefix):
                    verdict, root = classify(rel, manifest)
                    if verdict == "excluded":
                        excluded_from_run.append(root)
                        continue
                    report.fail(
                        f"{rel}: untracked addition under '{prefix}' -- declared out of "
                        f"scope by {owner}; the set is byte-unchanged, which admits no "
                        f"new files either"
                    )
    else:
        # A fixture tree carries no history. Say so rather than passing quietly:
        # the set-coverage assertion below still runs, and it is the half of this
        # requirement that a tree without history can carry.
        print(
            f"  note: {scan_root} is not a work tree; the history comparison against "
            f"'{baseline_ref}' was not run -- set coverage only"
        )

    # ---- every declared path names something ---------------------------------
    # Checked on both routes, not only against history: a prefix that matches
    # nothing is the failure mode this requirement exists for, and it is
    # decidable without a baseline.
    for prefix in prefixes:
        if baseline_sha is not None:
            present = bool(_files_at_ref(scan_root, baseline_sha, [prefix]))
            where = f"{baseline_ref} ({baseline_sha[:12]})"
        else:
            present = (scan_root / prefix).exists()
            where = f"{scan_root}"
        if not present:
            report.fail(
                f"{prefix}: declared out of scope by {owner} but matches no file at "
                f"{where} -- a declared set that covers nothing is a gate that "
                f"asserts nothing"
            )

    # ---- the set actually covers the sixteen specifications -----------------
    if baseline_sha is not None:
        listing = subject_files
        source = f"{baseline_ref} ({baseline_sha[:12]})"
    else:
        listing = md_paths
        source = "filesystem"
    specs = sorted(
        rel
        for rel in listing
        if Path(rel).name == SPEC_FILENAME and _under_any(rel, prefixes) is not None
    )
    if len(specs) != EXPECTED_SPEC_FILES:
        report.fail(
            f"the declared out-of-scope set covers {len(specs)} '{SPEC_FILENAME}' "
            f"file(s) at {source}, expected {EXPECTED_SPEC_FILES} under "
            f"'{SPEC_SET_ROOT}' -- declared by {owner} as "
            f"[{', '.join(prefixes) or '-'}]; the coherence pass of the tool this "
            f"change invokes seven times could revise the uncovered ones unnoticed"
        )

    if not subject_files:
        subject_files = [
            rel for rel in listing if _under_any(rel, prefixes) is not None
        ]
    for _subject in subject_files:
        report.examine(_subject)
    report.coverage(
        covered=prefixes,
        excluded=[
            *exempt_roots(manifest),
            *scan_excludes(manifest),
            *excluded_from_run,
        ],
        kind="specification",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    print(
        f"  set: {len(prefixes)} declared path(s) | declared_by: {owner}"
        f" | baseline: {baseline_ref} ({baseline_sha[:12] if baseline_sha else 'unresolved'})"
        f" | {SPEC_FILENAME} covered: {len(specs)}/{EXPECTED_SPEC_FILES}"
    )
    return report.finish(report_only=report_only)


# ---------------------------------------------------------------------------
# --self-test: the byte-modification case, which needs history a fixture tree
# cannot hold. Exit 0 means this gate DETECTED the planted modification (the
# gate works); exit 1 means it did not (the gate is broken).
# ---------------------------------------------------------------------------

_SELF_TEST_MANIFEST = """{
  "spine": "docs",
  "note_roots": {"directories": ["docs", "openspec", "ci"], "root_files": ["README.md"]},
  "exempt_roots": {},
  "scan_excludes": {},
  "entry_points": {"declared": []},
  "out_of_scope": {
    "paths": ["%(prefix)s"],
    "declared_by": "%(owner)s",
    "baseline_ref": "%(baseline)s"
  },
  "classification": {"planning_directories": ["openspec"]}
}
"""

_SELF_TEST_OWNER = "restructure-docs-as-vault"


def _git_quiet(root: Path, *args: str) -> tuple[int, bytes]:
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
    }
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, env=env
    )
    return done.returncode, done.stdout


def _committed_edit_case() -> list[str]:
    """The case a static fixture tree cannot carry: an edit that is COMMITTED.

    A declared baseline of `HEAD` is resolved per run, so a spec edited and then
    committed is byte-identical to the baseline the gate compares against, and
    the assertion passes. That is not a hypothetical -- it was the declared value
    until harden-vault-harness task 2.5, while four tasks across two changes
    offered this gate as the whole mitigation for "the sixteen specs are not
    edited". The window it guarded was the one moment the edit had not landed.

    This builds the scenario twice against one repository: pinned to the baseline
    commit, where the committed edit must fail, and against `HEAD`, where it must
    pass. The second assertion records the defect rather than trusting a sentence
    about it, so a future change back to a moving ref is caught by a test that
    already knows what that costs.
    """
    import contextlib
    import io

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        specs = [
            f"{SPEC_SET_ROOT}/cap{n:02d}/spec.md" for n in range(EXPECTED_SPEC_FILES)
        ]
        for rel in specs:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# spec\n\nbaseline line one\n", encoding="utf-8")
        (root / "ci").mkdir(parents=True, exist_ok=True)

        def manifest(baseline: str) -> None:
            (root / "ci" / "vault.json").write_text(
                _SELF_TEST_MANIFEST
                % {
                    "prefix": SPEC_SET_ROOT,
                    "owner": _SELF_TEST_OWNER,
                    "baseline": baseline,
                },
                encoding="utf-8",
            )

        manifest("HEAD")
        for args in (
            ["init", "-q"],
            ["add", "-A"],
            [
                "-c",
                "user.name=gate",
                "-c",
                "user.email=gate@invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-q",
                "-m",
                "baseline",
            ],
        ):
            code, _ = _git_quiet(root, *args)
            if code != 0:
                return [f"could not build the committed-edit scenario: git {args[0]}"]
        code, out = _git_quiet(root, "rev-parse", "HEAD")
        if code != 0:
            return ["could not resolve the baseline commit"]
        baseline_sha = out.decode().strip()

        # The edit, and then the commit that hides it from a moving baseline.
        edited = root / specs[2]
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nA tenant key MUST be forgeable.\n",
            encoding="utf-8",
        )
        for args in (
            ["add", "-A"],
            [
                "-c",
                "user.name=gate",
                "-c",
                "user.email=gate@invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-q",
                "-m",
                "edit a frozen spec",
            ],
        ):
            code, _ = _git_quiet(root, *args)
            if code != 0:
                return ["could not commit the planted edit"]

        for baseline, label, want_fail in (
            (baseline_sha, "a pinned baseline", True),
            ("HEAD", "a moving baseline", False),
        ):
            manifest(baseline)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                got = run(root, False)
            output = buffer.getvalue()
            if want_fail:
                if got != 1:
                    problems.append(
                        f"a committed edit to a frozen spec passed under {label} "
                        f"(exit {got}) -- pinning the baseline is what makes the "
                        f"byte-unchanged assertion true of history"
                    )
                elif specs[2] not in output:
                    problems.append(
                        f"the failure under {label} does not name the edited path {specs[2]}"
                    )
            elif got == 1:
                problems.append(
                    f"a committed edit FAILED under {label}, so this case no longer "
                    f"records why a fixed baseline is required -- if the gate has "
                    f"stopped resolving the ref per run, delete this assertion and "
                    f"say so"
                )
    return problems


def _self_test() -> int:
    import contextlib
    import io

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        (root / "ci").mkdir(parents=True)
        (root / "ci" / "vault.json").write_text(
            _SELF_TEST_MANIFEST
            % {"prefix": SPEC_SET_ROOT, "owner": _SELF_TEST_OWNER, "baseline": "HEAD"},
            encoding="utf-8",
        )
        # The set must cover exactly sixteen spec.md files, so the only failure
        # the planted modification can produce is the byte change itself.
        specs = [
            f"{SPEC_SET_ROOT}/cap{n:02d}/spec.md" for n in range(EXPECTED_SPEC_FILES)
        ]
        for rel in specs:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "# spec\n\nbaseline line one\nbaseline line two\n", encoding="utf-8"
            )

        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        }
        for args in (
            ["init", "-q"],
            ["add", "-A"],
            [
                "-c",
                "user.name=gate",
                "-c",
                "user.email=gate@invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-q",
                "-m",
                "baseline",
            ],
        ):
            done = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                check=False,
                env=env,
            )
            if done.returncode != 0:
                print(
                    f"[FAIL] {GATE_ID} --self-test: could not build the scenario: "
                    f"git {' '.join(args)} -> {done.stderr.decode().strip()}"
                )
                return 1

        # One byte, on a path the set covers, exactly as task 1.12 prescribes --
        # plus the two other shapes a coherence pass produces: a path removed
        # from the set, and a path added to it.
        planted = root / specs[3]
        planted.write_text(
            planted.read_text(encoding="utf-8").replace("one", "onE"), encoding="utf-8"
        )
        (root / specs[7]).unlink()
        stray = root / SPEC_SET_ROOT / "cap00" / "notes.md"
        stray.write_text("added by a coherence pass\n", encoding="utf-8")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = run(root, False)
        output = buffer.getvalue()

        problems = []
        if code != 1:
            problems.append(f"expected exit 1 on the planted modification, got {code}")
        for label, needle in (
            ("the modified path", specs[3]),
            ("the deleted path", specs[7]),
            ("the untracked addition", f"{SPEC_SET_ROOT}/cap00/notes.md"),
        ):
            if needle not in output:
                problems.append(f"failure output does not name {label} {needle}")
        if "first change at line 3" not in output:
            problems.append("failure output does not name the line the change lands on")
        if _SELF_TEST_OWNER not in output:
            problems.append(
                f"failure output does not name the declaring change {_SELF_TEST_OWNER}"
            )
        if f"{EXPECTED_SPEC_FILES}/{EXPECTED_SPEC_FILES}" not in output:
            problems.append("coverage line does not state the sixteen specifications")

        # The fourth shape, which needs its own repository because it needs a
        # second commit: an edit that is committed rather than left in the tree.
        problems.extend(_committed_edit_case())

        print(output, end="")
        if problems:
            print(f"[FAIL] {GATE_ID} --self-test: {len(problems)} problem(s)")
            for problem in problems:
                print(f"  - {problem}")
            print(f"  rule: {RULE_NOTE}")
            return 1
        print(
            f"[ok] {GATE_ID} --self-test: a one-byte change, a deletion and an "
            f"untracked addition under '{SPEC_SET_ROOT}' each fail, naming the "
            f"path, its line, and {_SELF_TEST_OWNER}; and a COMMITTED edit fails "
            f"against a pinned baseline while passing against a moving one"
        )
        return 0


if "--self-test" in sys.argv[1:]:
    sys.exit(_self_test())

main_guard(run)
