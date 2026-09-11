#!/usr/bin/env python3
"""Gate: a spine note summarising owned behaviour marks it and links the owner.

Enforces docs/knowledge-base -- "Authority precedence is stated and enforced":
a note may not state behaviour a specification owns; where it must summarise
owned behaviour for orientation it marks the summary as non-normative and links
the owning specification.

## The decidable form, and why the general one is not available

The requirement as written cannot be decided over arbitrary prose. "The proxy
retries once before giving up" is a behavioural claim; no deterministic check
over English finds it, and pretending otherwise would produce a gate that passes
while the property fails -- the exact shape of defect this repository exists to
avoid.

So this gate decides a narrower, real thing: **a spine note that reproduces a
specification's requirement title must link that specification.** A requirement
title is the specification's own name for one obligation, so a note carrying one
is unambiguously talking about owned behaviour, and the check names both the note
and the owner exactly as the requirement asks.

Two other decidable halves of the same requirement live elsewhere rather than
being duplicated here: the normative-modal prohibition is in
ci/gates/citations.py, and verbatim requirement text is in
ci/gates/duplication.py.

## Two structural exclusions, declared rather than discovered

**A generated index** reproduces requirement titles because it lists notes by
title. That is mechanical, not a claim, so generated files are excluded -- they
are already held to byte-identity with their generator.

**A rule note** whose heading IS the rule it enforces is naming its own rule, not
summarising someone else's behaviour. Requiring it to defer to a specification
would be requiring a rule to disclaim itself. The rule directories are therefore
excluded, and the correspondence they owe is checked by
ci/gates/rule_gate_correspondence.py instead.

Both were found by running this gate over the real tree: 64 hits, of which 58
were one of these two shapes. A gate that reports 58 structural matches to find 6
real ones gets disabled, and then the requirement has no enforcement at all.

## What it does not decide

Paraphrase. A note that restates a requirement in its own words, without using
its title, is invisible to all three checks. That residue is owned by review, by
the precedence rule every note states at its head, and by the concept-note
ceiling that makes a long paraphrase not fit. Naming the residue is the point:
a green run here is not evidence that no note states owned behaviour.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import Report, load_manifest, main_guard, notes, repo_root, subject_source

GATE_ID = "owned-behaviour"
RULE_NOTE = "docs/method/rules/no-owned-behaviour-in-the-spine.md"

REQ_TITLE = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$", re.M)
NON_NORMATIVE = re.compile(r"non-normative|orientation only|wins where", re.I)

# Titles this short or this generic would match incidentally.
MIN_WORDS = 5


def spec_requirements(root: Path, manifest: dict) -> dict[str, list[str]]:
    glob = manifest["capability_notes"]["spec_glob"]
    out: dict[str, list[str]] = {}
    for p in sorted(root.glob(glob)):
        rel = p.relative_to(root).as_posix()
        titles = [
            t for t in REQ_TITLE.findall(p.read_text(encoding="utf-8"))
            if len(t.split()) >= MIN_WORDS
        ]
        if titles:
            out[rel] = titles
    return out


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    reqs = spec_requirements(scan_root, manifest)
    report = Report(GATE_ID, RULE_NOTE)

    generated = {
        k for k in manifest.get("generated_files", {}) if not k.startswith("_")
    }
    rule_dirs = tuple(manifest["code_standards"]["rule_dirs"])

    checked = hits = 0
    for rel in notes(scan_root, manifest, scopes=("spine",)):
        path = scan_root / rel
        if not path.is_file():
            continue
        if rel in generated or rel.endswith("/index.md"):
            continue
        if any(rel.startswith(d + "/") for d in rule_dirs):
            continue
        checked += 1
        report.examine(rel)
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for spec_rel, titles in reqs.items():
            spec_name = spec_rel.rsplit("/", 3)
            cap = f"{spec_name[-3]}/{spec_name[-2]}" if len(spec_name) >= 3 else spec_rel
            for title in titles:
                if title.lower() not in lower:
                    continue
                hits += 1
                links_owner = spec_rel.rsplit("/", 1)[0] in text or cap in text
                if not links_owner:
                    report.fail(
                        f"{rel}: reproduces the requirement title \"{title}\" and "
                        f"does not link its owner -- that requirement belongs to "
                        f"`{cap}` ({spec_rel}); link it, or say it in your own words"
                    )
                elif not NON_NORMATIVE.search(text):
                    report.fail(
                        f"{rel}: reproduces the requirement title \"{title}\" owned "
                        f"by `{cap}` and marks no summary as non-normative -- add "
                        f"the deferral (\"the owning artifact wins where the two "
                        f"disagree\") or drop the title"
                    )

    report.coverage(
        covered=[manifest["spine"]],
        excluded=["generated indexes (mechanical, held to byte-identity)",
                  "rule notes (a rule names its own rule; see rule_gate_correspondence)",
                  "normative modals (ci/gates/citations.py)",
                  "verbatim requirement text (ci/gates/duplication.py)",
                  "paraphrase (undecidable; owned by review)"],
        kind="note",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  spine notes: {checked} | requirement titles across "
        f"{len(reqs)} specs: {sum(len(v) for v in reqs.values())} | "
        f"titles reproduced in the spine: {hits}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
