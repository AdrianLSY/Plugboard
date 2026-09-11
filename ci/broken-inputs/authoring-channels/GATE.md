# Violating input: authoring-channels

- **Gate:** `ci/gates/authoring_channels.py` (`authoring_channels`)
- **Rule note:** `docs/method/rules/authoring-channels.md`
- **Requirement:** `docs/knowledge-base` — "Authoring guidance is applied at authoring time".

## Violations

1. `docs/method/conventions.md` lists only one convention, so the rest never reach a note author.
2. The planning tool delivers no guidance for this tree, so no convention reaches a planning-artifact
   author either.

## The case this gate exists for, and where it is exercised

The gate reads the conventions back **through the planning tool** rather than out of the config
file's bytes. That is the requirement's own wording — "the conventions are present in the context it
reads" — and it matters because the tool responds to an unparseable config by printing a warning and
**ignoring the whole file**. A check that grepped the file would pass on exactly that state, since
the ids are still in the bytes.

That failure happened for real while writing the config: a sequence item dedented out of its parent
made the file unparseable, and the tool silently fell back to no configuration at all.

It is verified against the **real tree** rather than here, because a fixture tree has no
`openspec/changes/`, so the tool produces no output and the delivery check cannot run. Reproduce it
by dedenting a guidance item in the real `openspec/config.yaml` and running the gate: it reports
"the planning tool delivers no context and no guidance" plus one line per undelivered convention.

## Expected

Exit 1, with every convention reported missing from at least one channel.
