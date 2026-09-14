#!/usr/bin/env python3
"""Gate: ten identical non-comment lines in two places is a duplication failure.

Enforces docs/code/rules/duplication-threshold.md. rebuild-plugboard task 3.6.

Two passes, and the second is the one the rule asks for:

  1. VERBATIM -- ten consecutive non-comment lines, whitespace-collapsed,
     appearing at two locations.
  2. RENAMED -- the same windows with every identifier replaced by a placeholder,
     so keywords, operators and punctuation remain. The rule says "whether or not
     identifiers were renamed between them", and a copy with `mount` swapped for
     `hook` throughout is invisible to the first pass. `MountStore` and
     `HookStore` were the same GenServer twice: 128 of hook_store.ex's 199
     non-comment lines appeared verbatim in mount_store.ex, and domain affinities
     were then bolted INSIDE MountStore because there was no third slot.

Two locations in ONE file count, which is deliberate: a block pasted twice inside
a module is the same defect with a shorter commute.

## The price of the second pass, stated

Blanking identifiers can match two blocks that share only a shape -- ten lines of
struct fields, a decision table, or the import block and `func main` opening that
Go requires of every command. That is a false positive, and it is the cost of
catching a rename.

Saying so "in review" is not a record. A judgement made once in a pull request is
invisible to the next reader and to the next run, so the gate stayed red or the
window got widened, and widening is how a threshold dies. A shape collision is
therefore DECLARED, in ci/vault.json, naming both files and the reason -- and the
declaration is held in BOTH directions: a declared pair that has stopped colliding
fails as stale, so an exemption cannot outlive the shape that earned it.

Only the renamed pass can be declared. A verbatim copy is never a shape.

## What it does not decide

A paraphrase: the same logic written differently. Nothing over text finds that.
Requirement TEXT duplicated between the spine and a specification is a different
rule and a different gate (ci/gates/duplication.py).
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, repo_root, subject_source
from _source import COMMENT, code_lines, config, sources

GATE_ID = "code-duplication"
RULE_NOTE = "docs/code/rules/duplication-threshold.md"

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SPACE = re.compile(r"\s+")
#: Words that carry meaning even when identifiers do not. Blanking these too
#: would make every ten-line block look like every other.
KEEP = {
    "func", "return", "if", "else", "for", "range", "var", "const", "type", "struct",
    "interface", "map", "chan", "go", "defer", "switch", "case", "default", "nil",
    "true", "false", "error", "string", "int", "byte", "def", "defp", "defmodule",
    "do", "end", "when", "with", "cond", "fn", "use", "alias", "import", "require",
}


def normalise(line: str) -> str:
    return SPACE.sub(" ", line).strip()


def blank(line: str) -> str:
    return IDENT.sub(lambda m: m.group(0) if m.group(0) in KEEP else "_", normalise(line))


#: A window has to carry some variety to be evidence of a copy. Ten consecutive
#: import lines blank to ten identical placeholders, and so does a run of struct
#: fields; matching those is matching the language, not a duplication.
MIN_DISTINCT = 3


def windows(lines: list[tuple[int, str]], size: int, shape):
    for i in range(0, max(0, len(lines) - size + 1)):
        chunk = lines[i:i + size]
        shaped = [shape(t) for _n, t in chunk]
        if len(set(shaped)) < MIN_DISTINCT:
            continue
        yield chunk[0][0], "\n".join(shaped)


def distinct_sites(sites: list[str], size: int) -> list[str]:
    """Sites that are not just the same region seen through an adjacent window.

    Overlapping windows over one block report each other, which is the block
    matching itself. Only the first of each overlapping run is kept.
    """
    kept: list[str] = []
    for site in sites:
        rel, _, line = site.rpartition(":")
        near = False
        for other in kept:
            orel, _, oline = other.rpartition(":")
            if orel == rel and abs(int(line) - int(oline)) < size:
                near = True
                break
        if not near:
            kept.append(site)
    return kept


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = config(manifest)
    size = cfg["duplicate_lines"]
    declared = {
        frozenset(e["sites"]): e
        for e in cfg.get("shape_collisions", []) if isinstance(e, dict)
    }
    #: How many colliding regions each declared pair is allowed. An exemption at
    #: file level would hide a REAL copy made between those two files later; a
    #: count means growth reopens the question.
    seen: dict[frozenset, int] = {}
    report = Report(GATE_ID, RULE_NOTE)

    files = sources(scan_root, cfg, manifest)
    verbatim: dict[str, list[str]] = {}
    renamed: dict[str, list[str]] = {}
    for rel in files:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        comment = COMMENT.get("." + rel.rsplit(".", 1)[-1], "#")
        lines = code_lines(path.read_text(encoding="utf-8", errors="replace"), comment)
        for start, key in windows(lines, size, normalise):
            verbatim.setdefault(key, []).append(f"{rel}:{start}")
        for start, key in windows(lines, size, blank):
            renamed.setdefault(key, []).append(f"{rel}:{start}")

    # One finding per duplicated REGION, not one per window. A copied block
    # twenty lines long contains eleven ten-line windows, and reporting each is
    # eleven lines about one defect -- which is how a gate's output stops being
    # read.
    kept: list[list[str]] = []
    for key, raw in sorted(verbatim.items()):
        sites = distinct_sites(raw, size)
        if len(sites) > 1 and not continues(kept, sites, size):
            kept.append(sites)
            report.fail(
                f"{sites[0]}: {size} identical non-comment lines also at "
                f"{', '.join(sites[1:])} -- one copy and a call, not two copies"
            )
    verbatim_regions = list(kept)
    for key, raw in sorted(renamed.items()):
        sites = distinct_sites(raw, size)
        if len(sites) > 1 and not continues(kept, sites, size) \
                and not _already(sites, verbatim_regions):
            kept.append(sites)
            pair = frozenset(s.rpartition(":")[0] for s in sites)
            if pair in declared:
                seen[pair] = seen.get(pair, 0) + 1
                if seen[pair] <= declared[pair]["regions"]:
                    continue
            report.fail(
                f"{sites[0]}: {size} lines identical to {', '.join(sites[1:])} once "
                f"identifiers are set aside -- a renamed copy is a copy. If the two "
                f"genuinely only share a shape, say so in review; widening the "
                f"window is not the remedy"
            )

    for pair, entry in sorted(declared.items(), key=lambda kv: sorted(kv[0])):
        # A declaration names files by path. A miniature violating-input tree
        # contains none of them, so there is nothing there to be stale about --
        # without this, every fixture under ci/broken-inputs/ trips this gate and
        # the meta-check rightly calls each of them ambiguous.
        if not all((scan_root / s).is_file() for s in pair):
            continue
        found, allowed = seen.get(pair, 0), entry["regions"]
        if found == allowed:
            continue
        names = " and ".join(sorted(pair))
        if found < allowed:
            report.fail(
                f"{names}: declared {allowed} colliding region(s), found {found} "
                f"-- the declaration outlived the shape that earned it. Reason "
                f"given was \"{entry['reason'][:60]}...\"; delete or lower it"
            )
        else:
            report.fail(
                f"{names}: declared {allowed} colliding region(s), found {found}. "
                f"The extra one is not covered by the declaration -- a shape was "
                f"exempted, and something has since been COPIED between these two"
            )

    report.coverage(
        covered=[f"windows of {size} non-comment lines, verbatim and identifier-blanked"],
        excluded=["a paraphrase: the same logic written differently"],
        kind="source file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  files: {len(files)} | windows: {len(verbatim)} verbatim, {len(renamed)} "
        f"identifier-blanked | threshold: {size} consecutive non-comment lines | "
        f"declared shape collisions: {sum(seen.values())}/"
        f"{sum(e['regions'] for e in declared.values())}"
    )
    return report.finish(report_only=report_only)


def continues(kept: list[list[str]], sites: list[str], size: int) -> bool:
    """True when these sites are the same region a kept finding already named.

    A window shifted by one line over the same copied block is the same finding.
    Same files, every site within `size` lines of the kept one in that file.
    """
    for prior in kept:
        if _same_region(prior, sites, size):
            return True
    return False


def _same_region(prior: list[str], sites: list[str], size: int) -> bool:
    by_file: dict[str, list[int]] = {}
    for site in prior:
        rel, _, line = site.rpartition(":")
        by_file.setdefault(rel, []).append(int(line))
    if {s.rpartition(":")[0] for s in sites} != set(by_file):
        return False
    for site in sites:
        rel, _, line = site.rpartition(":")
        if not any(abs(int(line) - p) < size for p in by_file[rel]):
            return False
    return True


def _already(sites: list[str], regions: list[list[str]]) -> bool:
    """True when the verbatim pass already covered these sites."""
    return any(set(sites) <= set(region) for region in regions)


main_guard(run)
