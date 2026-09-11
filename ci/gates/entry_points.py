#!/usr/bin/env python3
"""Gate: an entry file routes, stays small, and never names an absent artifact.

Enforces docs/knowledge-base -- "Entry points route rather than carry content":

  1. Each entry file is under the declared size ceiling.
  2. Each links into the vault, names at least one invariant and at least one
     banned pattern, and does not restate framework or language conventions.
  3. No entry file instructs a reader to use a generated index, tool or
     directory the repository does not contain.

## The third case is not hypothetical

Before this gate existed, `CLAUDE.md` instructed every agent to prefer
`graphify query` over grep "when graphify-out/graph.json exists", described a
knowledge graph with god nodes and community structure, and told the reader to
navigate by `graphify-out/wiki/index.md`. None of it exists; no graph has ever
been generated in this repository. A hook in `.claude/settings.json` fired on the
same absent file.

That is roughly a kilobyte of the most-read file in the repository describing an
artifact that is not there -- in a file whose own plan caps it at 4 KB. An entry
file is the one place where a false claim is guaranteed to be read first, which
is why this check exists here rather than only in the currency gate.

## What it does not decide

Whether the invariant an entry file names is the *right* one, or whether its
routing is good. It decides presence, size, and that nothing named is absent.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root

GATE_ID = "entry-points"
RULE_NOTE = "docs/method/rules/entry-files-route.md"

FRAMEWORK = re.compile(
    r"^#+.*\b(conventions?|idioms?|style)\b.*\b(phoenix|elixir|go|golang|python|rails|django)\b",
    re.I | re.M,
)
LINK = re.compile(r"\]\(([^)]+)\)")
BACKTICK_PATH = re.compile(r"`([A-Za-z0-9_./-]+/[A-Za-z0-9_./-]+|[A-Za-z0-9_-]+/)`")


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["entry_files"]
    ceiling = cfg["ceiling_bytes"]
    report = Report(GATE_ID, RULE_NOTE)

    declared = [f for f in cfg["files"] if not f.startswith("_")]
    invariants = [s for s in cfg["invariant_markers"] if not s.startswith("_")]
    checked = 0

    for rel in declared:
        path = scan_root / rel
        if not path.is_file():
            report.fail(f"{rel}: declared entry file does not exist")
            continue
        checked += 1
        report.examine(rel)
        raw = path.read_bytes()
        text = raw.decode("utf-8")

        # (1) the ceiling
        if len(raw) > ceiling:
            report.fail(
                f"{rel}: {len(raw)} bytes, over the declared ceiling of {ceiling} "
                f"-- an entry file routes; it does not carry content"
            )

        # (2) routes, names an invariant, names a banned pattern
        links = [m.group(1) for m in LINK.finditer(text)]
        if not any(l.startswith("docs/") or "/docs/" in l or l.endswith(".md") for l in links):
            report.fail(f"{rel}: links into no note -- an entry file is a router")
        if not any(inv.lower() in text.lower() for inv in invariants):
            report.fail(
                f"{rel}: names none of the declared invariants "
                f"({', '.join(invariants)})"
            )
        if "banned" not in text.lower():
            report.fail(f"{rel}: names no banned pattern")
        m = FRAMEWORK.search(text)
        if m:
            report.fail(
                f"{rel}: restates framework or language conventions "
                f"({m.group(0).strip()[:60]!r}) -- a framework tutorial is not context"
            )

        # (3) nothing named that is absent
        for m2 in BACKTICK_PATH.finditer(text):
            cand = m2.group(1)
            if cand.startswith(("http", "-")) or " " in cand:
                continue
            root = cand.split("/", 1)[0]
            if root in {"docs", "ci", "openspec", "contract", "proxy", "sidecar",
                        "terminator", "conformance", "graphify-out", "reference"}:
                target = scan_root / cand.rstrip("/")
                if not target.exists() and root not in {"contract", "proxy", "sidecar",
                                                        "terminator", "conformance", "reference"}:
                    report.fail(
                        f"{rel}: names '{cand}', which the repository does not "
                        f"contain -- an entry file is read first, so a false claim "
                        f"here is the one guaranteed to be believed"
                    )

    report.coverage(
        covered=declared,
        excluded=["planned component directories (declared absent by design)"],
        kind="entry file",
        source="manifest",
        scan_root=scan_root,
    )
    sizes = ", ".join(
        f"{f}={(scan_root / f).stat().st_size}B" for f in declared if (scan_root / f).is_file()
    )
    print(f"  ceiling {ceiling}B | {sizes or 'no entry file exists'}")
    return report.finish(report_only=report_only)


main_guard(run)
