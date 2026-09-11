# Violating input: links

- **Gate:** `ci/gates/links.py`
- **Rule note:** `docs/method/rules/link-resolution.md`
- **Requirement:** docs/knowledge-base -- "Every link resolves".

## Violation

`tree/docs/notes.md` carries exactly two unresolved links, one per cause:

| Line | Link | Cause |
| --- | --- | --- |
| 14 | `[ghost file](ghost.md)` | `missing-file` -- no such path in the tree |
| 15 | `[ghost anchor](target.md#no-such-heading)` | `missing-anchor` -- `tree/docs/target.md` exists; the heading does not |

## Expected

`python3 ci/gates/links.py --root ci/broken-inputs/links/tree` exits **1** with
**two** violations reported in the one run, each naming the source note and its
line, and each labelled with its cause so a missing anchor is never mistaken for
a missing file. The accounting line shows `missing-file=1 missing-anchor=1`.
With `--report-only` the same two are printed as warnings and the exit code is 0.

## Controls the fixture also asserts

Every other link in `tree/docs/notes.md` must resolve, or the fixture would stop
isolating the two causes above: a plain relative link, a fragment that the target
does provide, a bare `#fragment` against the note's own heading, an external
`https:` scheme, a `file.ex:3` line-numbered citation (file resolved, line
ignored), a `#L3` line fragment on a non-markdown file, a reference definition
(`[id]: target`), an inline code span containing link syntax, and a fenced block
containing link syntax -- the last two render literally and are not relations.

The tree is otherwise clean: `tree/docs/` is the declared spine so no path is
undeclared, every note carries valid `type`/`status`/`authority` frontmatter with
no spine note claiming normative authority, no wiki-style or transclusion syntax
appears, and `tree/docs/start-here.md` is the declared entry point linking to
both other notes. This fixture fails the link gate and no other.
