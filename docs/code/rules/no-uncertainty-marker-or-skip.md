---
type: rule
status: current
authority: rationale
---

# No uncertainty marker, and no unconditional skip, stands in for a failing assertion

<a id="no-uncertainty-marker-or-skip"></a>

**Gate:** `ci/gates/test_hygiene.py` — an uncertainty marker in a test body, a skip with no linked
issue, and `async: false` with no stated reason. The marker phrases are declared in `ci/vault.json`:
a check for "uncertainty" over English fires on every honest comment.

Prohibited in a test: abandoned reasoning committed as comments — "actually this shouldn't be…",
"let me think again", "for now we just…" — and a skip that carries no linked issue. A skip claiming
that coverage exists elsewhere names the case that provides it.

## Why

`hooks_test.exs:425` carries the model's abandoned reasoning verbatim as committed comments, and
`executor_test.exs:465` skips the only mount-point hook success test behind a claim that
`proxy_controller` integration tests cover it — a claim the audit records as false
([the audit](../../history/reference-audit.md)). So the suite reported a feature as covered by a
file that did not cover it, which is a worse position than an empty test file.

An uncertainty marker is a failing assertion someone hid, and it is the clearest signature of
model-written test code, which the review pass expects a fraction of contributions to be
([reviewing](../reviewing.md#ai-generated-pr-review)). Both shapes read as work-in-progress at the
moment of writing and as coverage forever afterwards.

## Related

- [A test asserts the intended behaviour](no-test-accommodating-a-defect.md) — the same file,
  `hooks_test.exs:425`, is cited by both: the comment and the dodged case arrived together.
