"""Shared helpers for the vault gates. Standard library only.

Two properties of this module are load-bearing, and both come from
docs/knowledge-base -- "The repository is one vault with one spine":

1. A gate's subject is the TRACKED set, because the rules are written about
   tracked files. So candidates come from the version-control index, not from a
   filesystem walk. An untracked scratch file must not fail a gate about tracked
   files, and a tracked file must not escape one by living where a walk does not
   look.

2. A gate never decides its own scope. Every root is declared governed or
   exempt in ci/vault.json, the declared set is closed, and each gate reports
   the roots it excluded even when it passes -- so a green run states its own
   coverage instead of implying total coverage.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

MANIFEST_NAME = "vault.json"


def repo_root(start: Path | None = None) -> Path:
    """Walk upward to the directory holding ci/vault.json."""
    here = (start or Path(__file__).resolve()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "ci" / MANIFEST_NAME).is_file():
            return candidate
    raise SystemExit(f"could not locate ci/{MANIFEST_NAME} above {here}")


def load_manifest(root: Path | None = None) -> dict:
    with ((root or repo_root()) / "ci" / MANIFEST_NAME).open(encoding="utf-8") as handle:
        return json.load(handle)


def _keys(section: dict) -> list[str]:
    """Manifest sections carry a `_comment`; it is documentation, not an entry."""
    return sorted(k for k in section if not k.startswith("_"))


def governed_roots(manifest: dict) -> tuple[list[str], set[str]]:
    roots = manifest["note_roots"]
    return list(roots["directories"]), set(roots["root_files"])


def exempt_roots(manifest: dict) -> list[str]:
    return _keys(manifest.get("exempt_roots", {}))


def scan_excludes(manifest: dict) -> list[str]:
    return _keys(manifest.get("scan_excludes", {}))


def _under(rel: str, root: str) -> bool:
    return rel == root or rel.startswith(root + "/")


def classify(rel: str, manifest: dict) -> tuple[str, str]:
    """Return (verdict, root) where verdict is governed / exempt / excluded / undeclared."""
    directories, root_files = governed_roots(manifest)
    for root in exempt_roots(manifest):
        if _under(rel, root):
            return "exempt", root
    for root in scan_excludes(manifest):
        if _under(rel, root):
            return "excluded", root
    if "/" not in rel:
        return ("governed", rel) if rel in root_files else ("undeclared", rel)
    for root in directories:
        if _under(rel, root):
            return "governed", root
    return "undeclared", rel.split("/", 1)[0]


def tracked_markdown(root: Path) -> list[str] | None:
    """Every tracked .md path relative to `root`, or None if `root` is not a work tree.

    None is the signal a fixture tree gives: ci/broken-inputs/<gate>/tree is
    deliberately untracked, so a gate run with --root against one treats every
    file it finds as in scope. That is what a fixture means, and stating it here
    keeps the fallback from looking like a bug in the real run.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
            capture_output=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not (root / ".git").exists() and not _in_worktree(root):
        return None
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def _in_worktree(root: Path) -> bool:
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
        ).stdout.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return Path(top).resolve() == root.resolve()


def on_tracked_tree(scan_root: Path) -> bool:
    """True only for the run the aggregating target makes with no tree argument.

    Some checks are about the REPOSITORY -- a declaration that has outlived its
    reason, a declared generator's existence, a gate's subject set being empty.
    A violating input is deliberately partial and carries none of that context,
    so applying such a check to one produces a failure that is not a defect.
    Three gates learned this separately (component_boundaries, index_drift,
    out_of_scope), each by making its own fixture emit a count its note did not
    declare, which is why it is a named helper rather than a line to remember.
    """
    return scan_root.resolve() == repo_root().resolve()


def subject_source(root: Path) -> str:
    """"index" when `root` is a work tree, otherwise "scan".

    A gate should not decide this by hand. Five hardcoded "the tracked index"
    and reported it while walking a fixture tree; six hardcoded the opposite and
    reported a fixture tree while reading the repository's index.
    """
    return "index" if _in_worktree(root) else "scan"


def walk_markdown(root: Path) -> list[str]:
    """Every .md file on disk under `root`, relative and sorted. Fixture trees only."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        rel_dir = Path(dirpath).relative_to(root)
        for name in sorted(filenames):
            if name.endswith(".md"):
                found.append((rel_dir / name).as_posix())
    return sorted(found)


def candidates(root: Path, manifest: dict) -> tuple[list[str], bool]:
    """(paths, from_index). Tracked set for a work tree; everything for a fixture."""
    tracked = tracked_markdown(root)
    if tracked is None:
        return walk_markdown(root), False
    return tracked, True


def notes(root: Path, manifest: dict, scopes: tuple[str, ...] = ()) -> list[str]:
    """Governed, non-excluded candidates, optionally narrowed to given scopes.

    scopes: "spine", "components", "planning". Empty means every governed root.
    """
    paths, _ = candidates(root, manifest)
    spine = manifest["spine"]
    planning = set(manifest["classification"]["planning_directories"])
    _, root_files = governed_roots(manifest)
    out = []
    for rel in paths:
        verdict, _root = classify(rel, manifest)
        if verdict != "governed":
            continue
        if scopes:
            top = rel.split("/", 1)[0]
            in_spine = top == spine
            in_planning = top in planning
            in_components = not in_spine and not in_planning and rel not in root_files
            keep = (
                ("spine" in scopes and in_spine)
                or ("planning" in scopes and in_planning)
                or ("components" in scopes and in_components)
                or ("entry" in scopes and rel in root_files)
            )
            if not keep:
                continue
        out.append(rel)
    return out


class Report:
    """Collects every failure so a gate reports all of them in one run.

    docs/knowledge-base requires the link gate to report every unresolved link
    rather than stopping at the first; every gate uses the same shape so a
    contributor fixes a class of problem in one pass. It also carries the
    coverage line, so a passing gate says what it covered and what it skipped.
    """

    # Where a gate's subject set came from. Three values, not two: at least six
    # gates take their set from a named key in ci/vault.json and are neither the
    # version-control index nor a directory walk. Offered only the first two,
    # such a gate must report something false -- and the coverage rule would
    # then fail it for the report it was forced into.
    SOURCES = {
        "index": "tracked index",
        "scan": "a directory scan",
        "manifest": "a declared key in ci/vault.json",
    }

    def __init__(self, gate_id: str, rule_note: str) -> None:
        self.gate_id = gate_id
        self.rule_note = rule_note
        self.failures: list[str] = []
        self.covered: list[str] = []
        self.excluded: list[str] = []
        self.kind = "file"
        self.source = "index"
        self._subjects: set[str] = set()
        self._source_note: str | None = None

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def examine(self, subject) -> None:
        """Register one subject as examined.

        The reported count is derived from these rather than handed over as a
        literal, because a literal is an assertion nothing checks -- twelve gates
        passed one, and six of them named a source they had not used. A gate that
        fails about an item it never registered is reporting a reach it does not
        have, which the coverage rule treats as a failure.
        """
        self._subjects.add(str(subject))

    @property
    def subject_count(self) -> int:
        return len(self._subjects)

    def coverage(self, *, covered, excluded, kind="file", source, scan_root=None) -> None:
        if source not in self.SOURCES:
            raise SystemExit(
                f"{self.gate_id}: coverage source {source!r} is not one of "
                f"{sorted(self.SOURCES)}"
            )
        self.covered = sorted(covered)
        self.excluded = sorted(excluded)
        self.kind = kind
        self.source = source
        # A run whose scan root is not a work tree cannot have read its set from
        # version control. This is the one half of the source claim that is
        # decidable without an oracle, so it is the half the build checks.
        if source == "index" and scan_root is not None and not _in_worktree(Path(scan_root)):
            self.fail(
                f"{self.gate_id}: reports its subjects came from version control, but "
                f"'{scan_root}' is not a work tree -- a coverage line naming a source "
                f"the run did not use is narrative, not an assertion"
            )

    def _coverage_line(self) -> str:
        noun = self.kind if self.subject_count == 1 else f"{self.kind}s"
        return (
            f"  coverage: {self.subject_count} {noun} from {self.SOURCES[self.source]}"
            f" | covered: {', '.join(self.covered) or '-'}"
            f" | excluded: {', '.join(self.excluded) or '-'}"
        )

    def finish(self, *, report_only: bool = False) -> int:
        if not self.failures:
            print(f"[ok] {self.gate_id}: no violations")
            print(self._coverage_line())
            return 0
        label = "warn" if report_only else "FAIL"
        print(f"[{label}] {self.gate_id}: {len(self.failures)} violation(s)")
        for failure in self.failures:
            print(f"  - {failure}")
        print(self._coverage_line())
        # docs/code-standards: a gate's failure output names its rule note, so
        # the contributor who trips it is handed the rule rather than a verdict.
        print(f"  rule: {self.rule_note}")
        return 0 if report_only else 1


def parse_args(argv: list[str]) -> tuple[Path, bool]:
    """Every gate takes --root (default: the repository) and --report-only.

    --root is what lets a gate run against a miniature violating-input tree
    under ci/broken-inputs/, which is how the meta-check proves it fails.
    """
    scan_root: Path | None = None
    report_only = False
    rest = list(argv)
    while rest:
        arg = rest.pop(0)
        if arg == "--root":
            if not rest:
                raise SystemExit("--root requires a path")
            scan_root = Path(rest.pop(0)).resolve()
        elif arg == "--report-only":
            report_only = True
        else:
            raise SystemExit(f"unknown argument: {arg}")
    return (scan_root or repo_root()), report_only


def main_guard(fn) -> None:
    sys.exit(fn(*parse_args(sys.argv[1:])))


# The rule set has two consumers -- ci/gates/rule_gate_correspondence.py holds it
# against the gates, ci/gen/rule_index.py publishes it as a table -- and for a
# while they resolved it separately. The generator walked the rule directories
# only; the gate additionally held any note a gate's RULE_NOTE named. One run of
# `make check` printed "42 rules" and "rule notes: 43" over the same set, and the
# member missing from the published side was docs/method/authority-precedence.md,
# a gated rule absent from the index CLAUDE.md routes every reader to. So the
# resolver lives here, where both may legally import it, and a divergence
# between the two is no longer possible by construction.
RULE_NOTE_DECL = re.compile(r'^RULE_NOTE\s*=\s*"([^"]+)"', re.M)


def rule_notes(root: Path, cfg: dict) -> dict[str, Path]:
    """Every rule note: those under the declared rule directories, plus any note
    a gate names. A rule note living outside those directories -- the canonical
    authority precedence sits in docs/method/ because the spine is where it
    belongs -- is still held to the correspondence rather than escaping it by
    location, and is still published."""
    found: dict[str, Path] = {}
    for d in cfg["rule_dirs"]:
        for p in sorted((root / d).rglob("*.md")):
            if p.name == "index.md":
                continue
            found[p.relative_to(root).as_posix()] = p
    for gate in sorted((root / "ci" / "gates").glob("*.py")):
        m = RULE_NOTE_DECL.search(gate.read_text(encoding="utf-8"))
        if not m:
            continue
        rel = m.group(1).split("#")[0]
        if rel not in found and (root / rel).is_file():
            found[rel] = root / rel
    return found
