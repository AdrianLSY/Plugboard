# Violating inputs: reachability

- **Gate:** `ci/gates/reachability.py`
- **Rule note:** `docs/method/rules/reachability.md`
- **Requirement:** docs/knowledge-base — "Every note is reachable from an entry point"

Two trees, because the requirement names two ways a file loses its last inbound
link and they read identically to a naive graph walk. Both must exit 1.

```bash
python3 ci/gates/reachability.py --root ci/broken-inputs/reachability/tree            # exit 1
python3 ci/gates/reachability.py --root ci/broken-inputs/reachability/tree-orphaned   # exit 1
# either tree, with --report-only                                                     # exit 0
```

## `tree/` — the newly added note, and the planning artifact's inbound link

- **Violation 1:** `docs/orphan.md` was **added** and no note links to it. The
  only mention of it anywhere in the tree is inside a fenced code block in
  `docs/architecture.md`, which is not a relation.
- **Violation 2:** `openspec/changes/demo/tasks.md` is reachable — but only
  through `openspec/changes/demo/proposal.md:3`, another planning artifact. The
  requirement says a planning artifact's inbound link must come from a note, so
  reachability of the normative surface is a property of the vault and not of
  the planning tool's internal cross-references.
- **Expected:** two failures in one run. The first names the note and states
  that no path exists from any entry point; the second names the offending
  inbound source and line, and the planning directories.

## `tree-orphaned/` — the note orphaned by a deletion

`docs/removed.md` used to link to `docs/stranded.md` and has been deleted. It is
absent from this tree, and nothing links to it, so no link is left dangling —
the damage is invisible to the link gate and visible only here.

- **Violation 1:** `docs/stranded.md` — its only inbound link went away with the
  deleted note. Reported the same way as a never-linked note, because it is the
  same computation; what distinguishes the two cases is the history, not the
  graph.
- **Violation 2:** `docs/downstream.md` — reported *differently*: it still has
  an inbound link, from `docs/stranded.md:12`, but that source is itself
  unreachable. This is what makes a deletion worse than an omission: one removed
  note strands a subtree, and the failure names the blocking source rather than
  claiming nothing links there.
- **Expected:** two failures in one run, the second naming `docs/stranded.md:12`
  as the unreachable source it hangs off.

## Cases these trees exercise

| Case | Where | Effect |
| --- | --- | --- |
| A newly added note nothing links to | `tree/docs/orphan.md` | fails |
| A note orphaned by a deletion | `tree-orphaned/docs/stranded.md` | fails |
| A note linked only from an unreachable note | `tree-orphaned/docs/downstream.md` | fails, naming the source |
| A planning artifact linked only by a planning artifact | `tree/openspec/changes/demo/tasks.md` | fails |
| Reachability stated as a path, not a yes/no | both trees' `paths:` block | 3-hop path printed |
| A declared entry point that does not exist yet | `AGENTS.md`, both trees | reported absent, **not** a violation |
| A link inside a fenced code block | `tree/docs/architecture.md` | not a relation — `orphan.md` stays unreachable |
| An external URL | `tree/docs/start-here.md` | not a vault relation |
| A fragment-only self link | `tree/docs/architecture.md` (`#overview`) | not a relation |
| A link carrying a fragment | `tree/docs/start-here.md` (`architecture.md#overview`) | resolves to the file |
| A non-markdown file under a planning directory | `tree/openspec/changes/demo/.openspec.yaml` | is a subject; reachable here, so it adds no violation |

## Why these trees fail only this gate

Every spine note and entry file carries frontmatter whose `type`, `status` and
`authority` come from the enumerations in `ci/vault.json`, and no spine note
declares normative authority; the planning artifacts deliberately carry none,
which is the scope the manifest records for them. Every link resolves, every
fragment names a heading that exists, and no link uses wiki or absolute form.
Every markdown file sits under a declared governed root — `python3
ci/gates/note_roots.py --root …` passes on both trees.
