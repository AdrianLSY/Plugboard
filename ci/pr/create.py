#!/usr/bin/env python3
"""Check a PR description against this branch, then push and open the PR."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import checks

ROOT = checks.ROOT


def command(*args: str) -> str:
    return subprocess.run(
        args, cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def current_branch() -> str:
    return command("git", "symbolic-ref", "--quiet", "--short", "HEAD")


def repository() -> tuple[str, str]:
    info = json.loads(
        command("gh", "repo", "view", "--json", "nameWithOwner,defaultBranchRef")
    )
    return info["nameWithOwner"], info["defaultBranchRef"]["name"]


def preflight(body: str, changed: list[str]) -> bool:
    mf = checks.manifest()
    for name in ("wire-contract-impact", "docs-touched"):
        verdict = checks.CHECKS[name](body, changed, mf)
        if verdict:
            print(f"[FAIL] {name}: {verdict}", file=sys.stderr)
            return False
        print(f"[ok] {name}")
    return True


def impact_answered(body: str) -> bool:
    verdict = checks.wire_contract_impact(body, [], checks.manifest())
    if verdict:
        print(f"[FAIL] wire-contract-impact: {verdict}", file=sys.stderr)
        return False
    return True


def publish(
    repo: str, base: str, branch: str, title: str, body_file: Path, draft: bool
) -> str:
    url = f"https://github.com/{repo}.git"
    command(
        "git",
        "-c",
        "credential.helper=!gh auth git-credential",
        "push",
        url,
        f"HEAD:refs/heads/{branch}",
    )
    args = [
        "gh",
        "pr",
        "create",
        "--repo",
        repo,
        "--base",
        base,
        "--head",
        branch,
        "--title",
        title,
        "--body-file",
        str(body_file),
    ]
    if draft:
        args.append("--draft")
    return command(*args)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True, type=Path)
    parser.add_argument(
        "--base", help="target branch (default: repository default branch)"
    )
    parser.add_argument("--draft", action="store_true")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate without pushing or opening a PR",
    )
    args = parser.parse_args(argv)

    try:
        body_file = args.body_file.resolve(strict=True)
        body = body_file.read_text(encoding="utf-8")
        # This check needs only the body. Reject it before any network request.
        if not impact_answered(body):
            return 1
        branch = current_branch()
        repo, default_base = repository()
        base = args.base or default_base
        if branch == base:
            print(
                f"[FAIL] cannot open a PR from its base branch ({base})",
                file=sys.stderr,
            )
            return 1
        url = f"https://github.com/{repo}.git"
        command(
            "git",
            "-c",
            "credential.helper=!gh auth git-credential",
            "fetch",
            "--no-tags",
            url,
            base,
        )
        changed = checks.changed_paths("FETCH_HEAD", "HEAD")
        if not preflight(body, changed):
            return 1
        if command("git", "status", "--porcelain"):
            print(
                "[FAIL] commit or remove uncommitted changes before opening a PR",
                file=sys.stderr,
            )
            return 1
        if args.check_only:
            print("[ok] PR preflight; no branch pushed and no PR created")
            return 0
        print(publish(repo, base, branch, args.title, body_file, args.draft))
        return 0
    except (
        OSError,
        UnicodeError,
        KeyError,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
        else:
            detail = str(exc)
        print(f"[FAIL] PR creation: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
