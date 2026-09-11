# Violating input: frontmatter

- **Gate:** `ci/gates/frontmatter.py`
- **Rule note:** `docs/method/rules/note-classification.md`
- **Requirement:** `docs/knowledge-base` — "Every note carries a classification"
  (tasks 1.6 and 1.7).

## Violations

The tree is a miniature vault: a spine (`docs/`), one per-component root
(`proxy/`), a planning directory (`openspec/`), and its own declared location
(`ci/vault.json`). One run must report all ten failures below, never stopping at
the first.

| # | Path | Violation | Expected failure |
|---|------|-----------|------------------|
| 1 | `tree/docs/no-frontmatter.md` | Opens with an H1, declares nothing — the shape of all eleven existing `docs/` files | `no frontmatter block`, naming all three required fields at once |
| 2 | `tree/docs/one-field-missing.md` | `authority` absent | `missing required field(s): authority` |
| 3 | `tree/proxy/two-fields-missing.md` | `status` **and** `authority` absent | **one** failure line naming *both*, not two lines |
| 4 | `tree/proxy/value-outside-enumeration.md` | `type: ruleset` | value refused, naming `'ruleset'` **and** the permitted set |
| 5 | `tree/docs/unread-field.md` | `tags:` — a field outside the declared set | refused as read by no gate and no index generator |
| 6 | `tree/docs/spine-normative.md` | `authority: normative` in the spine (task 1.7) | refused, naming the spine and the permitted authorities |
| 7 | `tree/docs/malformed.md` | A line that is not `key: value` | `malformed frontmatter`, naming line 3 |
| 7b | `tree/docs/malformed-unterminated.md` | Opening `---` never closed | `malformed frontmatter`, naming line 1 |
| 8 | `tree/ci/vault.json` → `banned-pattern-note` | Note class assigns no `authority` | names the class **and** the field with no value |
| 9 | `tree/ci/vault.json` → `generated-index` | Note class assigns `authority: generated`, outside the enumeration | same — a value the enumeration does not hold is not an assigned value |

## Must NOT fail

| Path | Why |
|------|-----|
| `tree/docs/valid-spine-note.md` | Every field declared, every value enumerated, no normative claim |
| `tree/proxy/valid-component-note.md` | Declares `authority: normative` **outside** the spine — the task 1.7 prohibition is scoped to the spine, and a gate that failed this would be enforcing a rule nobody wrote |
| `tree/openspec/changes/demo/tasks.md` | A planning artifact with **no frontmatter**. Out of this gate's scope, with the reason recorded in `ci/vault.json` (`classification.excluded_scopes`); the link and reachability gates still cover it. The run's coverage line must name `openspec` among the roots it excluded |
| `tree/ci/vault.json` → `orientation-essay` | A note class that assigns all three fields — present so a passing class and a failing class are discriminated, rather than the check firing on any populated table |

## Why the fixture carries its own `ci/vault.json`

Two of this gate's obligations — the closed enumerations and the note-class
completeness table — have their subject **in the manifest**, not in the tree. A
violating input for them can therefore only be a violating manifest, so the
fixture tree is a miniature repository with its own declared location, and
`resolve_manifest` reads the manifest belonging to the tree it is scanning.
Without this the completeness check would be unexercisable and would ship
untested — the failure `ci/gates/_common.py` was written to prevent.

The real `ci/vault.json` keeps `note_classes` empty until task 3.0. That is what
proves the other half of the check: on the real tree the run reports
`note classes checked=0` and raises no note-class failure, so the check passes
**vacuously** on an empty table and starts biting the moment a class appears.

## Proof

```
python3 ci/gates/frontmatter.py --root ci/broken-inputs/frontmatter/tree               # exit 1, 10 violations
python3 ci/gates/frontmatter.py --root ci/broken-inputs/frontmatter/tree --report-only # exit 0
python3 ci/gates/note_roots.py  --root ci/broken-inputs/frontmatter/tree               # exit 0 — fails only its own gate
```

On the real tree the gate reports 11 violations (the eleven `docs/*.md` files
with no frontmatter) and does not crash. It is report-only until task 3.11
applies the values task 3.0 assigns.
