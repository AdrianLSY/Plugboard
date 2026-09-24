#!/usr/bin/env python3
"""Gate: every note carries a classification, and the spine claims no normative authority.

Enforces docs/knowledge-base -- "Every note carries a classification":

  * a note under the spine or a per-component root declares `type`, `status`
    and `authority`; a note with no frontmatter, or frontmatter missing any of
    them, fails with EVERY missing field named in ONE failure line -- not one
    line per field, because the contributor fixes the note once;
  * each value comes from a closed enumeration held in ci/vault.json, the one
    retrievable location; a value outside it fails naming the value AND the
    permitted set;
  * the note-class -> value assignment table in that same location is checked
    for completeness, so a note class the change creates with no assigned value
    is a failure rather than a judgement call at authoring time;
  * a field outside the declared set fails -- see the caveat below;
  * (task 1.7) a note in the spine declaring `authority: normative` fails. The
    spine holds rationale; normative behaviour is owned by a specification, and
    a spine note that claims it has quietly become a second source of truth.

Scope is the spine and the per-component roots ONLY. The declared planning
directories are out of scope with the reason recorded in ci/vault.json: an
external tool authors and validates their format. So a planning artifact
carrying no frontmatter does not fail HERE, while the link and reachability
gates still cover it. Every run reports that exclusion, so a passing run states
its coverage rather than implying it covered the tree.

CAVEAT, stated plainly because the requirement's words are stronger than any
check can be: "a field no gate and no index generator reads" is enforced here
as "a field outside `classification.required_fields`" -- a DECLARED permitted
set, not an analysis of what code actually reads. A key admitted to that list
and then read by nothing would pass this gate. The declaration is the artifact
under review; task 6.3's rule-to-gate correspondence check is what keeps the
declaration honest.

The note-class table is intentionally empty in ci/vault.json until task 3.0
populates it. The completeness check therefore passes vacuously today and
starts biting the moment a class appears -- written now, on purpose, so that
task 3.0 is landing values into a check that already exists rather than
inventing the check afterwards to describe whatever it happened to write.

Frontmatter is parsed by the strict reader below rather than by a YAML library:
these gates are standard-library only, and the vault's frontmatter is a flat
scalar mapping. Anything richer is refused as malformed with its line named,
which is the correct answer for a classification block regardless.
"""

from __future__ import annotations

from pathlib import Path

from _common import (
    Report,
    candidates,
    exempt_roots,
    governed_roots,
    load_manifest,
    main_guard,
    notes,
    repo_root,
    scan_excludes,
)

GATE_ID = "frontmatter"
RULE_NOTE = "docs/method/rules/note-classification.md"

DELIMITER = "---"


# --------------------------------------------------------------------------
# Manifest resolution
# --------------------------------------------------------------------------
def resolve_manifest(scan_root: Path) -> tuple[dict, Path, str]:
    """The manifest belonging to the tree being scanned: (manifest, file, label).

    A real run reads ci/vault.json at the repository root. A fixture tree is a
    miniature repository, so if it carries its own ci/vault.json that is the
    declared location for that tree. This is not a convenience: two of this
    gate's obligations -- the note-class completeness check and the closed
    enumerations -- have their subject IN the manifest, not in the tree, so a
    violating input for them can only be a violating manifest. Without this the
    completeness check would be unexercisable and would ship untested.

    `label` is what a failure prints, relative to whichever tree owns it.
    """
    local = scan_root / "ci" / "vault.json"
    if local.is_file():
        return load_manifest(scan_root), local, "ci/vault.json"
    root = repo_root()
    return load_manifest(root), root / "ci" / "vault.json", "ci/vault.json"


def manifest_line(manifest_file: Path, needle: str) -> int:
    """1-based line in the manifest holding `needle`, or 0 if not found.

    The requirement asks a failure to name the path and line where it applies;
    for a manifest-level failure that line is in ci/vault.json.
    """
    try:
        text = manifest_file.read_text(encoding="utf-8")
    except OSError:
        return 0
    for number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return number
    return 0


# --------------------------------------------------------------------------
# Strict frontmatter reader
# --------------------------------------------------------------------------
class Malformed(Exception):
    """A frontmatter block that is present but not a flat scalar mapping.

    Carries the 1-based line so the failure names where to look.
    """

    def __init__(self, line: int, message: str) -> None:
        super().__init__(message)
        self.line = line
        self.message = message


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def read_frontmatter(text: str) -> tuple[dict[str, tuple[str, int]], bool]:
    """Parse a leading `---` delimited block.

    Returns ({key: (value, line)}, present). `present` is False when the file
    does not open with a delimiter at all -- that is "no frontmatter", a
    different failure from a malformed block, and the two are reported apart.

    Raises Malformed for: an unterminated block, a line that is not `key:
    value`, a duplicate key, an empty key, and a block value (a list item or a
    nested mapping), which a classification field may not be.
    """
    lines = text.split("\n")
    if lines and lines[0].startswith("﻿"):
        lines[0] = lines[0][1:]
    if not lines or lines[0].strip() != DELIMITER:
        return {}, False

    fields: dict[str, tuple[str, int]] = {}
    for offset, raw in enumerate(lines[1:], start=2):
        stripped = raw.strip()
        if stripped == DELIMITER:
            return fields, True
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            raise Malformed(
                offset,
                f"list value not permitted in a classification block: {stripped!r}"
                " -- a relation belongs in the note body as a relative markdown link",
            )
        if raw[:1] != raw[:1].strip():
            raise Malformed(
                offset,
                f"indented line {stripped!r} -- a classification block is a flat"
                " scalar mapping; nested mappings and block values are refused",
            )
        if ":" not in stripped:
            raise Malformed(offset, f"expected 'key: value', got {stripped!r}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = _unquote(value.strip())
        if not key:
            raise Malformed(offset, f"empty key in {stripped!r}")
        if not value:
            raise Malformed(
                offset,
                f"key {key!r} has no value -- a required field with an empty value"
                " is not a declaration",
            )
        if key in fields:
            raise Malformed(
                offset,
                f"duplicate key {key!r} (first declared on line {fields[key][1]})",
            )
        fields[key] = (value, offset)

    raise Malformed(1, "opening '---' with no closing '---'")


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def check_note_classes(
    manifest: dict, manifest_file: Path, label: str, report: Report
) -> int:
    """Every declared note class assigns each required field a value the enumeration holds.

    Passes vacuously while the table is empty (its state until task 3.0). A
    class present with a field missing, or with a value the enumeration does
    not hold, fails naming the class and the field -- the value that is not in
    the enumeration IS a field with no assigned value, since only enumerated
    values are values.
    """
    classification = manifest["classification"]
    required = list(classification["required_fields"])
    enumerations = classification["enumerations"]
    table = classification.get("note_classes", {})

    checked = 0
    for note_class in sorted(k for k in table if not k.startswith("_")):
        assigned = table[note_class]
        checked += 1
        line = manifest_line(manifest_file, f'"{note_class}"')
        located = f"{label}:{line}" if line else label
        if not isinstance(assigned, dict):
            report.fail(
                f"{located}: note class '{note_class}' assigns no field values at all"
                f" -- it must assign every one of: {', '.join(required)}"
            )
            continue
        unassigned = []
        for field in required:
            value = assigned.get(field)
            if value is None or value == "":
                unassigned.append(f"{field} (absent)")
            elif value not in enumerations[field]:
                unassigned.append(
                    f"{field} (value {value!r} is outside its enumeration)"
                )
        if unassigned:
            # One line per class: the class is what gets fixed, so every field
            # it leaves unassigned is named together.
            report.fail(
                f"{located}: note class '{note_class}' has no assigned value for"
                f" field(s): {', '.join(unassigned)}"
                " -- a note class with no assigned value is a failure, not a"
                " judgement call at authoring time"
            )
    return checked


def check_note(
    rel: str, text: str, manifest: dict, in_spine: bool, report: Report
) -> None:
    """Every classification obligation that applies to one note."""
    classification = manifest["classification"]
    required = list(classification["required_fields"])
    enumerations = classification["enumerations"]
    forbidden_in_spine = set(classification.get("spine_forbidden_authority", []))
    permitted_keys = set(required)

    try:
        fields, present = read_frontmatter(text)
    except Malformed as bad:
        report.fail(f"{rel}:{bad.line}: malformed frontmatter -- {bad.message}")
        return

    if not present:
        # Distinct from "missing a field": the block itself is absent. Every
        # required field is named anyway, so the fix is one edit.
        report.fail(
            f"{rel}:1: no frontmatter block -- a note must open with a '{DELIMITER}'"
            f" delimited block declaring every required field:"
            f" {', '.join(sorted(required))}"
        )
        return

    missing = sorted(field for field in required if field not in fields)
    if missing:
        # ONE failure naming every missing field at once. The requirement says
        # "names the note and every missing field at once"; two lines would
        # invite fixing one and re-running.
        report.fail(
            f"{rel}:1: missing required field(s): {', '.join(missing)}"
            f" (required: {', '.join(sorted(required))})"
        )

    for key in sorted(fields):
        value, line = fields[key]
        if key not in permitted_keys:
            report.fail(
                f"{rel}:{line}: field '{key}' is read by no gate and no index"
                f" generator -- the classification is limited to the declared set:"
                f" {', '.join(sorted(permitted_keys))}"
            )
            continue
        permitted = enumerations[key]
        if value not in permitted:
            report.fail(
                f"{rel}:{line}: field '{key}' value {value!r} is outside its"
                f" enumeration -- permitted: {', '.join(permitted)}"
            )
            continue
        if key == "authority" and in_spine and value in forbidden_in_spine:
            # Task 1.7. Reached only for an enumerated value, so the message is
            # about authority rather than about spelling.
            report.fail(
                f"{rel}:{line}: field 'authority' value {value!r} is forbidden in"
                f" the spine '{manifest['spine']}' -- a spine note may not declare"
                f" normative authority; the owning specification does. Permitted"
                f" here: {', '.join(v for v in permitted if v not in forbidden_in_spine)}"
            )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def run(scan_root: Path, report_only: bool) -> int:
    manifest, manifest_file, manifest_label = resolve_manifest(scan_root)
    report = Report(GATE_ID, RULE_NOTE)

    spine = manifest["spine"]
    directories, root_files = governed_roots(manifest)
    planning = list(manifest["classification"]["planning_directories"])
    governed_scopes = tuple(manifest["classification"]["governed_scopes"])

    subjects = notes(scan_root, manifest, scopes=governed_scopes)
    _all_candidates, from_index = candidates(scan_root, manifest)

    for rel in sorted(subjects):
        path = scan_root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as err:
            report.fail(f"{rel}: unreadable -- {err}")
            continue
        except UnicodeDecodeError as err:
            report.fail(f"{rel}: not valid UTF-8 -- {err}")
            continue
        top = rel.split("/", 1)[0]
        check_note(rel, text, manifest, in_spine=(top == spine), report=report)

    classes_checked = check_note_classes(
        manifest, manifest_file, manifest_label, report
    )

    covered = [d for d in directories if d not in planning]
    for _subject in subjects:
        report.examine(_subject)
    report.coverage(
        covered=covered,
        excluded=[
            *(f"{d} (planning: format owned by an external tool)" for d in planning),
            *(f"{r} (exempt root)" for r in exempt_roots(manifest)),
            *(f"{r} (scan exclusion)" for r in scan_excludes(manifest)),
            *(
                f"{f} (entry file: out of this gate's scope)"
                for f in sorted(root_files)
            ),
        ],
        kind="note",
        source="index" if from_index else "scan",
        scan_root=scan_root,
    )
    # A gate that passed by covering nothing must be distinguishable from one
    # that passed by being satisfied (task 3.11).
    print(
        f"  accounting: notes classified={len(subjects)} "
        f"note classes checked={classes_checked} "
        f"enumeration source={manifest_label}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
