#!/usr/bin/env python3
"""Gate: a cited artifact is obtainable, and the spine does not state behaviour.

Enforces docs/knowledge-base -- "A cited artifact is obtainable" and the
enforceable half of "Authority precedence is stated and enforced".

## What this gate DECIDES

1. **Obtainability.** Every `path:line` citation in a note resolves either to a
   tracked file in this repository, or into an artifact declared in
   ci/vault.json's `cited_artifacts` -- which names the note stating how to
   obtain it and the revision the citations were taken against. A citation into
   an undeclared artifact fails, naming the artifact.

2. **The obtaining note exists and pins the revision.** A declared artifact
   whose obtaining note is missing, or which does not state the pinned revision,
   fails. Without this, "obtainable" is a promise rather than a property: 139
   citations pointed into a gitignored directory whose location was recorded
   nowhere, so no reader but the author could check a single one.

3. **The cited LINE exists.** A citation resolving to a tracked file whose line
   count is below the cited number fails, naming both. A path that resolves is
   not evidence the line does: a note citing `spec.md:402` against a 200-line
   file is as wrong as one citing a file that is gone, and only one of the two
   was ever detected.

4. **A present artifact is at the revision it was cited against.** Where a
   declared artifact is actually checked out, its `HEAD` is compared to the
   pinned revision and a mismatch fails, naming both. Declaring a revision and
   reading a different one is the failure mode a pin exists to prevent, and it
   is invisible to every other check here.

5. **An absent artifact makes its citations UNVERIFIABLE, not satisfied.** When a
   declared artifact is not present, every citation into it is counted as
   unverifiable and the count is printed. The run exits zero -- absence is the
   normal state of gitignored prior art, and failing on it would make the one
   command this repository tells a reader to run impossible to pass. What it must
   not do is report those citations as resolved, which is indistinguishable from
   having checked them.

6. **No normative modal in the spine.** A spine note may not state behaviour a
   specification owns. `SHALL`, `MUST`, `SHALL NOT` and friends are what make a
   sentence an obligation, so their presence in a spine note means the note is
   either restating a specification or inventing an obligation. Both are
   refused. Quotes, code spans and fenced blocks are exempt -- a note explaining
   the rule must be able to show the words.

## What this gate DOES NOT decide, stated so it is not mistaken for coverage

It cannot detect "a behavioural claim" in ordinary prose. A confident, plausible,
unsourced sentence written in the indicative -- "the proxy retries once before
giving up" -- is invisible to it, and no deterministic check over English will
find it. That failure mode is owned by review, by the requirement that a note
link the specification owning any behaviour it summarises, and by the
`Unverified` marker convention. This gate narrows the surface; it does not close
it, and a green run is not evidence that every claim in the vault is sourced.

The reason for saying so here rather than in a commit message: the prior art
carried 148 KB of prose containing two verifiably false documented claims, and
the lesson recorded was that a check whose limits are undocumented gets read as
a guarantee.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from _common import Report, load_manifest, main_guard, notes, repo_root, subject_source

GATE_ID = "citations"
RULE_NOTE = "docs/method/rules/citations.md"

# path/to/file.ext:123 or :123-456 -- a citation, not a link.
CITATION = re.compile(r"\b((?:[\w.-]+/)*[\w.-]+\.[A-Za-z][\w]*):(\d+)(?:-(\d+))?\b")
CODE_SPAN = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*```")
# A markdown link target -- excluded so a link is not read as a citation.
LINK = re.compile(r"\]\([^)]*\)")
# A citation of an external standard: quoting its normative language is legitimate.
STANDARD_REF = re.compile(r"\bRFC\s?\d+|\bdraft-[a-z0-9-]+|§")


def _keys(section: dict) -> list[str]:
    return [k for k in section if not k.startswith("_")]


def strip_for_modals(line: str) -> str:
    """Blank out code spans and link targets, preserving column count.

    Only the modal check uses this. The citation check must NOT: a citation is
    conventionally written inside backticks -- `endpoint.ex:118` -- so stripping
    code spans first made the obtainability check see zero citations in a tree
    holding roughly a hundred and fifty of them. A gate reporting "0 checked"
    while passing is worse than one that fails.
    """
    line = CODE_SPAN.sub(lambda m: " " * len(m.group(0)), line)
    return LINK.sub(lambda m: " " * len(m.group(0)), line)


def strip_for_citations(line: str) -> str:
    """Blank out only link targets -- a link is not a citation."""
    return LINK.sub(lambda m: " " * len(m.group(0)), line)


def read_lines(path: Path) -> list[tuple[int, str, bool]]:
    """(lineno, text, in_fence) for each line."""
    out, in_fence = [], False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            out.append((n, line, True))
            continue
        out.append((n, line, in_fence))
    return out


def paragraph_at(lines: list[tuple[int, str, bool]], n: int) -> str:
    """The blank-line-delimited paragraph containing line n."""
    idx = next((i for i, (ln, _t, _f) in enumerate(lines) if ln == n), None)
    if idx is None:
        return ""
    start = idx
    while start > 0 and lines[start - 1][1].strip():
        start -= 1
    end = idx
    while end + 1 < len(lines) and lines[end + 1][1].strip():
        end += 1
    return " ".join(t for _l, t, _f in lines[start : end + 1])


_LINE_COUNTS: dict[Path, int] = {}


def line_count(path: Path) -> int | None:
    """Lines in `path`, cached. None when it cannot be read as text."""
    if path not in _LINE_COUNTS:
        try:
            _LINE_COUNTS[path] = len(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError):
            return None
    return _LINE_COUNTS[path]


def revision_state(path: Path, pinned: str) -> tuple[str, str | None]:
    """(verdict, actual) for a declared artifact's checkout.

    Verdicts: `absent`, `not-a-checkout`, `match`, `mismatch`. The toplevel
    comparison matters because the prior art is gitignored INSIDE this
    repository: without it, `git -C reference/Plugboard rev-parse HEAD` answers
    with THIS repository's HEAD and every pin reads as a mismatch.
    """
    if not path.is_dir():
        return "absent", None
    try:
        top = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if Path(top).resolve() != path.resolve():
            return "not-a-checkout", None
        head = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "not-a-checkout", None
    return ("match" if head.startswith(pinned) else "mismatch"), head[
        : max(len(pinned), 7)
    ]


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    artifacts = {
        k: v
        for k, v in manifest.get("cited_artifacts", {}).items()
        if not k.startswith("_")
    }
    modals = manifest["normative_modals"]["words"]
    spine = manifest["spine"]
    prior_art_default = artifacts.pop("prior_art_default", None)
    report = Report(GATE_ID, RULE_NOTE)
    revision_verdicts: dict[str, str] = {}
    # Every subpath a declared artifact pins. Presence is decided per SUBPATH,
    # never per artifact: with reference/Plugboard cloned and reference/Telephone
    # not, `reference/` is a directory, and an artifact-level test would report
    # every Telephone citation as checkable against a tree that is not there.
    artifact_subpaths: list[str] = []

    # (2) each declared artifact's obtaining note exists and pins its revisions.
    for name, decl in artifacts.items():
        note_rel = decl.get("obtaining_note")
        if not note_rel:
            report.fail(f"cited artifact '{name}': declares no obtaining note")
            continue
        note_path = scan_root / note_rel
        if not note_path.is_file():
            report.fail(
                f"cited artifact '{name}': its obtaining note {note_rel} does not "
                f"exist, so every citation into it is checkable only by its author"
            )
            continue
        text = note_path.read_text(encoding="utf-8")
        for sub, rev in (decl.get("revisions") or {}).items():
            if rev not in text:
                report.fail(
                    f"{note_rel}: does not state the pinned revision '{rev}' for "
                    f"{sub} -- a reader cannot confirm they obtained what was cited"
                )
            # (4) declared AND present: the pin is checked, not trusted.
            verdict, actual = revision_state(scan_root / sub, rev)
            revision_verdicts[sub] = verdict
            if verdict == "mismatch":
                report.fail(
                    f"{sub}: checked out at {actual}, and the citations in this "
                    f"repository were taken against {rev} -- a pin nobody compares "
                    f"is a sentence, and every line number cited into this tree is "
                    f"measured against the wrong revision"
                )
            elif verdict == "not-a-checkout":
                report.fail(
                    f"{sub}: present and not a git checkout, so the pinned revision "
                    f"{rev} cannot be confirmed -- an unpinnable copy is worse than "
                    f"an absent one, because a reader believes they have what was cited"
                )
            artifact_subpaths.append(sub)

    subjects = notes(scan_root, manifest)
    note_paths: dict[str, list[str]] = {}
    for rel in subjects:
        note_paths.setdefault(rel.rsplit("/", 1)[-1], []).append(rel)
    basenames = set(note_paths)
    unqualified = 0
    # Where each citation resolved. Counted and PRINTED because ci/vault.json
    # states these figures in prose, and a number in prose with no command that
    # reproduces it is the class of claim this repository keeps getting wrong:
    # "139 citations point into reference/" was true of the pre-restructure tree
    # and was never recomputed.
    resolved = {"tracked": 0, "declared_artifact": 0, "unqualified_to_default": 0}
    # A citation into an artifact that is not here is UNVERIFIABLE, which is
    # neither resolved nor a failure. Counted separately and printed, because a
    # run that folded it into "resolved" would be claiming a check it did not do.
    unverifiable = {"artifact_absent": 0, "unqualified": 0, "line_ambiguous": 0}
    lines_checked = 0
    modal_re = re.compile(
        r"\b(" + "|".join(sorted(modals, key=len, reverse=True)) + r")\b"
    )
    cite_count = modal_count = 0

    for rel in subjects:
        path = scan_root / rel
        if not path.is_file():
            continue
        in_spine = rel == spine or rel.startswith(spine + "/")
        rel_lines = read_lines(path)
        for n, line, in_fence in rel_lines:
            if in_fence:
                continue
            # (1) obtainability of every citation -- code spans NOT stripped
            for m in CITATION.finditer(strip_for_citations(line)):
                target = m.group(1)
                cited_last = int(m.group(3) or m.group(2))
                cite_count += 1

                def check_line(
                    file_path: Path,
                    shown: str,
                    rel: str,
                    n: int,
                    m: re.Match[str],
                    cited_last: int,
                ) -> None:
                    """(3) the cited line exists in the cited file."""
                    nonlocal lines_checked
                    count = line_count(file_path)
                    if count is None:
                        return
                    lines_checked += 1
                    if cited_last > count:
                        report.fail(
                            f"{rel}:{n}: cites '{shown}:{m.group(2)}"
                            + (f"-{m.group(3)}" if m.group(3) else "")
                            + f"', and {shown} has {count} line(s) -- the path "
                            f"resolves and the line does not, which is the half "
                            f"of a citation a reader actually follows"
                        )

                if (scan_root / target).is_file():
                    resolved["tracked"] += 1
                    check_line(scan_root / target, target, rel, n, m, cited_last)
                    continue
                if "/" not in target:
                    # An unqualified citation: resolve by basename against the
                    # tracked set, else attribute it to the declared prior art.
                    # Weaker than a prefixed citation, and declared as such in
                    # ci/vault.json rather than silently accepted here.
                    if target in basenames:
                        unqualified += 1
                        resolved["tracked"] += 1
                        owners = note_paths[target]
                        if len(owners) == 1:
                            check_line(
                                scan_root / owners[0], owners[0], rel, n, m, cited_last
                            )
                        else:
                            unverifiable["line_ambiguous"] += 1
                        continue
                    if prior_art_default:
                        unqualified += 1
                        resolved["unqualified_to_default"] += 1
                        # An unqualified citation names no path, so no line of it
                        # is checkable even with the artifact in hand. Counted
                        # under its own head rather than folded into absence,
                        # because the two are fixed by different things: one by
                        # obtaining the artifact, the other by writing the prefix.
                        unverifiable["unqualified"] += 1
                        continue
                root = target.split("/", 1)[0]
                if root in artifacts:
                    resolved["declared_artifact"] += 1
                    path = scan_root / target
                    sub = next(
                        (k for k in artifact_subpaths if target.startswith(k + "/")),
                        None,
                    )
                    if path.is_file():
                        check_line(path, target, rel, n, m, cited_last)
                    elif sub and (scan_root / sub).is_dir():
                        report.fail(
                            f"{rel}:{n}: cites '{target}:{m.group(2)}', and {sub} is "
                            f"checked out without that path -- the artifact is here "
                            f"and the citation still does not resolve"
                        )
                    else:
                        unverifiable["artifact_absent"] += 1
                    continue
                report.fail(
                    f"{rel}:{n}: cites '{target}:{m.group(2)}' -- neither a tracked "
                    f"file nor an artifact declared obtainable in ci/vault.json "
                    f"(declared: {', '.join(sorted(artifacts)) or 'none'})"
                )

            # (3) no normative modal in the spine
            if in_spine:
                # Exempt: a blockquote, a line carrying a quotation mark, or a
                # line inside a paragraph that quotes an external standard. The
                # last case is why this is paragraph-scoped rather than
                # line-scoped -- RFC 9110's "a proxy MUST NOT change the order of
                # these field line values" wraps across two lines, and a
                # line-scoped exemption refused the second half of a quotation.
                para = paragraph_at(rel_lines, n)
                if (
                    line.lstrip().startswith(">")
                    or '"' in line
                    or '"' in para
                    or STANDARD_REF.search(para)
                ):
                    continue
                for m in modal_re.finditer(strip_for_modals(line)):
                    modal_count += 1
                    report.fail(
                        f"{rel}:{n}: uses the normative modal '{m.group(1)}' in the "
                        f"spine -- a note may not state behaviour a specification "
                        f"owns; link the owning specification instead of restating it"
                    )

    for _subject in subjects:
        report.examine(_subject)
    report.coverage(
        covered=[spine, *sorted(artifacts)],
        excluded=["fenced blocks", "code spans", "link targets", "quoted lines"],
        kind="note",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  citations checked: {cite_count} | declared artifacts: "
        f"{', '.join(sorted(artifacts)) or 'none'} | spine modal hits: {modal_count}"
    )
    print(
        f"  resolved: {resolved['tracked']} to a tracked file | "
        f"{resolved['declared_artifact']} into a declared artifact (prefixed) | "
        f"{resolved['unqualified_to_default']} unqualified, attributed to the declared prior art"
    )
    print(
        f"  verified: {lines_checked} cited line(s) exist in the file cited | "
        f"unverifiable: {unverifiable['artifact_absent']} into an absent artifact, "
        f"{unverifiable['unqualified']} written with no path prefix, "
        f"{unverifiable['line_ambiguous']} whose basename matches more than one note"
    )
    print(
        "  artifact revisions: "
        + (
            ", ".join(
                f"{sub}={verdict}" for sub, verdict in sorted(revision_verdicts.items())
            )
            or "none declared"
        )
    )
    print(
        "  NOT decided by this gate: an unsourced claim written in the indicative. "
        "Owned by review and by the Unverified convention."
    )
    return report.finish(report_only=report_only)


main_guard(run)
