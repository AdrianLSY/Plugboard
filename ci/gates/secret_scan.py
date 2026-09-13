#!/usr/bin/env python3
"""Gate: no credential in the working tree, and none in the range under review.

Enforces rebuild-plugboard task 3.15, in the half that is decidable today. Two
subjects, one detector:

  1. THE TRACKED WORKING TREE. Every tracked file that decodes as UTF-8 is read
     and every line is matched against a closed set of credential shapes.
  2. THE COMMIT RANGE UNDER REVIEW. Every blob added or modified by a commit in
     the range is read and matched the same way, MERGE COMMITS INCLUDED. A
     secret committed on Tuesday and deleted on Wednesday is absent from the
     tree and present in every clone of the branch, so a tree-only scan reports
     green over a disclosed credential. The range is the merge-base of a
     declared base ref with `HEAD`, or whatever `--range` names.

     A merge is read through its combined diff, which is the version the merge
     itself wrote where that version matches none of the parents -- a conflict
     resolution, or a value typed during one. What a parent changed is reached
     through that parent's own commit, which is in the range whenever the parent
     is. Skipping merges (`rev-list --no-merges`) left a credential a resolution
     introduced in no subject set at all, under a coverage line claiming every
     blob the range added or modified.

Five cases, all five failing:

  1. A credential-shaped literal in a tracked file, naming the path and line.
  2. The same in a blob the range introduced, naming the path, the line and the
     commit that introduced it -- reported whether or not the tree still holds
     it.
  3. A private-key block committed as a file.
  4. A password embedded in a URL's userinfo.
  5. A credential written by a merge commit's own resolution, belonging to none
     of that merge's parents.

## The trade this gate makes, stated because it is the whole design

It runs toward FALSE NEGATIVES. Every pattern is anchored on something an
issuer assigns -- `AKIA` for an AWS access key id, `ghp_` for a GitHub token,
`sk_live_` for a Stripe secret key -- or on a structural delimiter that cannot
occur by accident, such as a PEM private-key header or the `user:pass@` userinfo
of a URL. There is no entropy sweep over arbitrary strings and no rule keyed on
a variable being *called* something secret-sounding.

That is deliberate, and it is the position ci/gates/banned_patterns.py already
records for the same reason: a check that fires on every high-entropy token in a
tree is switched off within a week, and the rule then has NO enforcement rather
than partial. A missed secret of an unrecognised shape is a gap. A gate nobody
runs is a gap in every shape at once.

The errors therefore run one way: a credential whose issuer this gate does not
know about passes, and so does one pasted into a field this gate cannot
recognise. What must not happen -- and what the negative controls in
ci/broken-inputs/secret-scan/tree exist to hold -- is a finding on a published
example key, on a `${VARIABLE}` reference, on a commit SHA, or on a base64 blob.

## Two escapes, both visible

A matched value containing a placeholder token (`example`, `redacted`,
`changeme`, ...) is not reported: vendors publish example keys of exactly the
issued shape, and AWS's own documented example key id would otherwise fail every
repository that quotes it.

And a line carrying `not-a-live-credential:` suppresses its own finding, for the
revoked value a conformance fixture legitimately holds -- but only when the
reason after the marker NAMES THE DAY the value stopped being live, as a
calendar date that has already happened. Three markers therefore suppress
nothing and say why in the failure: a bare one, a reason of arbitrary prose with
no date in it, and a date in the future, which is a plan to revoke rather than a
revocation. Every other exclusion in this repository lives in one retrievable
declaration with a reason and an ending condition; this one is in-file and
self-service, so the date is what stops it outliving the fact that justified it.

Both escapes are counted on every run, passing runs included, and each honoured
suppression is printed with its path, line, shape and reason -- a count alone
tells a reader of a green run that something is silenced and not which file,
which is an exemption nobody can retrieve.

## What it does not decide

Whether a matched value is live, whether it was rotated after disclosure, and
who it belongs to -- rotation is an operator action and no check over a tree can
observe it. Whether a value of an unlisted shape is a credential. Whether a
secret sits in a file that is not valid UTF-8, which is not read here at all
(what a committed binary must declare is ci/gates/binary_assets.py's subject).
Whether a secret reached a commit OUTSIDE the range under review -- history
before the merge-base is not re-scanned on every run, and a scan of the whole
history is a separate, one-off piece of work with a different remedy.

Nor whether a URL userinfo password made only of letters is a disclosure:
`_url_password_leaks` requires a digit, which is a separate and stricter
condition than the entropy floor beside it, and drops
`postgres://u:SuperSecretPass@h/db`. It is declared in the coverage line for
that reason rather than described as entropy.

One escape this gate cannot offer is the file that IS a key. The marker is read
on the finding's line and the line above, so a key fixture can carry it only as
a line before the delimiter -- which a PEM reader tolerates (RFC 7468 allows
text before the encapsulation boundary, and `openssl pkey` reads such a file)
and an OpenSSH-format private key does not (`ssh-keygen -y` answers "invalid
format"). A tracked OpenSSH key fixture therefore needs a declared path scope in
ci/vault.json, on the precedent ci/gates/binary_assets.py sets, and this gate
does not invent that key for itself.

Nor does it decide anything about a configuration item a schema marks secret:
rebuild-plugboard task 3.15 asks for that too, and the single configuration
schema it would read is task 5.2's and does not exist yet. Keying on the schema
is the principled version of the name-anchored rule this gate deliberately does
not guess at, and it belongs in the change that creates the schema.

## The value is never printed

A failure names the location, the shape, and a fingerprint of the value -- never
the value. CI output is an artifact too, and a scanner that echoes what it found
into a public build log has moved the disclosure rather than reported it.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from _common import (
    Report,
    load_manifest,
    main_guard,
    repo_root,
    scan_excludes,
    subject_source,
    _in_worktree,
)

GATE_ID = "secret-scan"
RULE_NOTE = "docs/code/rules/no-credential-in-tree-or-history.md"

#: A line carrying this marker, a reason of at least MIN_REASON characters AND a
#: calendar date that has already happened suppresses a finding on that line or
#: the line below it. Held here rather than in ci/vault.json because a gate must
#: not invent a manifest key -- the same reason ci/gates/out_of_scope.py keeps
#: its spec-set constant in the module.
EXEMPTION_MARKER = "not-a-live-credential:"
MIN_REASON = 12

#: The date is the ending condition. Every other exclusion in this repository is
#: one declaration in ci/vault.json carrying a reason and the work that ends it;
#: this one is in-file and self-service, so what it must carry is the DAY the
#: value stopped being live. A reason of any twelve characters silenced a live
#: token; a reason naming a day that has not arrived is a promise.
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

#: Substrings that make a matched value a published example rather than a
#: credential. AWS documents `AKIAIOSFODNN7EXAMPLE`; a gate failing every
#: repository that quotes it is a gate that gets switched off.
PLACEHOLDER_TOKENS = (
    "example",
    "placeholder",
    "redacted",
    "changeme",
    "change-me",
    "dummy",
    "notreal",
    "sample",
    "yourkey",
    "your-key",
    "xxxxxx",
)

#: Bounds on the history half. The range under review is a branch, not a
#: repository: these exist so a mis-resolved base cannot put the whole history
#: inside `make check`, and when one binds the run says so rather than
#: truncating quietly.
MAX_COMMITS = 500
MAX_BLOBS = 4000
MAX_BYTES = 2_000_000

#: Resolved in order against the scan root; the first that exists wins. The
#: range is then merge-base(base, HEAD)..HEAD -- the commits under review, not
#: every commit the base has not seen.
BASE_REFS = ("origin/main", "main")

# Each pattern is anchored on an issuer-assigned prefix or a structural
# delimiter. `show` is whether the first four characters may be echoed in a
# failure: for a prefixed shape those four ARE the public issuer prefix, and for
# an unprefixed one nothing is echoed at all.
#
# Every literal below is written so the pattern cannot match this file: the
# delimiters are spelled `-{5}` rather than as five hyphens, and each prefix is
# followed here by a character class rather than by a value.
PATTERNS: list[tuple[str, str, bool]] = [
    ("aws-access-key-id",
     r"(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ABIA|ACCA)[A-Z0-9]{16}", True),
    ("github-token", r"gh[pousr]_[A-Za-z0-9]{36,}", True),
    ("github-fine-grained-token", r"github_pat_[A-Za-z0-9_]{60,}", True),
    ("slack-token", r"xox[abprse]-[A-Za-z0-9-]{12,}", True),
    ("stripe-secret-key", r"(?:sk|rk)_live_[A-Za-z0-9]{20,}", True),
    ("google-api-key", r"AIza[A-Za-z0-9_\-]{35}", True),
    ("anthropic-api-key", r"sk-ant-[A-Za-z0-9_\-]{24,}", True),
    ("openai-api-key", r"sk-proj-[A-Za-z0-9_\-]{20,}", True),
    ("npm-token", r"npm_[A-Za-z0-9]{36}", True),
    ("private-key-block", r"-{5}BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-{5}", False),
    ("signed-json-web-token",
     r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{20,}", False),
    # Unprefixed, so it is admitted only where the line also names the field AWS
    # itself names -- the co-occurrence rule ci/gates/banned_patterns.py uses to
    # make "a map over header fields" decidable. Without it this matches a
    # 40-character commit SHA.
    ("aws-secret-access-key",
     r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])", False),
    # A password in a URL's userinfo. Structural, not entropic: the shape is
    # `scheme://user:value@host`, and the conditions in `_url_password_leaks`
    # are what keep `${PGPASSWORD}` and `user:password@` out.
    ("url-embedded-password",
     r"[a-z][a-z0-9+.\-]{1,15}://[^\s/:@\"'`]{1,64}:"
     r"(?P<url_password>[^\s/:@\"'`]{10,64})@[^\s\"'`]{2,}", False),
]

COMBINED = re.compile(
    "|".join(f"(?P<{name.replace('-', '_')}>{pattern})" for name, pattern, _ in PATTERNS)
)
SHOW_PREFIX = {name: show for name, _p, show in PATTERNS}
AWS_SECRET_FIELD = "aws_secret_access_key"


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    total = len(value)
    return -sum(
        (n / total) * math.log2(n / total) for n in Counter(value).values()
    )


def _is_placeholder(value: str) -> bool:
    low = value.lower()
    return any(token in low for token in PLACEHOLDER_TOKENS)


def _url_password_leaks(password: str) -> bool:
    """Whether a URL userinfo password is a value rather than a reference.

    FIVE conditions, and the fifth is not an entropy rule. Four remove a shape
    that is common in a tracked file and is not a disclosure: a variable
    reference, a template placeholder, a word somebody wrote to mean "your
    password here", and a token below the entropy floor. The fifth requires a
    DIGIT, which is stricter than the floor and is the one that decides most
    misses: `SuperSecretPass` clears an entropy floor of 3.0 comfortably and is
    dropped here for having no digit in it.

    That is deliberate and it is a narrowing, not a subtlety of the entropy
    rule -- dropping it fires on `postgres://user:ReplaceThisValue@host`, and a
    scanner that fails on a runbook's fill-me-in line is a scanner that gets
    switched off. It is named in the coverage line as its own exclusion.
    """
    if not password or password[0] in "$<{%(":
        return False
    if _is_placeholder(password):
        return False
    if password.lower() in {
        "password", "pass", "secret", "token", "hunter2", "pw", "admin", "root"
    }:
        return False
    if not any(c.isdigit() for c in password):
        return False
    return _entropy(password) >= 3.0


def _dated(reason: str) -> tuple[str | None, str | None]:
    """(the day this reason names, the defect) -- exactly one of the two."""
    for year, month, day in ISO_DATE.findall(reason):
        try:
            named = date(int(year), int(month), int(day))
        except ValueError:
            continue  # 2026-13-40: a number of the shape, not a day
        if named > date.today():
            return None, (
                f"names {named.isoformat()}, which has not happened -- a "
                f"suppression is for a value already revoked, not one somebody "
                f"means to revoke"
            )
        return named.isoformat(), None
    return None, (
        "names no day the value stopped being live -- state one as YYYY-MM-DD, "
        "because a marker with no ending condition outlives the fact that "
        "justified it"
    )


def _exemption(lines: list[str], index: int) -> tuple[str, str]:
    """(verdict, detail) for the marker governing a finding on line `index`.

    Read on the finding's own line and the one above it. The verdict is
    `honoured` and the detail the stated reason; or `refused` and the detail why
    the marker did not take; or `absent` when no marker is there at all -- which
    the caller must keep distinct from a refusal, because a refused marker is
    somebody's failed attempt to silence this and the failure should say so.
    """
    candidates = [lines[index]]
    if index > 0:
        candidates.append(lines[index - 1])
    refusal = ""
    for line in candidates:
        at = line.find(EXEMPTION_MARKER)
        if at == -1:
            continue
        reason = line[at + len(EXEMPTION_MARKER):].strip()
        if len(reason) < MIN_REASON:
            refusal = refusal or (
                f"states no reason (under {MIN_REASON} characters after the "
                f"marker) -- an off switch with no stated reason is how a "
                f"suppression outlives the fact that justified it"
            )
            continue
        day, defect = _dated(reason)
        if day is None:
            refusal = refusal or f"{defect}"
            continue
        return "honoured", reason
    return ("refused", refusal) if refusal else ("absent", "")


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


class Finding:
    __slots__ = ("line", "kind", "value", "refusal")

    def __init__(self, line: int, kind: str, value: str, refusal: str = "") -> None:
        self.line, self.kind, self.value = line, kind, value
        #: Why a marker on this line did NOT suppress it, if one was tried.
        self.refusal = refusal

    @property
    def key(self) -> tuple[str, str]:
        return self.kind, _fingerprint(self.value)

    @property
    def article(self) -> str:
        # "u" is deliberately absent: every kind starting with it here is read
        # letter by letter ("a url-embedded-password"), which takes "a".
        return "an" if self.kind[0] in "aeio" else "a"

    def preview(self) -> str:
        head = f"{self.value[:4]}... " if SHOW_PREFIX.get(self.kind) else ""
        return f"{head}{len(self.value)} characters, fingerprint {_fingerprint(self.value)}"

    def marker_note(self) -> str:
        """Why a marker that was tried here did not take, if one was."""
        if not self.refusal:
            return ""
        return f". The `{EXEMPTION_MARKER}` marker on it {self.refusal}"


def _suppression_lines(subject: str, hushed: list[tuple[int, str, str, str]]) -> list[str]:
    """One printable line per honoured suppression, naming where it is."""
    return [
        f"    {subject}:{line} {kind}, fingerprint {digest}: {reason}"
        for line, kind, digest, reason in hushed
    ]


def scan_text(text: str) -> tuple[list[Finding], int, list[tuple[int, str, str, str]]]:
    """(findings, placeholders skipped, suppressions honoured) for one file.

    A suppression is returned as (line, shape, fingerprint, reason) rather than
    counted, so the run can name each one. The fingerprint is what lets a
    reviewer tell two suppressed values apart without either being printed.
    """
    lines = text.splitlines()
    findings: list[Finding] = []
    suppressed: list[tuple[int, str, str, str]] = []
    placeholders = 0
    for index, line in enumerate(lines):
        for match in COMBINED.finditer(line):
            kind = (match.lastgroup or "").replace("_", "-")
            if kind == "url-embedded-password":
                password = match.group("url_password")
                if not _url_password_leaks(password):
                    continue
                value = password
            else:
                value = match.group(0)
                if kind == "aws-secret-access-key" and AWS_SECRET_FIELD not in line.lower():
                    continue
                if _is_placeholder(value):
                    placeholders += 1
                    continue
            verdict, detail = _exemption(lines, index)
            if verdict == "honoured":
                suppressed.append((index + 1, kind, _fingerprint(value), detail))
                continue
            findings.append(
                Finding(index + 1, kind, value, detail if verdict == "refused" else "")
            )
    return findings, placeholders, suppressed


# ---------------------------------------------------------------------------
# The two subject sets
# ---------------------------------------------------------------------------
def _git(root: Path, *args: str) -> tuple[int, bytes]:
    """Read-only git in `root`. Never raises, never takes the index lock."""
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False, env=env
        )
    except FileNotFoundError:
        return 127, b""
    return done.returncode, done.stdout


def _tracked(root: Path) -> list[str] | None:
    if not _in_worktree(root):
        return None
    code, out = _git(root, "ls-files", "-z")
    if code != 0:
        return None
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def _walk(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )


def _excluded(rel: str, excludes: list[str]) -> bool:
    return any(rel == e or rel.startswith(e + "/") for e in excludes)


def resolve_range(root: Path, explicit: str | None) -> tuple[str | None, str]:
    """(range spec, label). A spec of None means the history half was not run."""
    if not _in_worktree(root):
        return None, "not a work tree"
    if explicit:
        code, _ = _git(root, "rev-parse", "--verify", "--quiet", explicit.split("..")[0])
        if code != 0:
            return None, f"{explicit} does not resolve"
        return explicit, f"{explicit} (given)"
    for base in BASE_REFS:
        code, _ = _git(root, "rev-parse", "--verify", "--quiet", base)
        if code != 0:
            continue
        code, out = _git(root, "merge-base", base, "HEAD")
        if code != 0:
            return f"{base}..HEAD", f"{base}..HEAD (no merge base)"
        merge_base = out.decode().strip()
        return f"{merge_base}..HEAD", f"{base}...HEAD via {merge_base[:12]}"
    return None, f"no base ref of {', '.join(BASE_REFS)} resolves"


def range_blobs(root: Path, spec: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """[(path, blob sha, commit sha)] introduced in `spec`, and any limits hit.

    Every commit in the range, merges included. `diff-tree -c` is what makes a
    merge readable: for a merge it lists the paths whose resulting version
    matches NO parent -- the conflict resolutions, which are the versions no
    other commit in the range carries -- and for a single-parent commit it is
    the ordinary diff. Without it `diff-tree` prints nothing at all for a merge,
    so `--no-merges` was not a narrowing anyone could see: it was a blob the
    coverage line claimed and the run never read.
    """
    limits: list[str] = []
    code, out = _git(root, "rev-list", f"--max-count={MAX_COMMITS + 1}", spec)
    if code != 0:
        return [], [f"{spec} could not be listed"]
    commits = out.decode().split()
    if len(commits) > MAX_COMMITS:
        limits.append(f"commits beyond the most recent {MAX_COMMITS} in {spec}")
        commits = commits[:MAX_COMMITS]
    # Keyed on (path, blob), never on blob alone: one blob reached by two paths
    # is two disclosures, and deduplicating on content would report one of them
    # and name the other's path nowhere.
    seen: set[tuple[str, str]] = set()
    blobs: list[tuple[str, str, str]] = []
    for commit in commits:
        code, out = _git(
            root, "diff-tree", "-r", "-z", "-c", "--no-commit-id", "--root", commit,
        )
        if code != 0:
            continue
        fields = out.decode("utf-8", "surrogateescape").split("\0")
        i = 0
        while i + 1 < len(fields):
            meta = fields[i]
            if not meta.startswith(":"):
                i += 1
                continue
            # `:<src mode> <dst mode> <src sha> <dst sha> <status>` for one
            # parent, and `::<mode>{n+1} <sha>{n} <dst sha> <status>` for n
            # parents. In both the resulting version is the second-to-last
            # field and the resulting mode is at index n, so one parse reads
            # both rather than two that can disagree about which sha is which.
            parts = meta.split()
            path = fields[i + 1]
            i += 2
            if len(parts) < 5 or len(parts) % 2 == 0:
                continue
            parents = (len(parts) - 3) // 2
            blob = parts[-2]
            # A deletion (all-zero result) has no version to read, and a gitlink
            # is a commit id rather than a blob -- ci/gates/no_submodules.py
            # owns that one.
            if parts[parents] == "160000" or blob.strip("0") == "":
                continue
            if (path, blob) in seen:
                continue
            seen.add((path, blob))
            blobs.append((path, blob, commit))
    if len(blobs) > MAX_BLOBS:
        limits.append(f"blobs beyond the first {MAX_BLOBS} in {spec}")
        blobs = blobs[:MAX_BLOBS]
    return blobs, limits


#: How many blobs are read per `git cat-file --batch` invocation. One process
#: for all of them held the whole range in memory; one process per blob cost two
#: seconds over a five-commit range of this repository, and suite latency is
#: treated here as a correctness control rather than a convenience.
BATCH = 256


def blob_texts(root: Path, shas: list[str]) -> dict[str, str | None]:
    """{sha: text or None} for every blob, in one `cat-file --batch` per chunk.

    None means read and refused: over MAX_BYTES, or not valid UTF-8. A sha the
    batch reports missing is absent from the mapping entirely, which the caller
    counts as unreadable rather than as clean.
    """
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    out: dict[str, str | None] = {}
    for start in range(0, len(shas), BATCH):
        chunk = shas[start:start + BATCH]
        try:
            done = subprocess.run(
                ["git", "-C", str(root), "cat-file", "--batch"],
                input=("\n".join(chunk) + "\n").encode(),
                capture_output=True, check=False, env=env,
            )
        except FileNotFoundError:
            return out
        data, pos = done.stdout, 0
        for _ in chunk:
            end = data.find(b"\n", pos)
            if end == -1:
                break
            header = data[pos:end].decode("utf-8", "replace").split()
            pos = end + 1
            if len(header) < 3 or header[1] != "blob":
                continue  # `<oid> missing`, or a non-blob: no body follows
            sha, size = header[0], int(header[2])
            body = data[pos:pos + size]
            pos += size + 1
            if size > MAX_BYTES:
                out[sha] = None
                continue
            try:
                out[sha] = body.decode("utf-8")
            except UnicodeDecodeError:
                out[sha] = None
    return out


# ---------------------------------------------------------------------------
EXPLICIT_RANGE: str | None = None


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    # ci/broken-inputs is a declared scan exclusion, and this gate's own
    # violating input is a planted credential: without honouring it here, the
    # gate fails the repository on the evidence that it works. It is honoured on
    # BOTH halves -- the fixture is committed, so the history half would find it
    # in the commit that added it.
    excludes = scan_excludes(manifest)
    report = Report(GATE_ID, RULE_NOTE)

    tracked = _tracked(scan_root)
    paths = tracked if tracked is not None else _walk(scan_root)
    paths = sorted(p for p in paths if not _excluded(p, excludes))

    placeholders = unreadable = 0
    suppressions: list[str] = []
    reported: set[tuple[str, str, str]] = set()

    for rel in paths:
        path = scan_root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            unreadable += 1
            continue
        report.examine(rel)
        found, skipped, hushed = scan_text(text)
        placeholders += skipped
        suppressions += _suppression_lines(rel, hushed)
        for finding in found:
            reported.add((rel, *finding.key))
            report.fail(
                f"{rel}:{finding.line}: {finding.article} {finding.kind} in a tracked "
                f"file ({finding.preview()}) -- a credential in the tree is disclosed to "
                f"everyone who can clone it, so remove it, rotate the value at its "
                f"issuer, and keep the live one somewhere the tree cannot reach"
                f"{finding.marker_note()}"
            )

    spec, label = resolve_range(scan_root, EXPLICIT_RANGE)
    limits: list[str] = []
    blobs: list[tuple[str, str, str]] = []
    if spec:
        blobs, limits = range_blobs(scan_root, spec)
        blobs = [b for b in blobs if not _excluded(b[0], excludes)]
        bodies = blob_texts(scan_root, [sha for _rel, sha, _c in blobs])
        for rel, blob, commit in blobs:
            text = bodies.get(blob)
            if text is None:
                unreadable += 1
                continue
            short = commit[:12]
            subject = f"{rel}@{short}"
            report.examine(subject)
            found, skipped, hushed = scan_text(text)
            placeholders += skipped
            suppressions += _suppression_lines(subject, hushed)
            for finding in found:
                if (rel, *finding.key) in reported:
                    # Already reported against the working tree: one credential,
                    # one failure. The tree-side message is the actionable one.
                    continue
                reported.add((rel, *finding.key))
                report.fail(
                    f"{subject}: {finding.article} {finding.kind} at line "
                    f"{finding.line} of the version commit {short} introduced "
                    f"({finding.preview()}) -- the tracked tree does not carry this "
                    f"value and every clone of this branch does, so deleting it in a "
                    f"later commit is not rotation: rotate it at its issuer"
                )

    # A half that did not run is reported as EXCLUDED, never as covered. The
    # same rule ci/gates/citations.py applies to a citation into an artifact
    # that is not present: absence makes it unverified, not satisfied, and the
    # one thing a run must not do is report it as checked.
    report.coverage(
        covered=[
            "every tracked UTF-8 file in the working tree",
            *([f"every blob added or modified in {label}"] if spec else []),
        ],
        excluded=[
            *excludes,
            *limits,
            *([] if spec else [f"the commit range under review -- {label}"]),
            "a file that is not valid UTF-8 (a committed binary is binary-assets')",
            "a credential shape no declared issuer prefix or delimiter anchors",
            "whether a matched value is live or was rotated (the operator's)",
            "a configuration item a schema marks secret (task 5.2 builds the schema)",
            "a url userinfo password holding no digit (the condition beside the "
            "entropy floor, and stricter than it)",
        ],
        kind="file version",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  working tree: {len(paths)} path(s) | range: {label} | blob versions: "
        f"{len(blobs)} | patterns: {len(PATTERNS)} | placeholders skipped: "
        f"{placeholders} | suppressed by marker: {len(suppressions)} | not UTF-8: "
        f"{unreadable}"
    )
    # Named, never merely counted: a count tells a reader of a green run that
    # something is silenced and not which file, and an exclusion nobody can
    # retrieve is an exemption.
    for line in suppressions:
        print(line)
    return report.finish(report_only=report_only)


# ---------------------------------------------------------------------------
# --self-test: the history half, which needs commits a fixture tree cannot hold.
# Exit 0 means this gate BEHAVED as the rule requires on a built scenario; exit
# 1 means it did not.
# ---------------------------------------------------------------------------
_PLANTED_AWS = "AKIA" + "3MJ7X2QF5RLDN4TW"
_PLANTED_GITHUB = "ghp_" + "0Vv7QeR2kLm9XbTn4CsD8JyH6WgZaP1uE3Ff"


def _git_build(root: Path, *args: str) -> int:
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
    }
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, env=env
    ).returncode


def _commit(root: Path, message: str) -> int:
    if _git_build(root, "add", "-A") != 0:
        return 1
    return _git_build(
        root, "-c", "user.name=gate", "-c", "user.email=gate@invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", message,
    )


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD")[1].decode().strip()


def _run_capture(root: Path, rng: str | None) -> tuple[int, str]:
    import contextlib
    import io

    global EXPLICIT_RANGE
    EXPLICIT_RANGE = rng
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = run(root, False)
    finally:
        EXPLICIT_RANGE = None
    return code, buffer.getvalue()


def _merge_case(root: Path) -> list[str]:
    """The merge half: a credential no parent of the merge carries.

    Two branches change one file, the resolution types a credential into it, and
    a later commit removes it again. The value is then in no single-parent
    commit's diff and in no tree: `rev-list --no-merges` put it in no subject set
    at all while the coverage line claimed every blob the range added.
    """
    problems: list[str] = []
    root.mkdir(parents=True)
    (root / "deploy.env").write_text("baseline\n", encoding="utf-8")
    if _git_build(root, "init", "-q", "-b", "scratch") != 0 or _commit(root, "baseline"):
        return ["could not build the merge scenario (see the dependency note above)"]
    baseline = _head(root)
    for branch, body in (("side", "SIDE=1\n"), ("scratch", "TRUNK=1\n")):
        if _git_build(root, "checkout", "-q", *(["-b"] if branch == "side" else []), branch):
            return [f"could not build the merge scenario: checkout {branch}"]
        (root / "deploy.env").write_text(body, encoding="utf-8")
        if _commit(root, f"{branch} edit"):
            return [f"could not build the merge scenario: commit on {branch}"]
    _git_build(root, "merge", "--no-commit", "--no-ff", "side")  # conflicts, by design
    (root / "deploy.env").write_text(
        f"AWS_ACCESS_KEY_ID={_PLANTED_AWS}\n", encoding="utf-8"
    )
    if _commit(root, "merge side"):
        return ["could not build the merge scenario: the merge commit"]
    merge = _head(root)
    (root / "deploy.env").write_text("clean\n", encoding="utf-8")
    if _commit(root, "remove it again"):
        return ["could not build the merge scenario: the removal"]

    parents = _git(root, "rev-list", "--parents", "-n", "1", merge)[1].decode().split()
    if len(parents) < 3:
        problems.append(
            "the scenario's merge commit has fewer than two parents, so this case "
            "is not testing a merge at all -- the git that built it resolved the "
            "branches some other way"
        )
    code, output = _run_capture(root, f"{baseline}..HEAD")
    if code != 1:
        problems.append(
            f"a credential written by a merge's own resolution did not fail (exit "
            f"{code}) -- it is in no parent's diff and in no tree, so a range walk "
            f"that skips merges reports green over it"
        )
    for label, needle in (
        ("the path and the merge commit", f"deploy.env@{merge[:12]}"),
        ("the shape", "aws-access-key-id"),
    ):
        if needle not in output:
            problems.append(f"the merge failure does not name {label} ({needle})")
    if _PLANTED_AWS in output:
        problems.append("the merge failure echoes the matched value")
    return problems


_HUSHED = "ghp_" + "1Rt4MzC7nQe2WbX9JdK5PvS8LfG3HyU6Ao0T"
_REFUSED = "ghp_" + "8Xc5PjV2mHd6TqN4RwB9LzF7KsE1GyU3Ma0Q"


def _marker_case(root: Path) -> list[str]:
    """The escape names the file it silenced, and a refusal still fails.

    This exists because the printing is the whole of what makes an in-file,
    self-service exclusion reviewable, and nothing else gates it: the fixture
    declaration reads the violation lines and the failure count, so the
    suppression list could be deleted tomorrow and every check stay green. A
    count alone tells a reader of a passing run that something is silenced and
    not which file, which is an exemption nobody can retrieve.
    """
    problems: list[str] = []
    (root / "fixtures").mkdir(parents=True)
    reason = "revoked at the issuer on 2020-05-06, kept for the refusal case"
    (root / "fixtures" / "hushed.token").write_text(
        f"# not-a-live-credential: {reason}\n{_HUSHED}\n", encoding="utf-8"
    )
    (root / "fixtures" / "refused.token").write_text(
        f"# not-a-live-credential: fine, we checked it ages ago, trust me\n"
        f"{_REFUSED}\n",
        encoding="utf-8",
    )
    code, output = _run_capture(root, None)
    if code != 1:
        problems.append(
            f"a marker naming no day did not fail (exit {code}) -- a reason of "
            f"arbitrary prose is the condition that let a live token be silenced "
            f"permanently"
        )
    failures = [l.strip() for l in output.splitlines() if l.strip().startswith("- ")]
    if not any("fixtures/refused.token:2" in l for l in failures):
        problems.append("the refused marker's finding does not name its path and line")
    if any("fixtures/hushed.token" in l for l in failures):
        problems.append("an honoured marker was reported as a violation anyway")
    for label, needle in (
        ("the suppressed path and line", "fixtures/hushed.token:2"),
        ("the stated reason", reason),
        ("the shape", "github-token"),
        ("the count", "suppressed by marker: 1"),
    ):
        if needle not in output:
            problems.append(
                f"an honoured suppression is not printed with {label} ({needle!r}) "
                f"-- an exclusion nobody can retrieve is an exemption"
            )
    if _HUSHED in output or _REFUSED in output:
        problems.append("the marker case echoes a matched value")
    return problems


def _self_test() -> int:
    import tempfile

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        (root / "deploy").mkdir(parents=True)
        (root / "deploy" / "notes.txt").write_text("baseline\n", encoding="utf-8")
        # A branch name no BASE_REFS entry matches, so the unresolved-range case
        # below is testing what it claims rather than an empty range.
        if _git_build(root, "init", "-q", "-b", "scratch") != 0 or _commit(root, "baseline"):
            print(
                f"[FAIL] {GATE_ID} --self-test: could not build the scenario. This "
                f"is the one gate whose runner must be able to CREATE A COMMIT: it "
                f"needs git on PATH, at least 2.28 for `init -b`, and a writable "
                f"temporary directory. Identity and signing are passed per command, "
                f"so no global git config is required and none is read."
            )
            return 1
        baseline = _head(root)

        leaked = root / "deploy" / "keys.env"
        leaked.write_text(f"AWS_ACCESS_KEY_ID={_PLANTED_AWS}\n", encoding="utf-8")
        if _commit(root, "add deployment keys"):
            print(f"[FAIL] {GATE_ID} --self-test: could not commit the planted value")
            return 1
        introduced = _head(root)[:12]

        leaked.unlink()
        if _commit(root, "remove deployment keys"):
            print(f"[FAIL] {GATE_ID} --self-test: could not commit the removal")
            return 1
        removed = _head(root)

        # (1) the range holding the introducing commit fails, naming path and commit.
        code, output = _run_capture(root, f"{baseline}..HEAD")
        if code != 1:
            problems.append(
                "a credential introduced and then deleted inside the range did not "
                f"fail (exit {code}) -- the history half is the whole reason this "
                "gate is not a tree scan"
            )
        for label, needle in (
            ("the path", "deploy/keys.env"),
            ("the introducing commit", introduced),
            ("the shape", "aws-access-key-id"),
        ):
            if needle not in output:
                problems.append(f"the failure does not name {label} ({needle})")
        if _PLANTED_AWS in output:
            problems.append(
                "the failure echoes the matched value -- a build log is an artifact "
                "too, so a finding names its location and a fingerprint, never the "
                "value"
            )

        # (2) a range that excludes the introducing commit passes, so the range
        # bounds the history half rather than decorating it.
        code, _ = _run_capture(root, f"{removed}..HEAD")
        if code != 0:
            problems.append(
                f"a range holding no planted value failed (exit {code}) -- the "
                "history half is then reporting commits outside the range under review"
            )

        # (3) with no range resolvable, the tree-only run passes over the same
        # repository. This records WHY the history half exists rather than
        # trusting a sentence about it.
        code, output = _run_capture(root, None)
        if code != 0:
            problems.append(
                f"the tree-only run failed (exit {code}) on a tree holding no "
                "credential"
            )
        if "no base ref" not in output:
            problems.append(
                "an unresolved range is not reported as unresolved -- a half that "
                "silently did not run reads exactly like a half that found nothing"
            )

        # (4) and the working-tree half fails on its own, in the same repository.
        (root / "deploy" / "token.txt").write_text(
            f"GITHUB_TOKEN={_PLANTED_GITHUB}\n", encoding="utf-8"
        )
        if _commit(root, "add a token to the tree"):
            problems.append("could not commit the working-tree case")
        code, output = _run_capture(root, None)
        if code != 1 or "deploy/token.txt:1" not in output:
            problems.append(
                f"a credential in a tracked file did not fail with its line "
                f"(exit {code})"
            )

        # (5) a value written by a MERGE's own resolution, in a second repository
        # so the tree half is silent and only the history half can fail it.
        problems += _merge_case(Path(tmp) / "merged")

        # (6) the marker: a refusal fails, an honoured suppression is NAMED.
        problems += _marker_case(Path(tmp) / "marked")

    if problems:
        print(f"[FAIL] {GATE_ID} --self-test: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        print(f"  rule: {RULE_NOTE}")
        return 1
    print(
        f"[ok] {GATE_ID} --self-test: a credential introduced and deleted inside "
        f"the range fails naming its path, line and introducing commit and never "
        f"echoing the value; the same repository passes for a range that excludes "
        f"that commit and for a tree-only run; a tracked credential fails on its "
        f"own; a credential written by a MERGE's own resolution -- in no "
        f"parent's diff and in no tree -- fails naming that merge; and the "
        f"in-file marker refuses a reason naming no day while printing every "
        f"honoured suppression with its path, line, shape and reason"
    )
    return 0


def _take_range(argv: list[str]) -> str | None:
    """Remove `--range SPEC` from argv, so main_guard sees only what it owns."""
    if "--range" not in argv:
        return None
    at = argv.index("--range")
    if at + 1 >= len(argv):
        raise SystemExit("--range requires a revision range, for example main..HEAD")
    spec = argv[at + 1]
    del argv[at:at + 2]
    return spec


if "--self-test" in sys.argv[1:]:
    sys.exit(_self_test())

EXPLICIT_RANGE = _take_range(sys.argv)
main_guard(run)
