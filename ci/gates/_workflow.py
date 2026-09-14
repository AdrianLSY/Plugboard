"""Shared reading of a workflow file. Standard library only.

Three gates need the same two questions answered about a workflow -- which events
it triggers on, and what it actually EXECUTES -- and they were on their way to
three copies: ci/gates/runner.py grew `triggers` first, ci/gates/security_scan.py
grew its own beside it, and ci/gates/parity.py would have been the third.

That is the defect this repository keeps finding in itself. Three instances landed
in one day (the pull-request template against the note stating it, "which modules
are not gates" in six hardcoded copies, the test tiers' invocations in YAML and in
make), and the lesson recorded each time was the same: where one of the two copies
can be deleted, delete it. Here it can, so it is.

Parsed by regex rather than by a YAML library because ci/gates is standard library
only: a gate with a dependency can stop running without failing.
"""

from __future__ import annotations

import re

_KEY = re.compile(r"^(\s*)(?:-\s+)?(run|uses|with)\s*:\s*(.*)$")
_BLOCK_SCALAR = {"|", ">", "", "|-", ">-", "|+", ">+"}


def triggers(body: str) -> set[str]:
    """Every event name under `on:`, in all three spellings GitHub accepts.

    A mapping (`on:` then indented keys), a bare scalar (`on: pull_request_target`),
    and an inline sequence (`on: [push, pull_request]`). ci/gates/runner.py
    recognised only the first and reported a workflow that DID carry its declared
    trigger as missing it -- a gate refusing a correct spelling is one that gets
    argued with and then switched off.
    """
    m = re.search(r"^on:\s*$(.*?)(?=^\S)", body, re.M | re.S)
    if m:
        return set(re.findall(r"^\s+([a-z_]+)\s*:", m.group(1), re.M))
    m = re.search(r"^on:\s*(.+?)\s*$", body, re.M)
    if not m:
        return set()
    rest = m.group(1).strip()
    if rest.startswith("["):
        return {t.strip().strip("'\"") for t in rest.strip("[]").split(",") if t.strip()}
    return {rest}


def executable_text(body: str) -> str:
    """Only what a runner executes: `run:` bodies, `uses:` references, `with:` values.

    A step's `name:` is prose, and a comment is not even that. Reading either is how
    an earlier ci/gates/security_scan.py came to report "scanners invoked: 4 of 4"
    against a workflow whose every step was `echo skipping` with the scanner named
    in `name:`. Returning the executable text alone makes that shape unmatchable
    rather than merely discouraged.
    """
    out: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        m = _KEY.match(lines[i])
        if not m:
            i += 1
            continue
        indent, key, rest = len(m.group(1)), m.group(2), m.group(3)
        out.append(rest)
        if key in ("run", "with") and rest.strip() in _BLOCK_SCALAR:
            i += 1
            while i < len(lines) and (
                not lines[i].strip()
                or len(lines[i]) - len(lines[i].lstrip()) > indent
            ):
                out.append(lines[i])
                i += 1
            continue
        i += 1
    return "\n".join(out)


def executes(body: str, command: str) -> bool:
    """Whether the workflow runs `command`, in a position a shell would run it.

    Reading `run:` bodies is NOT sufficient, and the gap was found by feeding a
    gate its own counter-example: `run: echo "make check-gates"` IS a run body and
    it DOES contain the command, so a containment test passes while nothing runs.
    That is the same defect one layer in from the one that had a scanner satisfied
    by its step's `name:`.

    So a command must appear at a COMMAND POSITION: the start of a line, or after
    `&&`, `||`, `;` or a pipe. `cd proxy && mix sobelow --exit` runs sobelow;
    `echo "mix sobelow --exit"` does not, and the difference is exactly where the
    string sits relative to those separators.

    What this still cannot decide: a command reached through a variable, a script
    file, or an alias. `run: $SCANNER` runs something this cannot name. Stated
    because the check is a floor, not a proof.
    """
    for line in executable_text(body).splitlines():
        for segment in re.split(r"&&|\|\||;|\|", line):
            if segment.strip().startswith(command):
                return True
    return False
