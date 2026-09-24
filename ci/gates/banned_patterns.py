#!/usr/bin/env python3
"""Gate: five defect classes, each banned by name, each naming its own note.

Enforces rebuild-plugboard task 3.7. Five checks over tracked Elixir and Go
source; a failure names the rule it broke, because the contributor who trips a
check is reading at the one moment the defect is worth explaining.

  1. HEADERS AS A MAP        `map[string]string`, `Map.new`, `Enum.into(…, %{})`
                             over header fields. `Set-Cookie` is the canary: two
                             in one response is routine and a map keeps one.
  2. READ-ALL ON A BODY      `io.ReadAll` / `ioutil.ReadAll` in production Go.
  3. INSPECT ON A PAYLOAD    `inspect/1` outside a log line, in production Elixir.
  4. MONITOR WITHOUT TRAP    a GenServer that monitors and never traps exits.
  5. `with` WITH NO `else`   in a controller action.

## What each check actually decides, stated because none of them is the rule

None of these decides the rule as written. "A map OVER HEADER FIELDS" needs to
know what a value holds, and no text check knows that. So each is a narrower,
decidable thing, and the gap is named rather than left for a reader to assume:

  1. The construct on a line that also mentions a declared header token
     (ci/vault.json). A map built into a variable called `h` two lines earlier is
     invisible. False negatives, never false positives, by design -- a check that
     fired on every `map[string]string` in the tree would be turned off within a
     week, and then the rule has no enforcement at all rather than partial.
  2. Every ReadAll in non-test Go, with an explicit escape: a comment carrying
     the declared marker and a reason. Reading a config file at startup is
     legitimate and has to remain writable; what the rule refuses is doing it
     silently on a body in transit.
  3. `inspect(` on a line that is not a Logger call. `inspect/1` renders a term
     for a human; a human reads logs. Anywhere else it is a candidate for the
     wire, and the marker escape applies here too.
  4. Module-scoped: a module using GenServer that mentions a monitoring
     construct must call Process.flag(:trap_exit, true) somewhere in the file.
     Whether it is called in init/1 is not decided.
  5. Line-scoped over a *Controller module: a `with` opening a block whose
     matching `end` is not preceded by an `else` at the same indent. Elixir is
     not parsed; indentation is used, and a `with` written on one line is not
     seen.

## Why these five and not others

Each is a defect that shipped. The prior attempt typed headers as a single-valued
map on BOTH sides (`proxy_controller.ex:496`, `telephone.go:85`), so every
`Set-Cookie` past the first was deleted with no error and no log line. Its
"streaming" read the whole body into a `[]string` and then decided whether it was
chunked (`telephone.go:881`). Its refresh-token error path shipped
`inspect(reason)` over the channel (`telephone_channel.ex:106`). Its notifier
linked without trapping exits, so it died before its `:DOWN` clause could run and
the documented backoff was unreachable ceremony (`mount_notifier.ex:120`). The
fifth comes from the same finding table in docs/method/harness.md.

## What this gate is not

A substitute for the linters. golangci-lint and Credo cover the general cases;
these five are project-specific prohibitions no off-the-shelf rule expresses, and
they are checked here so they are checked at all rather than remembered.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from _common import (
    Report,
    _in_worktree,
    load_manifest,
    main_guard,
    repo_root,
    scan_excludes,
    subject_source,
)

GATE_ID = "banned-patterns"
RULE_NOTE = "docs/code/rules/banned-defect-classes.md"

GO_MAP = re.compile(r"map\[string\]string")
EX_MAP = re.compile(r"Map\.new\b|Enum\.into\(\s*[^)]*,\s*%\{\s*\}\s*\)")
READ_ALL = re.compile(r"\b(?:io|ioutil)\.ReadAll\s*\(")
INSPECT = re.compile(r"\binspect\s*\(")
LOGGER = re.compile(r"\bLogger\.\w+")
USES_GENSERVER = re.compile(r"^\s*use\s+GenServer\b", re.M)
MONITORS = re.compile(r"Process\.monitor\b|:DOWN\b|\bmonitor:\s*true")
TRAPS = re.compile(r"Process\.flag\(\s*:trap_exit\s*,\s*true\s*\)")
WITH_OPEN = re.compile(r"^(\s*)with\s+\S")
COMMENT_EX = re.compile(r"^\s*#")
COMMENT_GO = re.compile(r"^\s*//")


def _tracked(root: Path) -> list[str] | None:
    if not _in_worktree(root):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [p for p in out.decode("utf-8").split("\0") if p]


def _walk(root: Path) -> list[str]:
    out = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            out.append(path.relative_to(root).as_posix())
    return out


def run(scan_root: Path, report_only: bool) -> int:
    manifest = load_manifest(repo_root())
    cfg = manifest["code_standards"]["banned_patterns"]
    tokens = [t for t in cfg["header_tokens"] if not t.startswith("_")]
    marker = cfg["exemption_marker"]
    notes = cfg["notes"]
    report = Report(GATE_ID, RULE_NOTE)

    header_re = re.compile("|".join(re.escape(t) for t in tokens), re.I)
    excluded = scan_excludes(manifest)
    tracked = _tracked(scan_root)
    paths = tracked if tracked is not None else _walk(scan_root)
    sources = [
        p
        for p in paths
        if p.endswith((".go", ".ex", ".exs"))
        and not any(p == e or p.startswith(e + "/") for e in excluded)
    ]

    def fail(rel: str, line_no: int, note_key: str, message: str) -> None:
        report.fail(f"{rel}:{line_no}: {message} -- {notes[note_key]}")

    for rel in sources:
        path = scan_root / rel
        if not path.is_file():
            continue
        report.examine(rel)
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        is_go = rel.endswith(".go")
        is_test = rel.endswith("_test.go") or rel.endswith("_test.exs")
        exempt_lines = {n for n, l in enumerate(lines, 1) if marker in l} | {
            n + 1 for n, l in enumerate(lines, 1) if marker in l
        }

        for n, line in enumerate(lines, 1):
            if (COMMENT_GO if is_go else COMMENT_EX).match(line):
                continue

            # (1) a one-value-per-name container over header fields.
            construct = GO_MAP.search(line) if is_go else EX_MAP.search(line)
            if construct and header_re.search(line):
                fail(
                    rel,
                    n,
                    "headers-as-a-map",
                    f"`{construct.group(0)}` on a line naming a header field -- a "
                    f"repeated field name is ordinary and the order is part of the "
                    f"message, so `Set-Cookie` past the first is deleted silently",
                )

            # (2) a body accumulated before it is emitted.
            read_all = READ_ALL.search(line)
            if is_go and not is_test and read_all and n not in exempt_lines:
                fail(
                    rel,
                    n,
                    "read-all-on-a-proxied-body",
                    f"`{read_all.group(0)}` with no `{marker}` comment "
                    f"stating why this is not a body in transit -- a hop reads a "
                    f"chunk and writes a chunk",
                )

            # (3) a term rendering that can reach a peer.
            if (
                (not is_go)
                and not is_test
                and INSPECT.search(line)
                and not LOGGER.search(line)
                and n not in exempt_lines
            ):
                fail(
                    rel,
                    n,
                    "inspect-on-a-wire-payload",
                    f"`inspect/1` outside a log line and with no `{marker}` comment "
                    f"-- a peer receives an enumerated code, not an Elixir term "
                    f"rendering that changes shape when the internal term does",
                )

        # (4) a GenServer that monitors and never traps exits. Module-scoped.
        genserver = USES_GENSERVER.search(text)
        if not is_go and genserver and MONITORS.search(text) and not TRAPS.search(text):
            fail(
                rel,
                text[: genserver.start()].count("\n") + 1,
                "monitor-without-trap-exit",
                "a GenServer that monitors and never calls "
                "`Process.flag(:trap_exit, true)` -- it dies before its `:DOWN` "
                "clause can run, which makes every recovery path below it "
                "unreachable ceremony",
            )

        # (5) `with` in a controller action, with no `else`.
        if not is_go and re.search(r"^\s*defmodule\s+\S*Controller\b", text, re.M):
            for n, line in enumerate(lines, 1):
                m = WITH_OPEN.match(line)
                if not m or COMMENT_EX.match(line):
                    continue
                indent = m.group(1)
                has_else = False
                for follow in lines[n:]:
                    if (
                        follow.strip()
                        and not follow.startswith(indent + " ")
                        and not follow.startswith(indent + "\t")
                    ):
                        if (
                            follow == indent + "else"
                            or follow.rstrip() == indent + "else"
                        ):
                            has_else = True
                        break
                if not has_else:
                    fail(
                        rel,
                        n,
                        "with-without-else",
                        "`with` in a controller action and no `else` clause -- every "
                        "non-matching clause then falls through as its own raw value",
                    )

    report.coverage(
        covered=sorted({p.rsplit(".", 1)[-1] for p in sources})
        or ["(no Elixir or Go source)"],
        excluded=[*excluded, "the general cases, which golangci-lint and Credo own"],
        kind="source file",
        source=subject_source(scan_root),
        scan_root=scan_root,
    )
    print(
        f"  source files: {len(sources)} | checks: 5 | header tokens: "
        f"{len(tokens)} | exemption marker: {marker}"
    )
    return report.finish(report_only=report_only)


main_guard(run)
