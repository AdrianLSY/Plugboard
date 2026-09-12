# Violating input: authoring-channels

- **Gate:** `ci/gates/authoring_channels.py` (`authoring_channels`)
- **Rule note:** `docs/method/rules/authoring-channels.md`
- **Requirement:** `docs/knowledge-base` — "Authoring guidance is applied at authoring time".

## Violations

### `tree/` — a convention reaches neither channel

1. `docs/method/conventions.md` lists only one convention, so the rest never reach a note author.
2. The planning tool delivers no guidance for this tree, so no convention reaches a planning-artifact
   author either.

### `tree-divergent/` — the two channels state different conventions

3. `openspec/config.yaml` delivers `relative-links` with a statement that is not the one
   `ci/vault.json` holds, while `docs/method/conventions.md` carries the source statement. Both
   channels name the id, so presence is not the property at stake: agreement is. The failure names
   the convention and both channels, because the author needs to know which one lied.

Both channels carry all fifteen ids in that tree, so absence is not what it demonstrates. It holds
`openspec/changes/divergence-probe/` because the gate reads the planning-artifact channel back
through the tool, and the tool delivers nothing for a tree with no change to read a configuration
for. Its fifteen `names gate ... which the repository does not run` failures are the same
unavoidable consequence of a fixture tree holding no `ci/gates/` that `tree/` emits.

## The case this gate exists for, and where it is exercised

The gate reads the conventions back **through the planning tool** rather than out of the config
file's bytes. That is the requirement's own wording — "the conventions are present in the context it
reads" — and it matters because the tool responds to an unparseable config by printing a warning and
**ignoring the whole file**. A check that grepped the file would pass on exactly that state, since
the ids are still in the bytes.

That failure happened for real while writing the config: a sequence item dedented out of its parent
made the file unparseable, and the tool silently fell back to no configuration at all.

`tree/` demonstrates the unparseable-config state itself, because it has no `openspec/changes/`:
the tool produces no output, which is byte-for-byte what an ignored file produces. Reproduce the
original defect in the real tree by dedenting a guidance item in `openspec/config.yaml` and running
the gate: it reports "the planning tool delivers no context and no guidance" plus one line per
undelivered convention.

`tree-divergent/` takes the other branch on purpose. Adding a change directory makes the tool
deliver that tree's own configuration, which is what lets a fixture exercise the comparison rather
than only the absence.

## Expected

Exit 1 on both trees: `tree/` with every convention reported missing from at least one channel, and
`tree-divergent/` with one convention reported as stated differently by the two. `expect.json`
carries the counts and the cases; the prose above is not the declaration.
