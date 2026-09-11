# Violating input: duplication

- **Gate:** `ci/gates/duplication.py`
- **Rule note:** `docs/method/rules/one-copy-of-requirement-text.md`
- **Requirement:** `docs/knowledge-base` — "The repository is one vault with one spine", scenario
  "Content is not duplicated between the spine and the specifications".
- **Violation:** three requirement paragraphs owned by
  `tree/openspec/changes/add-widget-mount/specs/widget-mount/spec.md` are also carried by notes in the
  spine, one per form the gate must see through.
- **Expected:** **three** failures in one run, exit 1; each names *both* locations as `path:line` and
  quotes the normalised block. `--report-only` prints the same three and exits 0.

## What each file in the tree is for

Every case below is exercised by the fixture in one run; the three violations and the four
non-violations are what distinguish this gate from a substring search.

### Violations — must fail, and must name both ends

| Case | Spine location | Owner | Form the gate must see through |
| --- | --- | --- | --- |
| **A** | `tree/docs/concepts/widget-mount.md:13` | spec `:10` | Verbatim copy, re-wrapped at different line breaks. |
| **B** | `tree/docs/concepts/refusal-shape.md:13` | spec `:15` | Same text with `**bold**` and `*italic*` added, opening words upper-cased, run-in whitespace, and the inline link pointed at a different relative path (the note sits at a different depth from the spec). |
| **C** | `tree/docs/method/quoting.md:15` | spec `:20` | Verbatim copy indented into a `>` blockquote — quote markers do not make a copy into a citation. |

### Non-violations — must stay silent, and each states why

| Case | Location | Why it does not fire |
| --- | --- | --- |
| **D** | `tree/docs/concepts/widget-mount.md` / spec | A sentence shared by both ("The gate fails and names both locations.") that is below the floor: 7 words, 40 characters against a floor of 18 words and 120 characters. Boilerplate a specification and a note about it inevitably share is not a copy, and a gate that fired on it would be switched off rather than obeyed. |
| **E** | `tree/docs/rules/refuse-never-degrade.md` | A genuine paraphrase of the specification's first requirement, marked non-normative and linked to its owner. **This is the case the gate cannot decide.** It is in the fixture so the boundary is visible rather than assumed: currency of a restatement is owned by the "Authority precedence is stated and enforced" requirement and by review, not here. |
| **F** | `tree/docs/method/quoting.md` / spec | A fenced `bash` block byte-identical in both files, and long enough to clear both floors if it were counted (its four command lines normalise to 18 words and 315 characters; 30 words and 385 characters with the comment line). Fenced code is not requirement text; duplicated code is owned by the code-standards duplication threshold (task 6.11). |
| **G** | `tree/docs/method/authoring.md` + `tree/docs/rules/refuse-never-degrade.md` | One long paragraph repeated between two spine notes, crossing no boundary. The requirement is about the spine-versus-specification boundary, so this pair is out of scope. |

`tree/docs/start-here.md` is the declared entry point, so every note in the tree is reachable and
every relative link in the fixture resolves.

## The fixture fails only this gate

`python3 ci/gates/note_roots.py --root ci/broken-inputs/duplication/tree` exits 0: all seven files sit
under the governed roots `docs` and `openspec`, none is an undeclared root-level note. Every spine note
carries `type`/`status`/`authority` from the declared enumerations with non-normative authority, links
are relative markdown with resolving targets and no wiki-link or transclusion syntax, and the
specification file is under a declared planning directory, where frontmatter is not required.

## Proof

```bash
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree               # 3 failures, exit 1
python3 ci/gates/duplication.py --root ci/broken-inputs/duplication/tree --report-only # same 3, exit 0
python3 ci/gates/duplication.py                                                        # real tree, exit 0
```

The real tree currently reports **0 violations** over 11 spine notes and 16 specification files. That is
a real result, not an inert gate: pasting a genuine paragraph from
`openspec/changes/rebuild-plugboard/specs/auth/sidecar-credentials/spec.md:3` into `docs/README.md` in a
throwaway copy of the tree produced exactly one failure naming both locations.
