"""The preflight must refuse bad descriptions before any PR is opened."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import create


VALID_BODY = """## What breaks if this is wrong?
The PR guard might let an incomplete description through.

## Wire contract impact
- [x] None
- [ ] Additive
- [ ] **BREAKING**

## Tests
The missing-heading regression fails before any network command.

## Checklist
docs: n/a — This change only affects pull-request tooling.
"""


class CreateTests(unittest.TestCase):
    def run_with_body(self, body: str, *extra: str) -> int:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "body.md"
            path.write_text(body, encoding="utf-8")
            return create.main(["--title", "Guard PRs", "--body-file", str(path), *extra])

    def test_missing_impact_stops_before_any_command(self):
        with patch.object(create, "command") as command:
            result = self.run_with_body("## What breaks if this is wrong?\nThe check is bypassed.\n")
        self.assertEqual(result, 1)
        command.assert_not_called()

    def test_docs_check_stops_before_push_or_pr_create(self):
        outputs = ["tooling/pr-guard", '{"nameWithOwner":"owner/repo","defaultBranchRef":{"name":"main"}}', ""]
        with patch.object(create, "command", side_effect=outputs) as command, \
             patch.object(create.checks, "changed_paths", return_value=["contract/wire.proto"]):
            result = self.run_with_body(VALID_BODY.replace("docs: n/a — This change only affects pull-request tooling.", ""))
        self.assertEqual(result, 1)
        self.assertEqual(command.call_count, 3)  # branch, repository, fetch; never push/create

    def test_valid_description_pushes_then_creates_pr(self):
        outputs = ["tooling/pr-guard", '{"nameWithOwner":"owner/repo","defaultBranchRef":{"name":"main"}}', "", "", "", "https://github.com/owner/repo/pull/11"]
        with patch.object(create, "command", side_effect=outputs) as command, \
             patch.object(create.checks, "changed_paths", return_value=["ci/pr/create.py"]):
            self.assertEqual(self.run_with_body(VALID_BODY), 0)
        calls = [call.args for call in command.call_args_list]
        self.assertEqual(calls[4][:5], ("git", "-c", "credential.helper=!gh auth git-credential", "push", "https://github.com/owner/repo.git"))
        self.assertEqual(calls[5][:3], ("gh", "pr", "create"))
        self.assertIn("--body-file", calls[5])

    def test_check_only_does_not_publish(self):
        outputs = ["tooling/pr-guard", '{"nameWithOwner":"owner/repo","defaultBranchRef":{"name":"main"}}', "", ""]
        with patch.object(create, "command", side_effect=outputs) as command, \
             patch.object(create.checks, "changed_paths", return_value=["ci/pr/create.py"]):
            self.assertEqual(self.run_with_body(VALID_BODY, "--check-only"), 0)
        self.assertEqual(command.call_count, 4)  # branch, repository, fetch, status


if __name__ == "__main__":
    unittest.main()
